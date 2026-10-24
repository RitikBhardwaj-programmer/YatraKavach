"""Hazard rules (docs/PLAN.md "Rules"). Pure functions, no DB. Values come from config/thresholds.yaml."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

GREEN, YELLOW, ORANGE, RED = 0, 1, 2, 3
LEVEL_NAMES = {GREEN: "GREEN", YELLOW: "YELLOW", ORANGE: "ORANGE", RED: "RED"}
# Rain windows by definition (docs/PLAN.md): R3, R24, R15d, in hours.
R3_H, R24_H, R15D_H = 3, 24, 15 * 24

CONFIG = Path(__file__).resolve().parents[3] / "config" / "thresholds.yaml"
if not CONFIG.exists():
    CONFIG = Path("/app/config/thresholds.yaml")


@dataclass(frozen=True)
class HazardThresholds:
    version: str
    daily_watch_mm: float
    antecedent_15d_mm: float
    orange_daily_factor: float
    orange_r24_mm: float
    red_r24_mm: float
    id_a: float
    id_b: float
    id_durations_h: tuple[int, ...]
    steep_slope_deg: float
    high_susceptibility_class: int
    hysteresis_updates: int
    step_up_rules_excluded: tuple[str, ...] = ()

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> "HazardThresholds":
        h = cfg["hazard"]
        return cls(
            version=str(cfg["version"]),
            daily_watch_mm=float(h["daily_watch_mm"]),
            antecedent_15d_mm=float(h["antecedent_15d_mm"]),
            orange_daily_factor=float(h["orange_daily_factor"]),
            orange_r24_mm=float(h["orange_r24_mm"]),
            red_r24_mm=float(h["red_r24_mm"]),
            id_a=float(h["id_curve"]["a"]),
            id_b=float(h["id_curve"]["b"]),
            id_durations_h=tuple(int(d) for d in h["id_curve"]["durations_h"]),
            steep_slope_deg=float(h["steep_slope_deg"]),
            high_susceptibility_class=int(h["high_susceptibility_class"]),
            hysteresis_updates=int(h["hysteresis_updates"]),
            step_up_rules_excluded=tuple(h.get("step_up_rules_excluded", ())),
        )

    @property
    def windows_h(self) -> tuple[int, ...]:
        """Every rain window (hours) the rules read."""
        return tuple(sorted({R3_H, R24_H, R15D_H, *self.id_durations_h}))


def load_thresholds(path: Path = CONFIG) -> HazardThresholds:
    with open(path, encoding="utf-8") as f:
        return HazardThresholds.from_config(yaml.safe_load(f))


def id_threshold_mm_h(t: HazardThresholds, duration_h: int) -> float:
    """I-D curve: mean intensity (mm/h) over D hours that triggers RED. I = a * D^b."""
    return t.id_a * duration_h ** t.id_b


def _r(x: float) -> float:
    return round(x, 2)


def rain_level(sums_mm: dict[int, float], t: HazardThresholds) -> tuple[int, dict[str, Any]]:
    """Rain-only level from rain sums keyed by window length in hours (see HazardThresholds.windows_h).

    Returns (level, drivers). Rules are checked from RED down; the first match wins.
    """
    r24, r15d = sums_mm[R24_H], sums_mm[R15D_H]
    base = {"r3_mm": _r(sums_mm[R3_H]), "r24_mm": _r(r24), "r15d_mm": _r(r15d)}

    if r24 >= t.red_r24_mm:
        return RED, {**base, "rule": "RED_R24", "r24_threshold": t.red_r24_mm, "ratio": _r(r24 / t.red_r24_mm)}
    for d in t.id_durations_h:
        intensity, limit = sums_mm[d] / d, id_threshold_mm_h(t, d)
        if intensity >= limit:
            return RED, {**base, "rule": f"RED_ID_{d}H", "duration_h": d, "intensity_mm_h": _r(intensity),
                         "id_threshold_mm_h": _r(limit), "ratio": _r(intensity / limit)}

    orange_daily = t.orange_daily_factor * t.daily_watch_mm
    if r24 >= orange_daily and r15d >= t.antecedent_15d_mm:
        return ORANGE, {**base, "rule": "ORANGE_R24_ANTECEDENT", "r24_threshold": _r(orange_daily),
                        "r15d_threshold": t.antecedent_15d_mm, "ratio": _r(r24 / orange_daily)}
    if r24 >= t.orange_r24_mm:
        return ORANGE, {**base, "rule": "ORANGE_R24", "r24_threshold": t.orange_r24_mm,
                        "ratio": _r(r24 / t.orange_r24_mm)}

    if r24 >= t.daily_watch_mm:
        return YELLOW, {**base, "rule": "YELLOW_R24", "r24_threshold": t.daily_watch_mm,
                        "ratio": _r(r24 / t.daily_watch_mm)}
    if r15d >= t.antecedent_15d_mm:
        return YELLOW, {**base, "rule": "YELLOW_R15D", "r15d_threshold": t.antecedent_15d_mm,
                        "ratio": _r(r15d / t.antecedent_15d_mm)}
    return GREEN, {**base, "rule": "GREEN", "r24_threshold": t.daily_watch_mm, "ratio": _r(r24 / t.daily_watch_mm)}


def step_up_reasons(slope_deg: float | None, susceptibility: int | None, past_slide: bool,
                    t: HazardThresholds) -> list[str]:
    """Segment factors that raise a level by one step."""
    reasons = []
    if slope_deg is not None and slope_deg >= t.steep_slope_deg:
        reasons.append("STEEP_SLOPE")
    if susceptibility is not None and susceptibility >= t.high_susceptibility_class:
        reasons.append("HIGH_SUSCEPTIBILITY")
    if past_slide:
        reasons.append("PAST_SLIDE")
    return reasons


def apply_step_up(level: int, reasons: list[str]) -> int:
    """Raise a level >= YELLOW by one step (max RED) when any segment factor applies."""
    return min(RED, level + 1) if level >= YELLOW and reasons else level


def step_up_allowed(rule: str, t: HazardThresholds) -> bool:
    """Segment factors do not raise rules listed in step_up_rules_excluded (e.g. antecedent rain alone)."""
    return rule not in t.step_up_rules_excluded


@dataclass(frozen=True)
class HysteresisState:
    level: int = GREEN
    below: tuple[int, ...] = ()     # raw levels of the consecutive updates below `level`


def apply_hysteresis(state: HysteresisState, new_level: int, updates: int) -> HysteresisState:
    """A level drops only after `updates` consecutive updates below it, then to the highest of those levels."""
    if new_level >= state.level:
        return HysteresisState(new_level)
    below = state.below + (new_level,)
    if len(below) >= updates:
        return HysteresisState(max(below))
    return HysteresisState(state.level, below)


def segment_level(sums_mm: dict[int, float], state: HysteresisState, slope_deg: float | None,
                  susceptibility: int | None, past_slide: bool,
                  t: HazardThresholds) -> tuple[HysteresisState, dict[str, Any]]:
    """One hourly update for one segment: rain rule, step-up, hysteresis. Returns (new state, drivers)."""
    rain, drivers = rain_level(sums_mm, t)
    reasons = step_up_reasons(slope_deg, susceptibility, past_slide, t) if step_up_allowed(drivers["rule"], t) else []
    raw = apply_step_up(rain, reasons)
    new = apply_hysteresis(state, raw, t.hysteresis_updates)

    drivers = {**drivers, "rain_level": rain, "slope_deg": slope_deg}
    if reasons and rain >= YELLOW:   # recorded even when capped at RED
        drivers["step_up"] = reasons
    if new.level != raw:
        drivers.update(rule="HYSTERESIS_HOLD", raw_rule=drivers["rule"], raw_level=raw,
                       updates_below=len(new.below), updates_needed=t.hysteresis_updates)
    drivers["level_name"] = LEVEL_NAMES[new.level]
    return new, drivers
