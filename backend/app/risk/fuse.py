"""Risk fusion of hazard and crowd levels (pure, no DB). Rule: docs/PLAN.md "Risk fusion"."""
from typing import Any

from app.risk.config import thresholds

LEVEL_NAMES = ("GREEN", "YELLOW", "ORANGE", "RED")


def fuse_levels(hazard: int, crowd: int) -> tuple[int, str]:
    """risk = max(hazard, crowd); if hazard >= 2 and crowd >= 1, risk = min(3, hazard + 1)."""
    cfg = thresholds()["risk"]
    if hazard >= cfg["fusion_hazard_min"] and crowd >= cfg["fusion_crowd_min"]:
        return min(3, hazard + 1), "HAZARD_PLUS_CROWD"
    return max(hazard, crowd), "MAX"


def fuse(hazard_level: int, hazard_drivers: dict[str, Any], crowd: dict[str, Any] | None) -> dict[str, Any]:
    """One `segment_risk` payload. `crowd` is a segment_crowd row or None (no crowd data -> level 0)."""
    crowd_level = crowd["level"] if crowd else 0
    risk_level, rule = fuse_levels(hazard_level, crowd_level)
    drivers = {
        "rule": rule,
        "hazard": {"level": hazard_level, **hazard_drivers},
        "crowd": ({"level": crowd_level, "persons": crowd["persons"], "density_ppm2": crowd["density_ppm2"],
                   "simulated": crowd.get("simulated", True),
                   **({"scenario": crowd["scenario"]} if crowd.get("scenario") else {})} if crowd else {"level": 0, "missing": True}),
    }
    return {"hazard_level": hazard_level, "crowd_level": crowd_level, "risk_level": risk_level, "drivers": drivers}
