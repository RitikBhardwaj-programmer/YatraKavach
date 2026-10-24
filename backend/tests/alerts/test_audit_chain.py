from datetime import datetime, timedelta

import pytest

from app.alerts import audit


def make_chain(n: int = 4) -> list[dict]:
    rows, prev = [], audit.GENESIS
    t = datetime.fromisoformat("2025-08-26T11:00:00+05:30")
    for i in range(n):
        row = audit.chain({"id": i + 1, "ts": t + timedelta(minutes=i), "alert_id": 1, "actor": "off-1",
                           "action": "APPROVE", "from_state": "PROPOSED", "to_state": "PROPOSED", "reason": None,
                           "input_snapshot": {"risk": {"VD-OLD-01": {"risk_level": 3}}, "n": i},
                           "thresholds_version": "2026-10-23.1", "message_text": "Clear segment VD-OLD-01"}, prev)
        rows.append(row)
        prev = row["hash"]
    return rows


def test_intact_chain_verifies():
    assert audit.verify(make_chain()) == {"ok": True, "rows": 4}
    assert audit.verify([]) == {"ok": True, "rows": 0}


def test_first_row_links_to_genesis():
    assert make_chain(1)[0]["prev_hash"] == audit.GENESIS


@pytest.mark.parametrize("field, value", [
    ("reason", "edited later"), ("actor", "off-2"), ("message_text", "Hold pilgrims"),
    ("input_snapshot", {"risk": {"VD-OLD-01": {"risk_level": 1}}, "n": 1}),
    ("ts", datetime.fromisoformat("2025-08-26T12:00:00+05:30"))])
def test_tampered_content_is_detected(field, value):
    rows = make_chain()
    rows[1][field] = value
    result = audit.verify(rows)
    assert result["ok"] is False and result["broken_row"]["id"] == 2
    assert "content" in result["broken_row"]["reason"]


def test_deleted_row_is_detected():
    rows = make_chain()
    del rows[1]
    result = audit.verify(rows)
    assert result["ok"] is False and result["broken_row"]["id"] == 3


def test_recomputed_hash_does_not_hide_tampering():
    rows = make_chain()
    rows[1]["reason"] = "edited"
    rows[1]["hash"] = audit.row_hash(rows[1])  # attacker fixes this row's hash; the next link breaks
    assert audit.verify(rows)["broken_row"]["id"] == 3


def test_canonical_json_ignores_key_order_and_timezone():
    a = make_chain(1)[0]
    b = {**a, "input_snapshot": {"n": 0, "risk": {"VD-OLD-01": {"risk_level": 3}}},
         "ts": a["ts"].astimezone(datetime.now().astimezone().tzinfo)}
    assert audit.row_hash(a) == audit.row_hash(b)
