from datetime import datetime, timedelta

import pytest

from app.crowd.simulator import IST, SimParams, crowd_rows, density_level, hourly_weights, simulate
from app.risk.config import segments_geojson, thresholds
from app.risk.topology import Topology, from_geojson

BANDS = thresholds()["crowd"]["bands_ppm2"]


@pytest.fixture(scope="module")
def topo() -> Topology:
    return Topology(from_geojson(segments_geojson()))


@pytest.mark.parametrize("density, level", [
    (0.0, 0), (1.99, 0), (2.0, 1), (3.99, 1), (4.0, 2), (5.99, 2), (6.0, 3), (12.0, 3)])
def test_density_bands(density, level):
    assert density_level(density, BANDS) == level


def test_bands_come_from_config():
    assert BANDS == [2.0, 4.0, 6.0]


def test_topology_branches(topo):
    assert topo.parent == {"VD-TRUNK": None, "VD-OLD": "VD-TRUNK", "VD-HIMKOTI": "VD-TRUNK"}
    assert topo.leaf_routes() == ["VD-HIMKOTI", "VD-OLD"]
    assert topo.landmark_below("VD-OLD-01").id == "VD-TRUNK-13"


def test_daytime_peak():
    w = hourly_weights(SimParams())
    assert max(range(24), key=w.__getitem__) == 9
    assert w[9] > 5 * w[2]


def test_arrivals_never_exceed_cap(topo):
    with pytest.raises(ValueError):
        simulate(topo, datetime(2025, 8, 26, tzinfo=IST), datetime(2025, 8, 26, 1, tzinfo=IST),
                 SimParams(daily_arrivals=50_001))


@pytest.fixture(scope="module")
def day(topo):
    start = datetime(2025, 8, 26, tzinfo=IST)
    return start, simulate(topo, start, start + timedelta(hours=23))


def test_deterministic_for_seed(topo, day):
    start, occ = day
    again = simulate(topo, start, start + timedelta(hours=23))
    assert again == occ
    other = simulate(topo, start, start + timedelta(hours=23), SimParams(seed=7))
    assert other != occ


def test_hourly_snapshots_for_every_segment(topo, day):
    start, occ = day
    assert len(occ) == 24 * len(topo.by_id)
    assert all(ts.minute == 0 for _, ts in occ)


def test_people_on_trail_bounded_by_two_days_of_arrivals(day):
    _, occ = day
    by_hour: dict[datetime, int] = {}
    for (_, ts), n in occ.items():
        by_hour[ts] = by_hour.get(ts, 0) + n
    assert 0 < max(by_hour.values()) < 2 * SimParams().daily_cap
    at = {ts.hour: n for ts, n in by_hour.items()}
    assert at[12] > at[4]  # daytime peak is visible on the trail


def test_rows_are_simulated_and_density_matches_area(topo, day):
    _, occ = day
    rows = crowd_rows(topo, occ, "replay", BANDS)
    assert all(r["simulated"] is True and r["mode"] == "replay" for r in rows)
    r = next(r for r in rows if r["segment_id"] == "VD-OLD-01" and r["persons"] > 0)
    seg = topo.by_id["VD-OLD-01"]
    assert r["density_ppm2"] == pytest.approx(r["persons"] / (seg.length_m * seg.width_m), abs=1e-4)
    assert r["level"] == density_level(r["density_ppm2"], BANDS)
