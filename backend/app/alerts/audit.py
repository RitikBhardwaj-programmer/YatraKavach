"""Hash chain for the append-only audit log (pure, no DB).

hash = sha256(prev_hash + canonical JSON of the row), where the row is every column except `id` and `hash`.
Canonical JSON: sorted keys, no spaces, UTF-8, timestamps as UTC ISO 8601 with microseconds.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

GENESIS = "0" * 64
HASHED_FIELDS = ("ts", "alert_id", "actor", "action", "from_state", "to_state", "reason", "input_snapshot",
                 "thresholds_version", "message_text", "prev_hash")


def _norm(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds")
    return value


def canonical(row: dict[str, Any]) -> str:
    payload = {k: _norm(row.get(k)) for k in HASHED_FIELDS}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def row_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256((row["prev_hash"] + canonical(row)).encode("utf-8")).hexdigest()


def chain(row: dict[str, Any], prev_hash: str) -> dict[str, Any]:
    """Return `row` with `prev_hash` and `hash` filled in."""
    out = {**row, "prev_hash": prev_hash}
    out["hash"] = row_hash(out)
    return out


def verify(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute the chain over rows in id order. Returns {"ok": True, "rows": n} or the first broken row."""
    prev = GENESIS
    for i, row in enumerate(rows):
        problem = None
        if row["prev_hash"] != prev:
            problem = "prev_hash does not match the previous row's hash"
        elif row_hash(row) != row["hash"]:
            problem = "hash does not match the row content"
        if problem:
            return {"ok": False, "rows": len(rows), "checked": i,
                    "broken_row": {"id": row.get("id"), "reason": problem}}
        prev = row["hash"]
    return {"ok": True, "rows": len(rows)}
