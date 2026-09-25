"""Validação, normalização e deduplicação da entrada."""

import pytest

from authlab.events import InputError, read_events

from conftest import row


def reasons_of(result):
    return [" | ".join(r.reasons) for r in result.rejected]


def test_timestamp_with_offset_is_normalized_to_utc(write_csv):
    path = write_csv([row(timestamp="2026-09-10T09:00:00-03:00")])
    ev = read_events(path).events[0]
    assert ev.timestamp_utc.isoformat() == "2026-09-10T12:00:00+00:00"
    assert ev.timestamp_original == "2026-09-10T09:00:00-03:00"


def test_timestamp_without_timezone_is_rejected_with_line(write_csv):
    path = write_csv([row(), row(timestamp="2026-09-10 09:00:00")])
    result = read_events(path)
    assert len(result.events) == 1
    assert result.rejected[0].source_line == 3
    assert "sem fuso" in reasons_of(result)[0]


def test_invalid_timestamp_is_rejected(write_csv):
    result = read_events(write_csv([row(timestamp="ontem às 10h")]))
    assert "formato inválido" in reasons_of(result)[0]


@pytest.mark.parametrize("field", ["timestamp", "event_id", "channel", "host", "outcome"])
def test_missing_required_field_is_rejected(write_csv, field):
    result = read_events(write_csv([row(**{field: "-"})]))
    assert result.events == []
    assert f"campo obrigatório ausente: {field}" in reasons_of(result)[0]


def test_event_and_outcome_must_be_consistent(write_csv):
    result = read_events(write_csv([row(event_id=4625, outcome="success")]))
    assert "inconsistência" in reasons_of(result)[0]


def test_success_with_failure_code_is_rejected(write_csv):
    result = read_events(write_csv([row(event_id=4624, status="0xC000006D")]))
    assert "4624 (sucesso) com código de falha" in reasons_of(result)[0]


def test_unsupported_event_id_and_channel_are_rejected(write_csv):
    result = read_events(write_csv([row(event_id=4634), row(channel="System")]))
    joined = " ".join(reasons_of(result))
    assert "fora do escopo" in joined and "channel inesperado" in joined


def test_dash_and_empty_become_missing_not_a_shared_value(write_csv):
    result = read_events(write_csv([row(src_ip="-", user=""), row(src_ip="")]))
    assert [e.src_ip for e in result.events] == [None, None]
    assert [e.src_ip_state for e in result.events] == ["missing", "missing"]
    assert result.events[0].user is None


def test_invalid_ip_is_rejected_not_treated_as_missing(write_csv):
    result = read_events(write_csv([row(src_ip="999.1.1.1")]))
    assert result.events == []
    assert "não é um endereço IP válido" in reasons_of(result)[0]


def test_ipv4_mapped_ipv6_is_normalized(write_csv):
    ev = read_events(write_csv([row(src_ip="::ffff:10.0.0.5")])).events[0]
    assert ev.src_ip == "10.0.0.5"


def test_status_codes_are_normalized(write_csv):
    ev = read_events(write_csv([row(status="0xc000006d", sub_status="0XC000006A")])).events[0]
    assert (ev.status, ev.sub_status) == ("0xC000006D", "0xC000006A")


def test_invalid_status_is_rejected(write_csv):
    result = read_events(write_csv([row(status="C000006D")]))
    assert "formato hexadecimal" in reasons_of(result)[0]


def test_duplicate_with_same_record_id_and_content_is_removed(write_csv):
    result = read_events(write_csv([row(rid=10), row(rid=10)]))
    assert len(result.events) == 1
    dup = result.duplicates[0]
    assert (dup.source_line, dup.first_source_line) == (3, 2)
    assert dup.event_uid == result.events[0].event_uid


def test_same_record_id_on_different_hosts_is_not_duplicate(write_csv):
    result = read_events(write_csv([row(rid=10, host="A"), row(rid=10, host="B")]))
    assert len(result.events) == 2 and not result.duplicates


def test_record_id_conflict_is_rejected(write_csv):
    result = read_events(write_csv([row(rid=10), row(60, rid=10)]))
    assert len(result.events) == 1
    assert "conflito" in reasons_of(result)[0]


def test_identical_rows_without_record_id_are_kept_and_counted(write_csv):
    result = read_events(write_csv([row(), row()]))
    assert len(result.events) == 2
    assert result.possible_duplicates_kept == 1
    assert len({e.event_uid for e in result.events}) == 2


def test_uid_is_stable_across_reordering(write_csv):
    rows = [row(0, rid=1), row(60, rid=2), row(120)]
    a = read_events(write_csv(rows))
    b = read_events(write_csv(list(reversed(rows))))
    assert [e.event_uid for e in a.events] == [e.event_uid for e in b.events]


def test_out_of_order_input_is_sorted_and_keeps_source_line(write_csv):
    result = read_events(write_csv([row(120), row(0), row(60)]))
    assert [e.source_line for e in result.events] == [3, 4, 2]


def test_every_line_is_accounted_for(write_csv):
    rows = [row(rid=1), row(rid=1), row(timestamp="x"), row(60)]
    result = read_events(write_csv(rows))
    assert result.rows_read == len(result.events) + len(result.rejected) + len(result.duplicates)


def test_missing_column_is_an_input_error(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("timestamp,event_id\n2026-01-01T00:00:00Z,4625\n", encoding="utf-8")
    with pytest.raises(InputError, match="colunas obrigatórias ausentes"):
        read_events(path)


def test_missing_file_is_an_input_error(tmp_path):
    with pytest.raises(InputError, match="não encontrado"):
        read_events(tmp_path / "nao-existe.csv")
