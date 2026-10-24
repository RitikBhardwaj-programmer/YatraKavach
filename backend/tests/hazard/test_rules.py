"""Hazard rule tests without a DB. Rain sums are test inputs; thresholds come from config/thresholds.yaml."""
from dataclasses import replace

import pytest

from app.hazard.rules import (GREEN, ORANGE, R3_H, R15D_H, R24_H, RED, YELLOW, HysteresisState, apply_hysteresis,
                              apply_step_up, id_threshold_mm_h, rain_level, segment_level, step_up_reasons)

EPS = 0.01


def sums(t, r24=0.0, r15d=None, short=None):
    """Rain sums for every window. Short windows (< 24 h) get `short` mm or a share well below the I-D curve."""
    out = {h: (short if short is not None else 0.0) for h in t.windows_h}
    out[R24_H] = r24
    out[R15D_H] = r24 if r15d is None else r15d
    return out


def test_green_below_everything(t):
    assert rain_level(sums(t, r24=t.daily_watch_mm - EPS), t)[0] == GREEN


@pytest.mark.parametrize("delta, level", [(-EPS, GREEN), (0.0, YELLOW), (EPS, YELLOW)])
def test_yellow_r24_edge(t, delta, level):
    lvl, drivers = rain_level(sums(t, r24=t.daily_watch_mm + delta, r15d=0.0), t)
    assert lvl == level
    if level == YELLOW:
        assert drivers["rule"] == "YELLOW_R24" and drivers["r24_threshold"] == t.daily_watch_mm


@pytest.mark.parametrize("delta, level", [(-EPS, GREEN), (0.0, YELLOW)])
def test_yellow_r15d_edge(t, delta, level):
    lvl, drivers = rain_level(sums(t, r24=0.0, r15d=t.antecedent_15d_mm + delta), t)
    assert lvl == level
    if level == YELLOW:
        assert drivers["rule"] == "YELLOW_R15D"


def test_orange_needs_antecedent(t):
    r24 = t.orange_daily_factor * t.daily_watch_mm
    assert rain_level(sums(t, r24=r24, r15d=t.antecedent_15d_mm), t)[1]["rule"] == "ORANGE_R24_ANTECEDENT"
    # r15d must be >= r24, so without antecedent the 2x daily value alone is YELLOW
    lvl, drivers = rain_level(sums(t, r24=r24 - EPS, r15d=t.antecedent_15d_mm), t)
    assert (lvl, drivers["rule"]) == (YELLOW, "YELLOW_R24")


def test_orange_r24_rule_without_antecedent(t):
    # Antecedent threshold set above the daily value isolates ORANGE_R24 (R15d >= R24 always)
    t2 = replace(t, antecedent_15d_mm=t.orange_r24_mm * 2)
    assert rain_level(sums(t2, r24=t.orange_r24_mm - EPS), t2)[0] == YELLOW
    lvl, drivers = rain_level(sums(t2, r24=t.orange_r24_mm), t2)
    assert (lvl, drivers["rule"], drivers["ratio"]) == (ORANGE, "ORANGE_R24", 1.0)


@pytest.mark.parametrize("delta, level", [(-EPS, ORANGE), (0.0, RED)])
def test_red_r24_edge(t, delta, level):
    # Spread evenly over 24 h so the I-D curve stays below its own limit except at D = 24
    r24 = t.red_r24_mm + delta
    s = sums(t, r24=r24)
    for d in t.windows_h:
        if d < R24_H:
            s[d] = r24 * d / R24_H
    lvl, drivers = rain_level(s, t)
    assert lvl == level
    if level == RED:
        assert drivers["rule"] == "RED_R24"


def test_id_curve_values(t):
    assert id_threshold_mm_h(t, 1) == pytest.approx(t.id_a)
    assert id_threshold_mm_h(t, 24) == pytest.approx(t.id_a * 24 ** t.id_b)
    limits = [id_threshold_mm_h(t, d) for d in t.id_durations_h]
    assert limits == sorted(limits, reverse=True)   # longer storms trigger at lower mean intensity


@pytest.mark.parametrize("d", [1, 3, 6, 12])
def test_id_curve_edge_per_duration(t, d):
    assert d in t.id_durations_h
    limit_mm = id_threshold_mm_h(t, d) * d * (1 + 1e-9)   # on the curve, guarded against float rounding
    s = sums(t, r24=limit_mm)        # all rain fell inside the D-hour window
    for h in t.windows_h:
        if h < R24_H:
            s[h] = limit_mm if h >= d else limit_mm * h / d
    lvl, drivers = rain_level(s, t)
    assert lvl == RED and drivers["rule"].startswith("RED_ID_")
    assert drivers["intensity_mm_h"] >= drivers["id_threshold_mm_h"]

    s_below = {h: v * (1 - 1e-3) for h, v in s.items()}
    assert rain_level(s_below, t)[0] < RED


def test_drivers_explain_numbers(t):
    lvl, drivers = rain_level(sums(t, r24=63.9, r15d=63.9, short=1.0), t)
    assert lvl == ORANGE
    assert {"r3_mm", "r24_mm", "r15d_mm", "rule", "ratio", "r24_threshold"} <= drivers.keys()
    assert drivers["r24_mm"] == 63.9 and drivers["r3_mm"] == 1.0
    assert R3_H in t.windows_h


@pytest.mark.parametrize("slope, susc, slide, reasons", [
    (None, None, False, []),
    (39.9, 2, False, []),
    (40.0, None, False, ["STEEP_SLOPE"]),
    (10.0, 3, False, ["HIGH_SUSCEPTIBILITY"]),
    (10.0, None, True, ["PAST_SLIDE"]),
])
def test_step_up_reasons(t, slope, susc, slide, reasons):
    assert step_up_reasons(slope, susc, slide, t) == reasons


@pytest.mark.parametrize("level, expected", [(GREEN, GREEN), (YELLOW, ORANGE), (ORANGE, RED), (RED, RED)])
def test_step_up_only_from_yellow_and_capped(level, expected):
    assert apply_step_up(level, ["PAST_SLIDE"]) == expected
    assert apply_step_up(level, []) == level


def test_hysteresis_rise_is_immediate():
    assert apply_hysteresis(HysteresisState(GREEN), RED, 2) == HysteresisState(RED)


def test_hysteresis_drop_after_two_updates():
    s = HysteresisState(RED)
    s = apply_hysteresis(s, GREEN, 2)
    assert s.level == RED                       # 1 update below: hold
    s = apply_hysteresis(s, YELLOW, 2)
    assert s == HysteresisState(YELLOW)          # 2 updates below: drop to the highest of them


def test_hysteresis_interrupted_drop_resets():
    s = apply_hysteresis(HysteresisState(ORANGE), YELLOW, 2)
    s = apply_hysteresis(s, ORANGE, 2)           # back at the held level: counter resets
    assert s == HysteresisState(ORANGE)
    s = apply_hysteresis(s, GREEN, 2)
    assert s.level == ORANGE


def test_segment_level_reports_hold_and_step_up(t):
    s, d = segment_level(sums(t, r24=t.daily_watch_mm, r15d=0.0), HysteresisState(), 45.0, None, False, t)
    assert s.level == ORANGE and d["step_up"] == ["STEEP_SLOPE"] and d["rain_level"] == YELLOW
    assert d["level_name"] == "ORANGE"
    s, d = segment_level(sums(t), s, 45.0, None, False, t)
    assert s.level == ORANGE and d["rule"] == "HYSTERESIS_HOLD" and d["raw_level"] == GREEN
    assert d["raw_rule"] == "GREEN" and d["updates_below"] == 1
    s, d = segment_level(sums(t), s, 45.0, None, False, t)
    assert s.level == GREEN and d["rule"] == "GREEN"
