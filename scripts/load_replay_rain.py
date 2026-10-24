"""Load every data/replay/rain_*.json into `rain_hourly` with mode `replay` (idempotent upsert).

File times are local IST (Asia/Kolkata, no DST); they are stored as timestamptz.
Run from the repo root: python scripts/load_replay_rain.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import conn, pool  # noqa: E402
from app.hazard.engine import IST  # noqa: E402

REPLAY_DIR = ROOT / "data" / "replay"


def rows(data: dict) -> list[tuple]:
    if data["timezone"] != "Asia/Kolkata":
        raise ValueError(f"expected Asia/Kolkata times, got {data['timezone']}")
    return [(data["point"], datetime.fromisoformat(t).replace(tzinfo=IST), data["source"], "replay", float(mm))
            for t, mm in zip(data["time"], data["precip_mm"]) if mm is not None]


def main() -> None:
    files = sorted(REPLAY_DIR.glob("rain_*.json"))
    if not files:
        sys.exit(f"no rain_*.json in {REPLAY_DIR}")
    with conn() as c, c.cursor() as cur:
        for f in files:
            r = rows(json.loads(f.read_text(encoding="utf-8")))
            cur.executemany(
                """INSERT INTO rain_hourly (point, ts, source, mode, precip_mm) VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (point, ts, source, mode) DO UPDATE SET precip_mm = EXCLUDED.precip_mm""", r)
            print(f"{f.name}: {len(r)} rows")


if __name__ == "__main__":
    main()
    pool().close()
