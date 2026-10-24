"""Engine scoring without a DB: hourly grid, rolling sums, per-segment carry of hysteresis."""
from datetime import datetime

from app.hazard.engine import HOUR, IST, Segment, score_point, score_segment, to_series
from app.hazard.rules import GREEN, R3_H, R24_H, YELLOW

T0 = datetime(2025, 8, 10, tzinfo=IST)


def test_to_series_fills_gaps():
    s = to_series([(T0, 1.0), (T0 + 3 * HOUR, 2.0)])
    assert s.precip_mm == [1.0, 0.0, 0.0, 2.0]
    assert s.present == [True, False, False, True]
    assert s.times[-1] == T0 + 3 * HOUR


def test_rolling_sums_and_coverage(t):
    s = to_series([(T0 + i * HOUR, 1.0) for i in range(30)])
    scores = score_point(s, t)
    sums, notes = scores[29]
    assert sums[R3_H] == 3.0 and sums[R24_H] == 24.0
    assert notes["r15d_hours_available"] == 30
    assert "missing_hours_15d" not in notes


def test_missing_hours_reported(t):
    _, notes = score_point(to_series([(T0, 1.0), (T0 + 2 * HOUR, 1.0)]), t)[-1]
    assert notes["missing_hours_15d"] == 1


def test_segment_carries_hysteresis(t):
    # Enough rain in one hour block for YELLOW, then dry: level holds one hour, then drops.
    wet = t.daily_watch_mm
    rows = [(T0, wet)] + [(T0 + i * HOUR, 0.0) for i in range(1, 27)]
    seg = Segment("X-01", "katra", 10.0, None, False)
    levels = [lvl for lvl, _ in score_segment(seg, score_point(to_series(rows), t), t)]
    assert levels[0] == YELLOW
    assert levels[23] == YELLOW          # rain still inside the 24 h window
    assert levels[24] == YELLOW          # first hour below: held by hysteresis
    assert levels[25] == GREEN           # second hour below: drops
