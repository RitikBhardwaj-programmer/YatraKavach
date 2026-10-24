"""Write SIMULATED crowd rows to `segment_crowd` (idempotent upsert), with the SIMULATED holding-area scenario."""
from datetime import datetime, timedelta

from psycopg.types.json import Jsonb

from app.crowd.simulator import HoldingParams, SimParams, apply_holding, crowd_rows, hold_points, simulate
from app.risk.config import thresholds
from app.risk.repo import load_topology

UPSERT = """
INSERT INTO segment_crowd (segment_id, ts, mode, persons, density_ppm2, level, simulated, scenario)
VALUES (%(segment_id)s, %(ts)s, %(mode)s, %(persons)s, %(density_ppm2)s, %(level)s, %(simulated)s, %(scenario)s)
ON CONFLICT (segment_id, ts, mode) DO UPDATE SET persons = EXCLUDED.persons,
    density_ppm2 = EXCLUDED.density_ppm2, level = EXCLUDED.level, simulated = EXCLUDED.simulated,
    scenario = EXCLUDED.scenario
"""


def holding_params() -> HoldingParams | None:
    h = thresholds()["crowd"].get("holding")
    if not h or not h.get("enabled"):
        return None
    return HoldingParams(tuple(h["points"]), int(h["hold_at_hazard_level"]), int(h["release_per_hour"]),
                        int(h["max_held_persons"]))


def _hazard_by_hour(c, mode: str, source: str | None, start: datetime, end: datetime) -> dict[datetime, dict[str, int]]:
    out: dict[datetime, dict[str, int]] = {}
    for r in c.execute("""SELECT segment_id, ts, level FROM segment_hazard
                          WHERE mode = %s AND (%s::text IS NULL OR source = %s) AND ts BETWEEN %s AND %s""",
                       (mode, source, source, start, end)).fetchall():
        hour = out.setdefault(r["ts"], {})
        hour[r["segment_id"]] = max(hour.get(r["segment_id"], 0), r["level"])
    return out


def run_crowd(c, mode: str, start: datetime, end: datetime, params: SimParams = SimParams(),
              hazard_source: str | None = None) -> int:
    """Simulate crowd; if the holding scenario is enabled, hold pilgrims below hazardous segments of
    `hazard_source` (the replay's proposal source; None = the highest level over all sources)."""
    topo = load_topology(c)
    hp = holding_params()
    arrivals = {(leaf, h): [] for leaf in topo.leaf_routes() for h in hp.points} if hp else None
    occupancy = simulate(topo, start, end, params, arrivals)
    notes = None
    if hp:
        times = sorted({ts for _, ts in occupancy})
        hazard = _hazard_by_hour(c, mode, hazard_source, start - timedelta(hours=1), end)
        holds = [hold_points(topo, hazard.get(ts, {}), hp) for ts in times]
        notes = apply_holding(occupancy, times, holds, arrivals, hp)
    rows = crowd_rows(topo, occupancy, mode, thresholds()["crowd"]["bands_ppm2"], notes)
    for r in rows:
        r["scenario"] = Jsonb(r["scenario"]) if r["scenario"] else None
    with c.cursor() as cur:
        cur.executemany(UPSERT, rows)
    return len(rows)
