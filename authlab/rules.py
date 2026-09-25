"""Regras de detecção AUTH-001 e AUTH-003.

Especificação completa (limites de janela, empates, eventos fora de ordem,
prevenção de alertas repetidos): docs/regras.md.

Resumo:
- Chave de correlação: (domain, user, src_ip, host), com comparação sem
  diferenciar maiúsculas/minúsculas em domain/user/host e IP canônico.
- Eventos sem algum campo da chave (inclusive src_ip ausente) NÃO são
  elegíveis e são contados no resumo (nunca agrupados como "desconhecido").
- AUTH-001: >= threshold falhas 4625 com a mesma chave em que
  (último - primeiro) <= window (limite inclusivo). Um alerta por episódio;
  o episódio continua enquanto a próxima falha ocorrer em até `window` após
  a anterior. Cada falha pertence a no máximo um alerta.
- AUTH-003: primeiro 4624 com a mesma chave, estritamente posterior à falha
  que completou o limiar e em até `success_within` após a última falha que o
  antecede (limite inclusivo). No máximo um AUTH-003 por AUTH-001 e cada
  sucesso é usado por no máximo um AUTH-003.
"""

from __future__ import annotations

import hashlib
from collections import Counter, deque
from dataclasses import dataclass, field
from datetime import datetime

from .config import Config
from .events import Event

RULE_NAMES = {
    "AUTH-001": "Falhas repetidas de autenticação",
    "AUTH-003": "Sucesso após falhas repetidas",
}


@dataclass(frozen=True)
class CorrelationKey:
    domain: str
    user: str
    src_ip: str
    host: str

    def label(self) -> str:
        return f"{self.domain}\\{self.user} | origem {self.src_ip} | destino {self.host}"


@dataclass
class Alert:
    alert_id: str
    rule_id: str
    key: CorrelationKey
    trigger_event: Event
    evidence: list[tuple[Event, str]]  # (evento, papel: "failure" | "success")
    parent_alert_id: str | None = None
    threshold: int = 0
    window_minutes: int = 0
    interval_minutes: int = 0

    @property
    def rule_name(self) -> str:
        return RULE_NAMES[self.rule_id]

    @property
    def failures(self) -> list[Event]:
        return [e for e, role in self.evidence if role == "failure"]

    @property
    def success(self) -> Event | None:
        for e, role in self.evidence:
            if role == "success":
                return e
        return None

    @property
    def first_seen(self) -> datetime:
        return self.evidence[0][0].timestamp_utc

    @property
    def last_seen(self) -> datetime:
        return self.evidence[-1][0].timestamp_utc


@dataclass
class RuleStats:
    rule_id: str
    enabled: bool
    candidates: int = 0
    eligible: int = 0
    ineligible_reasons: Counter = field(default_factory=Counter)
    alerts: int = 0

    @property
    def ineligible(self) -> int:
        return self.candidates - self.eligible

    def status_message(self) -> str:
        if not self.enabled:
            return "Regra desabilitada na configuração."
        if self.candidates == 0:
            return ("Dados insuficientes: não há eventos do tipo avaliado por esta regra. "
                    "Ausência de alerta aqui NÃO indica ausência de atividade.")
        if self.eligible == 0:
            return ("Dados insuficientes: nenhum evento tem todos os campos de correlação. "
                    "Ausência de alerta aqui NÃO indica ausência de atividade.")
        base = (f"{self.alerts} alerta(s). Avaliados {self.eligible} de "
                f"{self.candidates} eventos candidatos.")
        if self.ineligible:
            base += (f" Atenção: {self.ineligible} evento(s) não puderam ser avaliados "
                     "por falta de campos; a cobertura é parcial.")
        elif self.alerts == 0:
            base += " Nenhum padrão atingiu os critérios com os dados disponíveis."
        return base


def ineligibility_reasons(e: Event) -> list[str]:
    reasons = []
    if not e.domain:
        reasons.append("domain ausente")
    if not e.user:
        reasons.append("user ausente")
    if e.src_ip_state != "valid":
        reasons.append("src_ip ausente")
    return reasons


def correlation_key(e: Event) -> tuple:
    return (e.domain.casefold(), e.user.casefold(), e.src_ip, e.host.casefold())


def _alert_id(rule_id: str, *parts) -> str:
    text = "|".join(str(p) for p in parts)
    return f"{rule_id}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]}"


def _group(events: list[Event], event_id: int, stats: RuleStats) -> dict[tuple, list[Event]]:
    groups: dict[tuple, list[Event]] = {}
    for e in events:
        if e.event_id != event_id:
            continue
        stats.candidates += 1
        reasons = ineligibility_reasons(e)
        if reasons:
            stats.ineligible_reasons.update(reasons)
            continue
        stats.eligible += 1
        groups.setdefault(correlation_key(e), []).append(e)
    for items in groups.values():
        items.sort(key=Event.sort_key)  # garante ordem mesmo com entrada fora de ordem
    return groups


def _display_key(e: Event) -> CorrelationKey:
    return CorrelationKey(domain=e.domain, user=e.user, src_ip=e.src_ip, host=e.host)


def detect_auth001(events: list[Event], cfg: Config) -> tuple[list[Alert], RuleStats]:
    rc = cfg.auth001
    stats = RuleStats("AUTH-001", rc.enabled)
    if not rc.enabled:
        return [], stats
    alerts: list[Alert] = []
    for _, failures in sorted(_group(events, 4625, stats).items()):
        window: deque[Event] = deque()
        active: Alert | None = None
        for e in failures:
            if active is not None:
                last = active.evidence[-1][0]
                if e.timestamp_utc - last.timestamp_utc <= rc.window:
                    active.evidence.append((e, "failure"))
                    continue
                active = None  # episódio encerrado; recomeça a contagem do zero
                window.clear()
            window.append(e)
            while e.timestamp_utc - window[0].timestamp_utc > rc.window:
                window.popleft()
            if len(window) >= rc.threshold:
                first = window[0]
                active = Alert(
                    alert_id=_alert_id("AUTH-001", *correlation_key(e), first.event_uid),
                    rule_id="AUTH-001",
                    key=_display_key(first),
                    trigger_event=e,
                    evidence=[(x, "failure") for x in window],
                    threshold=rc.threshold,
                    window_minutes=rc.window_minutes,
                )
                alerts.append(active)
                window.clear()
    stats.alerts = len(alerts)
    alerts.sort(key=lambda a: (a.trigger_event.sort_key(), a.alert_id))
    return alerts, stats


def detect_auth003(events: list[Event], auth001_alerts: list[Alert], cfg: Config
                   ) -> tuple[list[Alert], RuleStats]:
    rc = cfg.auth003
    stats = RuleStats("AUTH-003", rc.enabled)
    if not rc.enabled:
        return [], stats
    successes = _group(events, 4624, stats)
    alerts: list[Alert] = []
    parents_by_key: dict[tuple, list[Alert]] = {}
    for parent in auth001_alerts:
        parents_by_key.setdefault(correlation_key(parent.trigger_event), []).append(parent)

    for key, parents in parents_by_key.items():
        assigned_parents: set[str] = set()
        for success in successes.get(key, []):
            candidates = []
            for parent in parents:
                if parent.alert_id in assigned_parents:
                    continue
                if success.timestamp_utc <= parent.trigger_event.timestamp_utc:
                    continue  # empate com a falha do limiar = ordem indeterminada
                before = [f for f in parent.failures if f.timestamp_utc < success.timestamp_utc]
                if not before:
                    continue
                last_fail = before[-1]
                if success.timestamp_utc - last_fail.timestamp_utc <= rc.interval:
                    candidates.append((parent, before))
            if not candidates:
                continue

            # Se um sucesso puder seguir mais de um episódio, vincula-o ao mais recente.
            parent, before = max(
                candidates,
                key=lambda item: (item[0].trigger_event.sort_key(), item[0].alert_id),
            )
            assigned_parents.add(parent.alert_id)
            alerts.append(Alert(
                alert_id=_alert_id("AUTH-003", parent.alert_id, success.event_uid),
                rule_id="AUTH-003",
                key=parent.key,
                trigger_event=success,
                evidence=[(failure, "failure") for failure in before] + [(success, "success")],
                parent_alert_id=parent.alert_id,
                threshold=parent.threshold,
                window_minutes=parent.window_minutes,
                interval_minutes=rc.success_within_minutes,
            ))

    alerts.sort(key=lambda alert: (alert.trigger_event.sort_key(), alert.alert_id))
    stats.alerts = len(alerts)
    return alerts, stats


def run_rules(events: list[Event], cfg: Config):
    a1, s1 = detect_auth001(events, cfg)
    a3, s3 = detect_auth003(events, a1, cfg)
    return a1 + a3, {"AUTH-001": s1, "AUTH-003": s3}
