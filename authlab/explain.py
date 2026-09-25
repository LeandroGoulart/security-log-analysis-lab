"""Textos explicativos dos alertas.

Cada explicação separa: o que foi observado, por que a regra disparou,
explicações possíveis e o que precisa ser verificado. Os textos não
concluem que houve ataque, não atribuem ações a uma pessoa e não tratam
o IP como identificação de pessoa ou equipamento.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .config import Config
from .rules import Alert
from .windows import codes_text, failure_reason, logon_type_short


@dataclass
class Explanation:
    observed: list[str]
    why: str
    possible: list[str]
    verify: list[str]
    plain_summary: str


def fmt_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def fmt_local(dt: datetime, cfg: Config) -> str:
    local = dt.astimezone(cfg.display_tz)
    return f"{local.strftime('%d/%m/%Y %H:%M:%S')} (UTC{cfg.display_utc_offset})"


def fmt_duration(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    if total < 60:
        return f"{total} s"
    minutes, seconds = divmod(total, 60)
    if minutes < 60:
        return f"{minutes} min" + (f" {seconds} s" if seconds else "")
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes} min"


def _reason_lines(alert: Alert) -> list[str]:
    counter = Counter(
        (failure_reason(e.status, e.sub_status), codes_text(e.status, e.sub_status))
        for e in alert.failures
    )
    return [f"{n}× {reason} [{codes}]" for (reason, codes), n in counter.most_common()]


def _regularity(failures) -> str | None:
    if len(failures) < 4:
        return None
    gaps = [
        (b.timestamp_utc - a.timestamp_utc).total_seconds()
        for a, b in zip(failures, failures[1:])
    ]
    median = statistics.median(gaps)
    if median < 30:
        return None
    if max(gaps) - min(gaps) <= 0.1 * median:
        return (
            f"As falhas ocorreram em intervalos praticamente constantes "
            f"(cerca de {fmt_duration(timedelta(seconds=median))}). Intervalos regulares são "
            "comuns em processos automatizados, como serviços, tarefas agendadas ou "
            "aplicações com credencial salva. Isso não exclui outras causas."
        )
    return None


def _common_observations(alert: Alert, cfg: Config) -> list[str]:
    failures = alert.failures
    first, last = failures[0], failures[-1]
    k = alert.key
    obs = [
        f"{len(failures)} falha(s) de autenticação (evento 4625) para a conta "
        f"{k.domain}\\{k.user}, com IP de origem {k.src_ip}, registradas no computador "
        f"{k.host}, entre {fmt_local(first.timestamp_utc, cfg)} e "
        f"{fmt_local(last.timestamp_utc, cfg)} "
        f"(intervalo de {fmt_duration(last.timestamp_utc - first.timestamp_utc)}).",
        "Motivo registrado nos eventos: " + "; ".join(_reason_lines(alert)) + ".",
        "Tipo de logon: " + ", ".join(
            f"{n}× {lt}" for lt, n in Counter(logon_type_short(e.logon_type) for e in failures)
            .most_common()
        ) + ".",
    ]
    if k.src_ip in ("127.0.0.1", "::1"):
        obs.append(
            "O IP de origem é o próprio computador (localhost, segundo a documentação da "
            "Microsoft), o que é típico de logon local."
        )
    reg = _regularity(failures)
    if reg:
        obs.append(reg)
    return obs


def explain_auth001(alert: Alert, cfg: Config) -> Explanation:
    k = alert.key
    failures = alert.failures
    trigger = alert.trigger_event
    observed = _common_observations(alert, cfg)
    why = (
        f"A regra AUTH-001 dispara quando há pelo menos {alert.threshold} falhas com a mesma "
        f"conta, domínio, IP de origem e computador de registro em uma janela de até "
        f"{alert.window_minutes} minutos. O limiar foi atingido em "
        f"{fmt_local(trigger.timestamp_utc, cfg)} (evento {trigger.event_uid}, "
        f"linha {trigger.source_line}). As falhas seguintes, sem intervalo maior que "
        f"{alert.window_minutes} minutos entre si, foram agregadas a este mesmo alerta."
    )
    possible = [
        "Erro de digitação repetido ou senha esquecida por quem usa a conta.",
        "Credencial antiga salva em aplicação, serviço, tarefa agendada, unidade mapeada "
        "ou dispositivo, tentando autenticar sozinha.",
        "Tentativa de descobrir a senha por tentativa e erro (força bruta).",
        "Teste de segurança autorizado.",
    ]
    verify = [
        "Existe logon bem-sucedido posterior com a mesma chave? Veja se há alerta AUTH-003 "
        "vinculado e a linha do tempo.",
        f"A quem o IP {k.src_ip} estava atribuído nesse horário (DHCP, VPN, inventário)? "
        "O IP indica uma origem de rede, não identifica uma pessoa com certeza.",
        "O responsável pela conta reconhece as tentativas? Confirme por um canal "
        "independente (telefone, presencial), não por e-mail da própria conta.",
        "Houve troca recente de senha ou mudança de configuração envolvendo esta conta "
        "(registros de mudança, chamados)?",
        "Há falhas da mesma origem contra outras contas ou outros destinos? Esta regra não "
        "cobre tentativas distribuídas.",
        "A conta foi bloqueada? Verifique a política de bloqueio e o impacto no serviço.",
    ]
    duration = fmt_duration(failures[-1].timestamp_utc - failures[0].timestamp_utc)
    plain = (
        f"Foram registradas {len(failures)} tentativas de acesso sem sucesso à conta "
        f"{k.user} em {duration}, vindas do mesmo endereço de rede e para o mesmo "
        "computador. Isso pode ter uma causa simples, como uma senha salva "
        "desatualizada, ou indicar uma tentativa de descobrir a senha. É necessário "
        "verificar o contexto antes de concluir."
    )
    return Explanation(observed, why, possible, verify, plain)


def explain_auth003(alert: Alert, cfg: Config) -> Explanation:
    k = alert.key
    failures = alert.failures
    success = alert.success
    gap = success.timestamp_utc - failures[-1].timestamp_utc
    observed = _common_observations(alert, cfg) + [
        f"Em seguida, logon bem-sucedido (evento 4624) com os mesmos campos de correlação em "
        f"{fmt_local(success.timestamp_utc, cfg)}, {fmt_duration(gap)} após a última falha. "
        f"Tipo de logon do sucesso: {logon_type_short(success.logon_type)}.",
    ]
    why = (
        f"A regra AUTH-003 dispara quando, depois de uma sequência que atende à AUTH-001 "
        f"(alerta {alert.parent_alert_id}), ocorre um logon bem-sucedido com a mesma conta, "
        f"domínio, IP de origem e computador em até {alert.interval_minutes} minutos após a "
        "última falha."
    )
    possible = [
        "A pessoa responsável errou a senha várias vezes e depois acertou.",
        "Uma credencial salva desatualizada foi corrigida (por exemplo, após troca de senha "
        "em aplicação ou serviço).",
        "Alguém descobriu a senha após várias tentativas e obteve acesso.",
        "Teste de segurança autorizado.",
    ]
    verify = [
        "O responsável pela conta reconhece este acesso, neste horário e a partir desta "
        "origem? Confirme por canal independente.",
        "Houve mudança planejada (troca de senha, manutenção) que explique a sequência?",
        "O que foi feito na sessão iniciada? Consulte outros registros disponíveis "
        "(fora do escopo desta ferramenta).",
        f"A quem o IP {k.src_ip} estava atribuído nesse horário?",
        "Se o acesso não for reconhecido, escale conforme o procedimento de resposta a "
        "incidentes da organização.",
    ]
    plain = (
        f"Foram registradas {len(failures)} falhas de autenticação para a conta {k.user} "
        f"em {fmt_duration(failures[-1].timestamp_utc - failures[0].timestamp_utc)}, seguidas "
        "de um logon bem-sucedido com os mesmos campos de correlação. A sequência pode ter "
        "uma explicação legítima ou indicar tentativa de acesso indevido. É necessário "
        "verificar o contexto antes de concluir."
    )
    return Explanation(observed, why, possible, verify, plain)


def explain(alert: Alert, cfg: Config) -> Explanation:
    if alert.rule_id == "AUTH-001":
        return explain_auth001(alert, cfg)
    return explain_auth003(alert, cfg)
