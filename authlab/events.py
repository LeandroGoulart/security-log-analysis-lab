"""Leitura, validação, normalização e deduplicação do CSV de entrada.

O formato aceito está documentado em docs/formato-csv.md. Não é o CSV
exportado pelo Event Viewer nem EVTX.

Princípios:
- nenhum registro é descartado em silêncio: cada linha lida termina como
  evento válido, rejeição (com motivo) ou duplicata (com referência);
- valores vazios e "-" viram ausência explícita (None), nunca um valor
  "coringa" que agruparia origens desconhecidas; IP informado mas inválido
  é rejeitado (problema de qualidade do dado, não ausência);
- timestamps precisam de fuso explícito e são convertidos para UTC.
"""

from __future__ import annotations

import csv
import hashlib
import ipaddress
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_COLUMNS = [
    "event_record_id",
    "timestamp",
    "event_id",
    "channel",
    "host",
    "user",
    "domain",
    "src_ip",
    "logon_type",
    "status",
    "sub_status",
    "outcome",
]

SUPPORTED_EVENTS = {4624: "success", 4625: "failure"}
MISSING_TOKENS = {"", "-"}
_HEX_RE = re.compile(r"^0[xX]([0-9a-fA-F]{1,8})$")


class InputError(ValueError):
    """Arquivo de entrada inutilizável como um todo (ausente, vazio, sem colunas)."""


@dataclass(frozen=True)
class Event:
    event_uid: str
    event_record_id: int | None
    timestamp_utc: datetime
    timestamp_original: str
    event_id: int
    channel: str
    host: str
    user: str | None
    domain: str | None
    src_ip: str | None
    src_ip_state: str  # "valid" | "missing" (IP inválido é rejeitado)
    src_ip_original: str | None
    logon_type: int | None
    status: str | None
    sub_status: str | None
    outcome: str
    source_file: str
    source_line: int
    uid_basis: str  # "event_record_id" | "content"

    @property
    def source_ref(self) -> str:
        return f"{self.source_file}:{self.source_line}"

    def sort_key(self):
        rid = self.event_record_id
        return (
            self.timestamp_utc,
            0 if rid is not None else 1,
            rid if rid is not None else 0,
            self.event_uid,  # desempate reproduzível, independente da posição da linha
        )


@dataclass(frozen=True)
class Rejected:
    source_file: str
    source_line: int
    reasons: tuple[str, ...]
    raw: dict


@dataclass(frozen=True)
class Duplicate:
    source_file: str
    source_line: int
    event_uid: str
    first_source_line: int


@dataclass
class ParseResult:
    source_file: str
    rows_read: int = 0
    events: list[Event] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    duplicates: list[Duplicate] = field(default_factory=list)
    possible_duplicates_kept: int = 0
    extra_columns: list[str] = field(default_factory=list)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return None if value in MISSING_TOKENS else value


def parse_timestamp(value: str) -> datetime:
    """Converte ISO 8601 com fuso explícito para UTC. Levanta ValueError."""
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"timestamp em formato inválido: {value!r} (use ISO 8601)") from None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(
            f"timestamp sem fuso horário: {value!r} (inclua Z ou um deslocamento como -03:00)"
        )
    return dt.astimezone(timezone.utc)


def normalize_ip(value: str | None) -> tuple[str | None, str]:
    """Retorna (ip_canônico, estado). IPv4 mapeado em IPv6 (::ffff:a.b.c.d) vira IPv4."""
    if value is None:
        return None, "missing"
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return None, "invalid"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return str(ip), "valid"


def normalize_hex(value: str | None) -> str | None:
    if value is None:
        return None
    match = _HEX_RE.match(value)
    if not match:
        raise ValueError(value)
    digits = match.group(1).upper().lstrip("0") or "0"
    return "0x" + digits


def _uid(*parts) -> str:
    text = "|".join("" if p is None else str(p) for p in parts)
    return "e" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _validate_row(raw: dict, source_file: str, line: int):
    """Retorna (dados_normalizados, motivos_de_rejeição)."""
    reasons: list[str] = []
    v = {k: _clean(raw.get(k)) for k in REQUIRED_COLUMNS}

    for name in ("timestamp", "event_id", "channel", "host", "outcome"):
        if v[name] is None:
            reasons.append(f"campo obrigatório ausente: {name}")

    ts = None
    if v["timestamp"] is not None:
        try:
            ts = parse_timestamp(v["timestamp"])
        except ValueError as exc:
            reasons.append(str(exc))

    event_id = None
    if v["event_id"] is not None:
        if not v["event_id"].isdigit():
            reasons.append(f"event_id não numérico: {v['event_id']!r}")
        else:
            event_id = int(v["event_id"])
            if event_id not in SUPPORTED_EVENTS:
                reasons.append(f"event_id fora do escopo (aceitos: 4624, 4625): {event_id}")
                event_id = None

    channel = v["channel"]
    if channel is not None:
        if channel.casefold() != "security":
            reasons.append(f"channel inesperado para 4624/4625: {channel!r} (esperado: Security)")
        channel = "Security"

    outcome = v["outcome"].lower() if v["outcome"] else None
    if outcome is not None and outcome not in ("success", "failure"):
        reasons.append(f"outcome inválido: {v['outcome']!r} (use success ou failure)")
        outcome = None
    if event_id is not None and outcome is not None and SUPPORTED_EVENTS[event_id] != outcome:
        reasons.append(
            f"inconsistência: event_id {event_id} exige outcome={SUPPORTED_EVENTS[event_id]}, "
            f"recebido {outcome}"
        )

    record_id = None
    if v["event_record_id"] is not None:
        if not v["event_record_id"].isdigit() or int(v["event_record_id"]) == 0:
            reasons.append(f"event_record_id deve ser inteiro positivo: {v['event_record_id']!r}")
        else:
            record_id = int(v["event_record_id"])

    logon_type = None
    if v["logon_type"] is not None:
        if not v["logon_type"].isdigit():
            reasons.append(f"logon_type não numérico: {v['logon_type']!r}")
        else:
            logon_type = int(v["logon_type"])

    codes = {}
    for name in ("status", "sub_status"):
        try:
            codes[name] = normalize_hex(v[name])
        except ValueError:
            reasons.append(f"{name} fora do formato hexadecimal 0x...: {v[name]!r}")
            codes[name] = None
    if event_id == 4624 and any(c not in (None, "0x0") for c in codes.values()):
        reasons.append("inconsistência: evento 4624 (sucesso) com código de falha em status/sub_status")
    if event_id == 4625 and codes["status"] == "0x0":
        reasons.append("inconsistência: evento 4625 (falha) com status 0x0")

    src_ip, ip_state = normalize_ip(v["src_ip"])
    if ip_state == "invalid":
        reasons.append(f"src_ip informado não é um endereço IP válido: {v['src_ip']!r}")

    data = dict(
        event_record_id=record_id,
        timestamp_utc=ts,
        timestamp_original=(raw.get("timestamp") or "").strip(),
        event_id=event_id,
        channel=channel,
        host=v["host"],
        user=v["user"],
        domain=v["domain"],
        src_ip=src_ip,
        src_ip_state=ip_state,
        src_ip_original=v["src_ip"],
        logon_type=logon_type,
        status=codes["status"],
        sub_status=codes["sub_status"],
        outcome=outcome,
        source_file=source_file,
        source_line=line,
    )
    return data, reasons


def _fingerprint(d: dict) -> tuple:
    return (
        d["timestamp_utc"].isoformat(),
        d["event_id"],
        d["channel"],
        d["host"].casefold(),
        (d["user"] or "").casefold(),
        (d["domain"] or "").casefold(),
        d["src_ip"] or d["src_ip_original"] or "",
        d["logon_type"],
        d["status"],
        d["sub_status"],
        d["outcome"],
    )


def read_events(path: str | Path, display_name: str | None = None) -> ParseResult:
    path = Path(path)
    if not path.is_file():
        raise InputError(f"Arquivo de entrada não encontrado: {path}")
    source_file = display_name or path.name
    result = ParseResult(source_file=source_file)

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise InputError(f"{path} está vazio ou não tem cabeçalho.")
        header = [h.strip() for h in reader.fieldnames]
        reader.fieldnames = header
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise InputError(
                f"{path}: colunas obrigatórias ausentes no cabeçalho: {', '.join(missing)}. "
                "Veja docs/formato-csv.md."
            )
        result.extra_columns = [c for c in header if c not in REQUIRED_COLUMNS]

        by_record_key: dict[tuple, tuple[tuple, int, str]] = {}
        content_seen: dict[tuple, int] = {}

        for raw in reader:
            line = reader.line_num
            result.rows_read += 1
            if None in raw:  # mais campos que colunas no cabeçalho
                result.rejected.append(
                    Rejected(source_file, line, ("linha com mais colunas que o cabeçalho",),
                             {k: v for k, v in raw.items() if k is not None})
                )
                continue
            data, reasons = _validate_row(raw, source_file, line)
            if reasons:
                result.rejected.append(Rejected(source_file, line, tuple(reasons), dict(raw)))
                continue

            fp = _fingerprint(data)
            if data["event_record_id"] is not None:
                key = (data["host"].casefold(), data["channel"], data["event_record_id"])
                uid = _uid("rid", *key)
                if key in by_record_key:
                    first_fp, first_line, first_uid = by_record_key[key]
                    if first_fp == fp:
                        result.duplicates.append(Duplicate(source_file, line, first_uid, first_line))
                    else:
                        result.rejected.append(Rejected(
                            source_file, line,
                            (f"conflito: mesmo host/channel/event_record_id da linha {first_line} "
                             "com conteúdo diferente",),
                            dict(raw),
                        ))
                    continue
                by_record_key[key] = (fp, line, uid)
                basis = "event_record_id"
            else:
                occurrence = content_seen.get(fp, 0)
                content_seen[fp] = occurrence + 1
                if occurrence:
                    result.possible_duplicates_kept += 1
                uid = _uid("content", *fp, occurrence)
                basis = "content"

            result.events.append(Event(event_uid=uid, uid_basis=basis, **data))

    result.events.sort(key=Event.sort_key)
    return result
