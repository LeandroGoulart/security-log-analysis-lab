"""Execução de ponta a ponta e gravação das saídas."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .events import Event, ParseResult, read_events
from .explain import explain
from .rules import Alert, RuleStats, run_rules
from .windows import failure_reason

OUTPUT_FILES = {
    "events": "events_normalized.csv",
    "alerts": "alerts.csv",
    "evidence": "alert_evidence.csv",
    "rejected": "rejected.csv",
    "duplicates": "duplicates.csv",
    "summary": "summary.json",
    "report": "report.html",
}


@dataclass
class RunResult:
    run_id: str
    generated_at: datetime
    title: str
    description: str
    input_path: Path
    input_sha256: str
    config: Config
    parsed: ParseResult
    alerts: list[Alert]
    stats: dict[str, RuleStats]

    @property
    def events(self) -> list[Event]:
        return self.parsed.events

    def alerts_by_rule(self) -> dict[str, int]:
        counts = {"AUTH-001": 0, "AUTH-003": 0}
        for a in self.alerts:
            counts[a.rule_id] += 1
        return counts


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(input_path: str | Path, cfg: Config, title: str = "", description: str = "",
            now: datetime | None = None) -> RunResult:
    input_path = Path(input_path)
    parsed = read_events(input_path)
    alerts, stats = run_rules(parsed.events, cfg)
    generated = now or datetime.now(timezone.utc)
    digest = sha256_file(input_path)
    run_id = f"{generated.strftime('%Y%m%dT%H%M%SZ')}-{digest[:6]}"
    return RunResult(run_id, generated, title or input_path.stem, description, input_path,
                     digest, cfg, parsed, alerts, stats)


# --- CSV -------------------------------------------------------------------

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(value) -> str:
    """Neutraliza injeção de fórmulas em planilhas (CSV aberto no Excel)."""
    if value is None:
        return ""
    text = str(value)
    if text and text.startswith(_FORMULA_PREFIXES):
        return "'" + text
    return text


def _write_csv(path: Path, header: list[str], rows) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for row in rows:
            writer.writerow([safe_cell(v) for v in row])


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def summary_dict(r: RunResult) -> dict:
    p = r.parsed
    return {
        "run_id": r.run_id,
        "generated_at_utc": _iso(r.generated_at),
        "title": r.title,
        "input_file": p.source_file,
        "input_sha256": r.input_sha256,
        "config_file": r.config.source_path,
        "config": {
            "AUTH-001": {"enabled": r.config.auth001.enabled,
                         "threshold": r.config.auth001.threshold,
                         "window_minutes": r.config.auth001.window_minutes},
            "AUTH-003": {"enabled": r.config.auth003.enabled,
                         "success_within_minutes": r.config.auth003.success_within_minutes},
        },
        "records": {
            "read": p.rows_read,
            "valid": len(p.events),
            "rejected": len(p.rejected),
            "duplicates_removed": len(p.duplicates),
            "possible_duplicates_kept": p.possible_duplicates_kept,
        },
        "rules": {
            rid: {"enabled": s.enabled, "candidates": s.candidates, "eligible": s.eligible,
                  "ineligible": s.ineligible,
                  "ineligible_reasons": dict(sorted(s.ineligible_reasons.items())),
                  "alerts": s.alerts, "status": s.status_message()}
            for rid, s in r.stats.items()
        },
        "alerts": [a.alert_id for a in r.alerts],
    }


def write_outputs(r: RunResult, out_dir: str | Path) -> dict[str, Path]:
    from .report import render_report  # import tardio evita ciclo

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {k: out / v for k, v in OUTPUT_FILES.items()}

    _write_csv(paths["events"], [
        "event_uid", "uid_basis", "event_record_id", "timestamp_utc", "timestamp_original",
        "event_id", "channel", "host", "user", "domain", "src_ip", "src_ip_state",
        "src_ip_original", "logon_type", "status", "sub_status", "outcome",
        "failure_reason", "source_file", "source_line",
    ], (
        [e.event_uid, e.uid_basis, e.event_record_id, _iso(e.timestamp_utc),
         e.timestamp_original, e.event_id, e.channel, e.host, e.user, e.domain, e.src_ip,
         e.src_ip_state, e.src_ip_original, e.logon_type, e.status, e.sub_status, e.outcome,
         failure_reason(e.status, e.sub_status) if e.event_id == 4625 else "",
         e.source_file, e.source_line]
        for e in r.events
    ))

    _write_csv(paths["alerts"], [
        "alert_id", "rule_id", "rule_name", "parent_alert_id", "domain", "user", "src_ip",
        "host", "first_seen_utc", "last_seen_utc", "trigger_time_utc", "trigger_event_uid",
        "failure_count", "success_event_uid", "summary",
    ], (
        [a.alert_id, a.rule_id, a.rule_name, a.parent_alert_id, a.key.domain, a.key.user,
         a.key.src_ip, a.key.host, _iso(a.first_seen), _iso(a.last_seen),
         _iso(a.trigger_event.timestamp_utc), a.trigger_event.event_uid, len(a.failures),
         a.success.event_uid if a.success else "", explain(a, r.config).plain_summary]
        for a in r.alerts
    ))

    _write_csv(paths["evidence"], [
        "alert_id", "sequence", "role", "is_trigger", "event_uid", "event_record_id",
        "timestamp_utc", "event_id", "source_file", "source_line",
    ], (
        [a.alert_id, i, role, "yes" if e.event_uid == a.trigger_event.event_uid else "no",
         e.event_uid, e.event_record_id, _iso(e.timestamp_utc), e.event_id,
         e.source_file, e.source_line]
        for a in r.alerts
        for i, (e, role) in enumerate(a.evidence, start=1)
    ))

    from .events import REQUIRED_COLUMNS
    _write_csv(paths["rejected"],
               ["source_file", "source_line", "reasons"] + [f"raw_{c}" for c in REQUIRED_COLUMNS],
               ([x.source_file, x.source_line, " | ".join(x.reasons)]
                + [x.raw.get(c, "") for c in REQUIRED_COLUMNS] for x in r.parsed.rejected))

    _write_csv(paths["duplicates"],
               ["source_file", "source_line", "duplicate_of_event_uid", "first_source_line"],
               ([d.source_file, d.source_line, d.event_uid, d.first_source_line]
                for d in r.parsed.duplicates))

    paths["summary"].write_text(json.dumps(summary_dict(r), ensure_ascii=False, indent=2),
                                encoding="utf-8")
    paths["report"].write_text(render_report(r, paths), encoding="utf-8")
    return paths
