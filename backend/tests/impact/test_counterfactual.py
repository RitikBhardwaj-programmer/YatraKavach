"""Impact counterfactual, pure logic (no DB). All person counts are SIMULATED."""
from datetime import datetime, timedelta

import pytest
from app.crowd.service import holding_params
from app.crowd.simulator import IST, SimParams, simulate
from app.impact.counterfactual import (
    Decision,
    counterfactual,
    persons_on_target,
    snapshot_hour,
    warning_start,
)
from app.impact.service import official_closure_ts
from app.risk.config import segments_geojson
from app.risk.topology import Topology, from_geojson

EVENT = datetime.fromisoformat("2025-08-26T14:40:00+05:30")
SNAP = datetime.fromisoformat("2025-08-26T14:00:00+05:30")
TARGET = ["VD-OLD-01"]


@pytest.fixture(scope="module")
def topo() -> Topology:
    return Topology(from_geojson(segments_geojson()))


def _h(day: int, hour: int) -> datetime:
    return datetime(2025, 8, day, hour, tzinfo=IST)


def test_snapshot_is_last_whole_ist_hour_at_or_before_event():
    assert snapshot_hour(EVENT) == SNAP
    assert snapshot_hour(SNAP) == SNAP
    assert snapshot_hour(EVENT.astimezone(datetime.now().astimezone().tzinfo)).utcoffset() == timedelta(hours=5.5)


def test_warning_start_ignores_a_warning_that_cleared_before():
    levels = [(_h(14, 10), 2), (_h(14, 11), 2), (_h(15, 16), 1), (_h(25, 15), 2), (_h(26, 5), 3), (_h(26, 14), 3),
              (_h(26, 15), 1)]
    assert warning_start(levels, 2, SNAP) == _h(25, 15)
    assert warning_start(levels, 3, SNAP) == _h(26, 5)
    assert warning_start(levels[::-1], 3, SNAP) == _h(26, 5)          # order of input does not matter
    assert warning_start(levels, 3, _h(26, 4)) is None                 # not RED yet
    assert warning_start(levels, 2, _h(27, 0)) is None                 # cleared at 15:00 (hour after the snapshot)


def test_official_closure_is_the_replay_timeline_event():
    assert official_closure_ts() == _h(26, 12)


def test_round_trip_is_shorter_than_a_day(topo):
    """`persons_on_target` simulates the snapshot hour only; simulate() adds the previous day, which covers
    every pilgrim still on the trail at the snapshot because the slowest round trip is shorter than a day."""
    p = SimParams()
    longest = max(sum(s.length_m for s in topo.ascent_path(r)) for r in topo.leaf_routes())
    assert 2 * longest / (min(p.speed_kmh) * 1000) + max(p.dwell_h) < 24


def test_snapshot_window_matches_a_longer_window(topo):
    stop = {"VD-OLD": ("VD-TRUNK-13", _h(26, 5))}
    longer = simulate(topo, SNAP - timedelta(hours=48), SNAP, stop_ascent=stop)
    assert persons_on_target(topo, TARGET, SNAP, SimParams(), stop) == longer[("VD-OLD-01", SNAP)]


@pytest.fixture(scope="module")
def result(topo):
    hp = holding_params()
    gate_orange = {"VD-TRUNK-01": 2, "VD-OLD-01": 2}
    decisions = [Decision("no_action", "No action", None), Decision("first_orange", "ORANGE", _h(25, 15)),
                 Decision("first_red", "RED", _h(26, 5)), Decision("official_closure", "~12:00", _h(26, 12)),
                 Decision("too_late", "after the snapshot", _h(26, 15)), Decision("missing", "never", None),
                 Decision("nothing_to_hold", "no hazard at that hour", _h(26, 9))]
    hazard_at = {_h(25, 15): gate_orange, _h(26, 5): gate_orange, _h(26, 12): {"VD-OLD-01": 3}}
    return counterfactual(topo, TARGET, EVENT, decisions, hazard_at, hp, SimParams())


def test_contract_shape(result):
    assert set(result) == {"simulated", "target_segments", "event_ts", "snapshot_ts", "scenarios"}
    assert result["simulated"] is True and result["target_segments"] == TARGET
    assert result["event_ts"] == EVENT and result["snapshot_ts"] == SNAP
    assert [s["key"] for s in result["scenarios"]] == ["no_action", "first_orange", "first_red", "official_closure"]
    for s in result["scenarios"]:
        assert set(s) == {"key", "label", "decision_ts", "hold_points", "persons_on_target"}
    no_action = result["scenarios"][0]
    assert no_action["decision_ts"] is None and no_action["hold_points"] is None


def test_hold_points_follow_the_hazard_of_the_decision_hour(result):
    by_key = {s["key"]: s for s in result["scenarios"]}
    assert by_key["first_red"]["hold_points"] == {"VD-HIMKOTI": "VD-TRUNK-01", "VD-OLD": "VD-TRUNK-01"}
    assert by_key["official_closure"]["hold_points"] == {"VD-OLD": "VD-TRUNK-13"}   # old track only


def test_earlier_decision_never_more_on_target(result):
    n = {s["key"]: s["persons_on_target"] for s in result["scenarios"]}
    assert n["no_action"] > 0
    assert n["first_orange"] <= n["first_red"] <= n["no_action"]
    assert n["official_closure"] <= n["no_action"]


def test_no_action_equals_plain_simulation(topo, result):
    assert result["scenarios"][0]["persons_on_target"] == simulate(topo, SNAP, SNAP)[("VD-OLD-01", SNAP)]
