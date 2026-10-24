"""Write SIMULATED crowd rows to `segment_crowd` (idempotent upsert)."""
from datetime import datetime

from app.crowd.simulator import SimParams, crowd_rows, simulate
from app.risk.config import thresholds
from app.risk.repo import load_topology

UPSERT = """
INSERT INTO segment_crowd (segment_id, ts, mode, persons, density_ppm2, level, simulated)
VALUES (%(segment_id)s, %(ts)s, %(mode)s, %(persons)s, %(density_ppm2)s, %(level)s, %(simulated)s)
ON CONFLICT (segment_id, ts, mode) DO UPDATE SET persons = EXCLUDED.persons,
    density_ppm2 = EXCLUDED.density_ppm2, level = EXCLUDED.level, simulated = EXCLUDED.simulated
"""


def run_crowd(c, mode: str, start: datetime, end: datetime, params: SimParams = SimParams()) -> int:
    topo = load_topology(c)
    rows = crowd_rows(topo, simulate(topo, start, end, params), mode, thresholds()["crowd"]["bands_ppm2"])
    with c.cursor() as cur:
        cur.executemany(UPSERT, rows)
    return len(rows)
