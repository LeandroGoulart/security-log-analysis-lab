"""Saídas, relatório HTML e execução completa dos cenários."""

import csv
import json
import re

import pytest

from authlab.__main__ import compare_expected, load_scenarios, main
from authlab.config import load_config
from authlab.pipeline import analyze, safe_cell, summary_dict, write_outputs

from conftest import RESOURCES, ROOT, failures, make_config, row

SCENARIOS = load_scenarios()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def test_html_escapes_content_from_data(write_csv, tmp_path):
    evil = '<script>alert("x")</script>'
    rows = failures(5, every=30, user=evil) + [row(300, event_id=4624, user=evil)]
    result = analyze(write_csv(rows), make_config())
    paths = write_outputs(result, tmp_path / "out")
    page = paths["report"].read_text(encoding="utf-8")
    assert evil not in page
    assert "&lt;script&gt;" in page


def test_report_has_no_external_resources(write_csv, tmp_path):
    result = analyze(write_csv(failures(5)), make_config())
    page = write_outputs(result, tmp_path / "out")["report"].read_text(encoding="utf-8")
    assert not re.search(r'(src|href)\s*=\s*"(https?:)?//', page)
    assert "<script" not in page.lower()


def test_csv_cells_are_protected_against_formula_injection():
    assert safe_cell("=HYPERLINK(1)") == "'=HYPERLINK(1)"
    assert safe_cell("alice") == "alice"
    assert safe_cell(None) == ""


def test_evidence_csv_links_alerts_to_events(write_csv, tmp_path):
    rows = failures(5, every=30) + [row(300, event_id=4624)]
    paths = write_outputs(analyze(write_csv(rows), make_config()), tmp_path / "out")
    events = {r["event_uid"]: r for r in read_csv(paths["events"])}
    alerts = read_csv(paths["alerts"])
    evidence = read_csv(paths["evidence"])
    assert {a["rule_id"] for a in alerts} == {"AUTH-001", "AUTH-003"}
    for ev in evidence:
        assert ev["event_uid"] in events
        assert events[ev["event_uid"]]["source_line"] == ev["source_line"]
    assert sum(ev["is_trigger"] == "yes" for ev in evidence) == len(alerts)


def test_rejections_are_written_with_reason_and_line(write_csv, tmp_path):
    private_user = "user-private-example"
    rows = [row(), row(timestamp="private-invalid-timestamp", user=private_user)]
    paths = write_outputs(analyze(write_csv(rows), make_config()), tmp_path / "out")
    [rej] = read_csv(paths["rejected"])
    assert rej["source_line"] == "3" and "formato inválido" in rej["reasons"]
    rejected_text = paths["rejected"].read_text(encoding="utf-8-sig")
    assert private_user not in rejected_text
    assert "private-invalid-timestamp" not in rejected_text
    assert set(rej) == {"source_file", "source_line", "reasons"}


@pytest.mark.parametrize("folder,meta", SCENARIOS, ids=[f.name for f, _ in SCENARIOS])
def test_scenarios_match_expected_results(folder, meta, tmp_path):
    cfg = load_config(RESOURCES / "config" / "rules.yaml")
    result = analyze(folder / meta["input"], cfg, meta["title"])
    write_outputs(result, tmp_path / folder.name)
    assert compare_expected(summary_dict(result), meta["expected"]) == []


def test_there_are_three_scenarios():
    assert [f.name for f, _ in SCENARIOS] == [
        "01-erro-digitacao", "02-acesso-suspeito", "03-credencial-servico"]


def test_demo_command_runs_end_to_end(tmp_path, capsys):
    out = tmp_path / "demo"
    assert main(["demo", "--out", str(out), "--strict"]) == 0
    assert (out / "index.html").is_file()
    for folder, _ in SCENARIOS:
        summary = json.loads((out / folder.name / "summary.json").read_text(encoding="utf-8"))
        assert summary["records"]["read"] > 0
    assert "conforme o esperado" in capsys.readouterr().out


def test_invalid_config_returns_error_code(tmp_path, capsys):
    bad = tmp_path / "rules.yaml"
    bad.write_text("display: {}\n", encoding="utf-8")
    assert main(["demo", "--config", str(bad), "--out", str(tmp_path / "o")]) == 2
    assert "Erro:" in capsys.readouterr().err


def test_calibration_changes_results(tmp_path):
    """Limiar 3 passa a alertar no cenário de erro de digitação (custo: ruído)."""
    folder = RESOURCES / "scenarios" / "01-erro-digitacao"
    cfg = load_config(ROOT / "config" / "exercicios" / "limiar-3.yaml")
    result = analyze(folder / "events.csv", cfg)
    assert result.alerts_by_rule() == {"AUTH-001": 1, "AUTH-003": 1}


def test_exploratory_sample_documents_v1_coverage():
    """data/samples/auth_events.csv: a v1 detecta força bruta, mas não spraying/fora de horário."""
    result = analyze(ROOT / "data" / "samples" / "auth_events.csv",
                     load_config(RESOURCES / "config" / "rules.yaml"))
    assert result.alerts_by_rule() == {"AUTH-001": 2, "AUTH-003": 1}
    assert {a.key.user for a in result.alerts} == {"maria.souza", "joao.silva"}
