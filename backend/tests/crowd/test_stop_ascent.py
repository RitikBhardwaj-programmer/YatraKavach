"""SIMULATED `simulate(..., stop_ascent=...)` for the impact counterfactual (pure, no DB)."""
from datetime import datetime, timedelta

import pytest
from app.crowd.simulator import SimParams, simulate
from app.risk.config import segments_geojson
from app.risk.topology import Segment, Topology, from_geojson

D = 0.0045  # about 500 m of latitude per segment
T0 = datetime.fromisoformat("2025-08-26T06:00:00+05:30")
SMALL = SimParams(daily_arrivals=300, speed_kmh=(1.0, 2.0), dwell_h=(0.5, 1.0))


def _seg(sid: str, route: str, seq: int, a: tuple[int, int], b: tuple[int, int]) -> Segment:
    return Segment(sid, route, seq, 500.0, 4.0, "trail", None, (75 + a[0] * D, 33 + a[1] * D),
                   (75 + b[0] * D, 33 + b[1] * D))


@pytest.fixture(scope="module")
def small() -> Topology:
    """Trunk T-1, T-2; branches A-1, A-2 (route A-OLD) and B-1 (route B) from the trunk end."""
    return Topology([_seg("T-1", "T", 1, (0, 0), (0, 1)), _seg("T-2", "T", 2, (0, 1), (0, 2)),
                     _seg("A-1", "A-OLD", 1, (0, 2), (1, 3)), _seg("A-2", "A-OLD", 2, (1, 3), (2, 4)),
                     _seg("B-1", "B", 1, (0, 2), (-1, 3))])


@pytest.fixture(scope="module")
def topo() -> Topology:
    return Topology(from_geojson(segments_geojson()))


def _series(occ, sid, start, n):
    return [occ[(sid, start + timedelta(hours=k))] for k in range(n)]


# Output of simulate() on `small` before stop_ascent existed (origin/main 45a8a3e), same arguments.
OLD_OCCUPANCY = {"A-1": [5, 7, 5, 16, 12, 8], "A-2": [3, 3, 6, 8, 7, 13], "B-1": [6, 3, 8, 10, 17, 11],
                 "T-1": [8, 9, 8, 17, 21, 22], "T-2": [4, 5, 20, 11, 20, 22]}
OLD_ARRIVALS = {("A-OLD", "A-1"): [11, 10, 24, 14, 16, 17], ("B", "T-2"): [6, 14, 11, 17, 15, 10]}


def test_no_stop_ascent_gives_the_old_output(small):
    assert small.parent == {"T": None, "A-OLD": "T", "B": "T"}
    for stop in (None, {}):
        arrivals = {k: [] for k in OLD_ARRIVALS}
        occ = simulate(small, T0, T0 + timedelta(hours=5), SMALL, arrivals, stop_ascent=stop)
        assert {sid: _series(occ, sid, T0, 6) for sid in small.by_id} == OLD_OCCUPANCY
        assert arrivals == OLD_ARRIVALS


def test_unknown_hold_segment_is_rejected(small):
    with pytest.raises(ValueError, match="not on the ascent path"):
        simulate(small, T0, T0, SMALL, stop_ascent={"B": ("A-1", T0)})


def test_nothing_changes_before_the_hold_time(small):
    """Before `from_ts` no pilgrim has been stopped yet, so every segment matches no action."""
    end = T0 + timedelta(hours=5)
    base = simulate(small, T0, end, SMALL)
    held = simulate(small, T0, end, SMALL, stop_ascent={"A-OLD": ("T-2", T0 + timedelta(hours=3))})
    early = {k: v for k, v in base.items() if k[1] <= T0 + timedelta(hours=3)}
    assert early == {k: held[k] for k in early}
    assert held != base


def test_held_pilgrims_appear_on_the_hold_segment(small):
    """Gate hold on both routes from T0: at the end, T-1 holds exactly everyone who entered since T0."""
    end = T0 + timedelta(hours=5)
    arrivals = {("A-OLD", "T-1"): [], ("B", "T-1"): []}
    occ = simulate(small, T0, end, SMALL, arrivals, stop_ascent={"A-OLD": ("T-1", T0), "B": ("T-1", T0)})
    entered = sum(sum(a[:5]) for a in arrivals.values())   # entries in hours T0 .. end-1
    assert entered > 0 and occ[("T-1", end)] == entered
    # everyone who entered before T0 has finished the round trip by `end` (max 2.5 km at 1 km/h + 1 h dwell)
    assert all(occ[(sid, end)] == 0 for sid in ("T-2", "A-1", "A-2", "B-1"))


def test_only_ascent_on_the_held_route_is_stopped(small):
    """Holding A-OLD at A-1 stops its ascent; pilgrims who went up B may still come down A-OLD (no descent stop)."""
    end = T0 + timedelta(hours=5)
    base = simulate(small, T0, end, SMALL)
    day_before = T0 - timedelta(days=1)
    one = simulate(small, T0, end, SMALL, stop_ascent={"A-OLD": ("A-1", day_before)})
    both = simulate(small, T0, end, SMALL, stop_ascent={"A-OLD": ("A-1", day_before), "B": ("B-1", day_before)})
    assert sum(_series(one, "A-2", T0, 6)) > 0          # descents of B pilgrims only
    assert _series(both, "A-2", T0, 6) == [0] * 6       # nobody reaches the top any more
    assert one[("A-1", end)] > base[("A-1", end)]       # held on A-1


@pytest.fixture(scope="module")
def slide():
    snap = datetime.fromisoformat("2025-08-26T14:00:00+05:30")
    return snap, lambda topo, stop: simulate(topo, snap, snap, stop_ascent=stop)[("VD-OLD-01", snap)]


def _gate(ts: datetime) -> dict[str, tuple[str, datetime]]:
    return {"VD-OLD": ("VD-TRUNK-01", ts), "VD-HIMKOTI": ("VD-TRUNK-01", ts)}


def test_earlier_hold_never_gives_more_on_target(topo, slide):
    snap, on_target = slide
    hours = [snap - timedelta(hours=h) for h in (24, 12, 9, 6, 3, 1, 0)]
    counts = [on_target(topo, _gate(ts)) for ts in hours]
    no_action = on_target(topo, None)
    assert counts == sorted(counts) and counts[-1] <= no_action
    assert counts[0] == 0 and no_action > 0
    adhkuwari = [on_target(topo, {"VD-OLD": ("VD-TRUNK-13", ts)}) for ts in hours]
    assert adhkuwari == sorted(adhkuwari) and adhkuwari[-1] <= no_action


def test_hold_above_target_changes_nothing_on_target(topo, slide):
    """Held at VD-OLD-02 from 12:00: they passed VD-OLD-01 normally and could not have come back down by 14:00."""
    snap, on_target = slide
    assert on_target(topo, {"VD-OLD": ("VD-OLD-02", snap - timedelta(hours=2))}) == on_target(topo, None)


def test_pilgrims_already_past_the_hold_keep_walking(topo, slide):
    """A gate hold at 12:00 cannot empty VD-OLD-01 at 14:00: the gate is >= 6.3 km below it (>= 2.1 h at 3 km/h)."""
    snap, on_target = slide
    assert on_target(topo, _gate(snap - timedelta(hours=2))) == on_target(topo, None)
