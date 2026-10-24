import pytest

from app.risk.fuse import fuse, fuse_levels


@pytest.mark.parametrize("hazard, crowd, risk", [
    (0, 0, 0), (1, 0, 1), (0, 1, 1), (0, 3, 3), (1, 1, 1), (1, 3, 3),
    (2, 0, 2), (2, 1, 3), (2, 3, 3), (3, 0, 3), (3, 1, 3), (3, 3, 3)])
def test_fusion_table(hazard, crowd, risk):
    assert fuse_levels(hazard, crowd)[0] == risk


def test_all_combinations_stay_in_range_and_never_below_max():
    for h in range(4):
        for c in range(4):
            r, _ = fuse_levels(h, c)
            assert max(h, c) <= r <= 3


def test_drivers_are_merged():
    out = fuse(2, {"rule": "ORANGE_R24", "r24_mm": 63.9}, {"persons": 1240, "density_ppm2": 2.1, "level": 1,
                                                          "simulated": True})
    assert out["risk_level"] == 3
    assert out["drivers"]["rule"] == "HAZARD_PLUS_CROWD"
    assert out["drivers"]["hazard"] == {"level": 2, "rule": "ORANGE_R24", "r24_mm": 63.9}
    assert out["drivers"]["crowd"]["persons"] == 1240 and out["drivers"]["crowd"]["simulated"] is True


def test_missing_crowd_counts_as_green():
    out = fuse(1, {"rule": "YELLOW_R24"}, None)
    assert (out["crowd_level"], out["risk_level"], out["drivers"]["rule"]) == (0, 1, "MAX")
    assert out["drivers"]["crowd"]["missing"] is True
