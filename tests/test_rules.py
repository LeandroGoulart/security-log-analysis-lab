"""Comportamento de AUTH-001 e AUTH-003 (especificação em docs/regras.md)."""

import pytest

from authlab.events import read_events
from authlab.rules import run_rules

from conftest import failures, make_config, row


def detect(write_csv, rows, **cfg):
    parsed = read_events(write_csv(rows))
    alerts, stats = run_rules(parsed.events, make_config(**cfg))
    by_rule = {"AUTH-001": [], "AUTH-003": []}
    for a in alerts:
        by_rule[a.rule_id].append(a)
    return by_rule, stats, parsed


# --- AUTH-001: limiar e janela ---------------------------------------------

def test_fires_exactly_at_threshold(write_csv):
    alerts, _, _ = detect(write_csv, failures(5, every=60), threshold=5, window=10)
    assert len(alerts["AUTH-001"]) == 1
    assert len(alerts["AUTH-001"][0].failures) == 5


def test_does_not_fire_below_threshold(write_csv):
    alerts, stats, _ = detect(write_csv, failures(4, every=60), threshold=5)
    assert alerts["AUTH-001"] == []
    assert stats["AUTH-001"].eligible == 4


def test_window_boundary_is_inclusive(write_csv):
    # 5 falhas: primeira em t=0, quinta exatamente em t=10 min
    rows = [row(s) for s in (0, 150, 300, 450, 600)]
    alerts, _, _ = detect(write_csv, rows, threshold=5, window=10)
    assert len(alerts["AUTH-001"]) == 1


def test_events_outside_window_do_not_count(write_csv):
    # mesma sequência, mas a quinta 1 s depois do limite
    rows = [row(s) for s in (0, 150, 300, 450, 601)]
    alerts, _, _ = detect(write_csv, rows, threshold=5, window=10)
    assert alerts["AUTH-001"] == []


def test_slow_attack_is_not_detected_documented_limitation(write_csv):
    alerts, _, _ = detect(write_csv, failures(20, every=11 * 60), threshold=5, window=10)
    assert alerts["AUTH-001"] == []


@pytest.mark.parametrize("field,values", [
    ("user", ["alice", "bob"]),
    ("domain", ["LAB", "OUTRO"]),
    ("src_ip", ["10.0.0.5", "10.0.0.6"]),
    ("host", ["SRV-01", "SRV-02"]),
])
def test_different_key_fields_are_not_correlated(write_csv, field, values):
    rows = [row(i * 30, **{field: values[i % 2]}) for i in range(8)]  # 4 de cada
    alerts, _, _ = detect(write_csv, rows, threshold=5)
    assert alerts["AUTH-001"] == []


def test_key_comparison_ignores_case_of_user_domain_host(write_csv):
    rows = [row(0, user="Alice"), row(30, user="ALICE"), row(60, domain="lab"),
            row(90, host="srv-01"), row(120)]
    alerts, _, _ = detect(write_csv, rows, threshold=5)
    assert len(alerts["AUTH-001"]) == 1


def test_out_of_order_input_gives_same_alerts(write_csv):
    rows = failures(6, every=30)
    a, _, _ = detect(write_csv, rows)
    b, _, _ = detect(write_csv, [rows[i] for i in (3, 0, 5, 1, 4, 2)])
    ids = lambda r: [(x.alert_id, [e.event_uid for e, _ in x.evidence]) for x in r["AUTH-001"]]
    assert ids(a) == ids(b)


def test_equal_timestamps_are_inside_window(write_csv):
    alerts, _, _ = detect(write_csv, [row(0) for _ in range(5)], threshold=5)
    assert len(alerts["AUTH-001"]) == 1


# --- AUTH-001: alertas redundantes -----------------------------------------

def test_one_alert_per_continuous_episode(write_csv):
    alerts, _, _ = detect(write_csv, failures(30, every=120), threshold=5, window=10)
    assert len(alerts["AUTH-001"]) == 1
    assert len(alerts["AUTH-001"][0].failures) == 30


def test_new_episode_after_gap_larger_than_window(write_csv):
    rows = failures(5, every=30) + failures(5, every=30, start=3600)
    alerts, _, _ = detect(write_csv, rows, threshold=5, window=10)
    assert len(alerts["AUTH-001"]) == 2
    first, second = alerts["AUTH-001"]
    assert not {e.event_uid for e in first.failures} & {e.event_uid for e in second.failures}


def test_duplicates_do_not_inflate_the_count(write_csv):
    rows = [row(i * 30, rid=100 + i) for i in range(4)]
    rows += [row(0, rid=100)]  # duplicata exata
    alerts, _, parsed = detect(write_csv, rows, threshold=5)
    assert len(parsed.duplicates) == 1
    assert alerts["AUTH-001"] == []


# --- Campos ausentes ---------------------------------------------------------

@pytest.mark.parametrize("override,reason", [
    ({"src_ip": "-"}, "src_ip ausente"),
    ({"user": "-"}, "user ausente"),
    ({"domain": ""}, "domain ausente"),
])
def test_missing_correlation_fields_are_not_eligible_nor_grouped(write_csv, override, reason):
    alerts, stats, _ = detect(write_csv, failures(8, every=10, **override), threshold=5)
    assert alerts["AUTH-001"] == []
    assert stats["AUTH-001"].eligible == 0
    assert stats["AUTH-001"].ineligible_reasons[reason] == 8
    assert "Dados insuficientes" in stats["AUTH-001"].status_message()


def test_no_events_is_reported_as_insufficient_data(write_csv):
    _, stats, _ = detect(write_csv, [row(event_id=4624)])
    assert stats["AUTH-001"].candidates == 0
    assert "Dados insuficientes" in stats["AUTH-001"].status_message()


def test_partial_coverage_is_reported(write_csv):
    rows = failures(2) + failures(1, src_ip="-", start=500)
    _, stats, _ = detect(write_csv, rows)
    assert "cobertura é parcial" in stats["AUTH-001"].status_message()


# --- AUTH-003 ----------------------------------------------------------------

def test_success_after_threshold_fires_and_links_parent(write_csv):
    rows = failures(5, every=30) + [row(300, event_id=4624)]
    alerts, _, _ = detect(write_csv, rows, within=30)
    [a3] = alerts["AUTH-003"]
    [a1] = alerts["AUTH-001"]
    assert a3.parent_alert_id == a1.alert_id
    assert [r for _, r in a3.evidence] == ["failure"] * 5 + ["success"]
    assert a3.success.event_id == 4624


def test_success_links_to_most_recent_qualifying_episode(write_csv):
    rows = failures(5, every=30)
    rows += failures(5, every=30, start=15 * 60)
    rows += [row(20 * 60, event_id=4624)]

    alerts, _, _ = detect(write_csv, rows, within=30)
    [first, second] = alerts["AUTH-001"]
    [success_alert] = alerts["AUTH-003"]

    assert success_alert.parent_alert_id == second.alert_id
    assert {event.event_uid for event in success_alert.failures} == {
        event.event_uid for event in second.failures
    }


def test_success_before_failures_does_not_fire(write_csv):
    rows = [row(0, event_id=4624)] + failures(5, every=30, start=60)
    alerts, _, _ = detect(write_csv, rows)
    assert len(alerts["AUTH-001"]) == 1 and alerts["AUTH-003"] == []


def test_success_before_threshold_is_reached_does_not_fire(write_csv):
    rows = failures(3, every=30) + [row(100, event_id=4624)] + failures(2, every=30, start=120)
    alerts, _, _ = detect(write_csv, rows)
    assert len(alerts["AUTH-001"]) == 1 and alerts["AUTH-003"] == []


def test_success_at_same_timestamp_as_trigger_is_ambiguous(write_csv):
    rows = failures(5, every=30) + [row(120, event_id=4624)]  # mesmo instante da 5a falha
    alerts, _, _ = detect(write_csv, rows)
    assert alerts["AUTH-003"] == []


def test_success_interval_boundary_is_inclusive(write_csv):
    last = 4 * 30
    rows = failures(5, every=30) + [row(last + 30 * 60, event_id=4624)]
    alerts, _, _ = detect(write_csv, rows, within=30)
    assert len(alerts["AUTH-003"]) == 1


def test_success_outside_interval_does_not_fire(write_csv):
    last = 4 * 30
    rows = failures(5, every=30) + [row(last + 30 * 60 + 1, event_id=4624)]
    alerts, _, _ = detect(write_csv, rows, within=30)
    assert alerts["AUTH-003"] == []


@pytest.mark.parametrize("field,value", [
    ("user", "bob"), ("domain", "OUTRO"), ("src_ip", "10.9.9.9"), ("host", "SRV-99"),
])
def test_success_with_different_key_does_not_fire(write_csv, field, value):
    rows = failures(5, every=30) + [row(300, event_id=4624, **{field: value})]
    alerts, _, _ = detect(write_csv, rows)
    assert alerts["AUTH-003"] == []


def test_only_one_auth003_per_sequence(write_csv):
    rows = failures(5, every=30) + [row(300 + i * 60, event_id=4624) for i in range(4)]
    alerts, _, _ = detect(write_csv, rows)
    assert len(alerts["AUTH-003"]) == 1
    assert alerts["AUTH-003"][0].success.timestamp_utc.minute == 5  # o primeiro sucesso


def test_success_with_missing_ip_is_not_eligible(write_csv):
    rows = failures(5, every=30) + [row(300, event_id=4624, src_ip="-")]
    alerts, stats, _ = detect(write_csv, rows)
    assert alerts["AUTH-003"] == []
    assert stats["AUTH-003"].ineligible_reasons["src_ip ausente"] == 1


def test_auth003_disabled_produces_no_alert(write_csv):
    rows = failures(5, every=30) + [row(300, event_id=4624)]
    alerts, stats, _ = detect(write_csv, rows, a3=False)
    assert alerts["AUTH-003"] == [] and not stats["AUTH-003"].enabled


# --- Rastreabilidade ----------------------------------------------------------

def test_evidence_points_to_existing_events_and_source_lines(write_csv):
    rows = failures(5, every=30) + [row(300, event_id=4624)]
    alerts, _, parsed = detect(write_csv, rows)
    by_uid = {e.event_uid: e for e in parsed.events}
    for alert in alerts["AUTH-001"] + alerts["AUTH-003"]:
        for ev, _ in alert.evidence:
            assert by_uid[ev.event_uid] is ev
            assert rows[ev.source_line - 2]["timestamp"] == ev.timestamp_original
        assert alert.trigger_event.event_uid in {e.event_uid for e, _ in alert.evidence}


def test_ties_without_record_id_are_reproducible_regardless_of_line_order(write_csv):
    rows = [row(0, logon_type=str(t)) for t in (2, 3, 10, 11, 7)]  # mesmo instante, conteúdos distintos
    a, _, _ = detect(write_csv, rows)
    b, _, _ = detect(write_csv, list(reversed(rows)))
    key = lambda r: [(x.alert_id, x.trigger_event.event_uid) for x in r["AUTH-001"]]
    assert key(a) == key(b) and len(a["AUTH-001"]) == 1
