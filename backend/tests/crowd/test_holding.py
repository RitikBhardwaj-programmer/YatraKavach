"""SIMULATED holding-area scenario (pure): where ascent stops, and how the held queue grows and drains."""
from datetime import datetime, timedelta

from app.crowd.simulator import HoldingParams, apply_holding, hold_points
from app.risk.config import segments_geojson
from app.risk.topology import Topology, from_geojson

TOPO = Topology(from_geojson(segments_geojson()))
HP = HoldingParams(("VD-TRUNK-01", "VD-TRUNK-07", "VD-TRUNK-13"), 2, 100, 250)
T0 = datetime.fromisoformat("2025-08-26T06:00:00+05:30")


def test_no_hold_when_nothing_is_hazardous():
    assert hold_points(TOPO, {"VD-OLD-03": 1}, HP) == {}


def test_hold_at_nearest_point_below_first_hazardous_segment():
    holds = hold_points(TOPO, {"VD-OLD-03": 2}, HP)
    assert holds == {"VD-OLD": "VD-TRUNK-13"}        # old track only; Himkoti walkers keep going


def test_hold_on_trunk_and_at_gate():
    assert set(hold_points(TOPO, {"VD-TRUNK-10": 3}, HP).values()) == {"VD-TRUNK-07"}
    assert set(hold_points(TOPO, {"VD-TRUNK-01": 2}, HP).values()) == {"VD-TRUNK-01"}


def test_queue_grows_while_held_is_capped_and_drains_after():
    times = [T0 + timedelta(hours=k) for k in range(5)]
    held = {"VD-OLD": "VD-TRUNK-13"}
    holds = [held, held, held, {}, {}]
    arrivals = {("VD-OLD", "VD-TRUNK-13"): [100, 100, 100, 100, 100]}
    occ = {("VD-TRUNK-13", ts): 10 for ts in times}
    notes = apply_holding(occ, times, holds, arrivals, HP)
    assert [occ[("VD-TRUNK-13", ts)] for ts in times] == [110, 210, 260, 160, 60]   # cap 250, release 100/h
    assert notes[("VD-TRUNK-13", times[0])]["held_routes"] == ["VD-OLD"]
    assert notes[("VD-TRUNK-13", times[3])]["releasing"] is True
    assert ("VD-TRUNK-13", times[4]) in notes and notes[("VD-TRUNK-13", times[4])]["held_persons"] == 50
