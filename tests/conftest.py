import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from authlab.config import parse_config
from authlab.events import REQUIRED_COLUMNS

ROOT = Path(__file__).resolve().parent.parent
RESOURCES = ROOT / "src" / "authlab" / "resources"
T0 = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)


def make_config(threshold=5, window=10, within=30, a1=True, a3=True):
    return parse_config({
        "display": {"timezone_label": "Teste", "utc_offset": "-03:00"},
        "rules": {
            "AUTH-001": {"enabled": a1, "threshold": threshold, "window_minutes": window},
            "AUTH-003": {"enabled": a3, "success_within_minutes": within},
        },
    })


def row(seconds=0, event_id=4625, user="alice", domain="LAB", src_ip="10.0.0.5",
        host="SRV-01", rid=None, logon_type="3", **overrides):
    """Monta uma linha de entrada; `seconds` é o deslocamento a partir de T0."""
    ts = (T0 + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
    failure = event_id == 4625
    data = {
        "event_record_id": "" if rid is None else str(rid),
        "timestamp": ts,
        "event_id": str(event_id),
        "channel": "Security",
        "host": host,
        "user": user,
        "domain": domain,
        "src_ip": src_ip,
        "logon_type": logon_type,
        "status": "0xC000006D" if failure else "",
        "sub_status": "0xC000006A" if failure else "",
        "outcome": "failure" if failure else "success",
    }
    data.update(overrides)
    return data


def failures(count, every=60, start=0, **kw):
    return [row(start + i * every, **kw) for i in range(count)]


@pytest.fixture
def write_csv(tmp_path):
    counter = {"n": 0}

    def _write(rows, name=None):
        counter["n"] += 1
        path = tmp_path / (name or f"input_{counter['n']}.csv")
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    return _write
