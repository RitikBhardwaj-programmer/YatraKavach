from datetime import datetime, timedelta

from app.alerts import templates
from app.alerts.proposals import OpenAlert, propose
from app.risk.config import segments_geojson
from app.risk.topology import Topology, from_geojson

TOPO = Topology(from_geojson(segments_geojson()))
T0 = datetime.fromisoformat("2025-08-26T10:00:00+05:30")
H = timedelta(hours=1)


def risk(levels: dict[str, int]) -> dict[str, dict]:
    return {sid: {"risk_level": levels.get(sid, 0), "drivers": {}} for sid in TOPO.by_id}


def test_contiguous_segments_form_one_alert_per_route_and_level():
    out, _ = propose(TOPO, {T0: risk({"VD-OLD-01": 2, "VD-OLD-02": 2, "VD-OLD-04": 2, "VD-HIMKOTI-01": 3})}, [], 2)
    assert sorted(p.segment_ids for p in out) == [["VD-HIMKOTI-01"], ["VD-OLD-01", "VD-OLD-02"], ["VD-OLD-04"]]


def test_below_proposal_level_gives_nothing():
    assert propose(TOPO, {T0: risk({"VD-OLD-01": 1})}, [], 2) == ([], [])


def test_covering_alert_blocks_new_proposal_at_same_level():
    stored = [OpenAlert(1, ["VD-OLD-01"], 2, T0 - H)]
    assert propose(TOPO, {T0: risk({"VD-OLD-01": 2})}, stored, 2) == ([], [])


def test_alert_after_this_hour_does_not_cover_it():
    stored = [OpenAlert(1, ["VD-OLD-01"], 2, T0 + H)]
    out, _ = propose(TOPO, {T0: risk({"VD-OLD-01": 2})}, stored, 2)
    assert [p.segment_ids for p in out] == [["VD-OLD-01"]]


def test_no_duplicate_over_hours_and_red_upgrade_references_orange():
    timeline = {T0: risk({"VD-OLD-01": 2}), T0 + H: risk({"VD-OLD-01": 2}), T0 + 2 * H: risk({"VD-OLD-01": 3})}
    out, cleared = propose(TOPO, timeline, [], 2)
    assert [(p.level, p.trigger_ts) for p in out] == [(2, T0), (3, T0 + 2 * H)]
    assert out[1].references is out[0].open and cleared == []
    out[0].open.id = 11  # the writer sets ids as it inserts
    assert out[1].references_alert_id == 11


def test_condition_cleared_ends_coverage_and_allows_new_proposal():
    timeline = {T0: risk({"VD-OLD-01": 2}), T0 + H: risk({"VD-OLD-01": 1}), T0 + 2 * H: risk({"VD-OLD-01": 2})}
    out, cleared = propose(TOPO, timeline, [], 2)
    assert [p.trigger_ts for p in out] == [T0, T0 + 2 * H]
    assert cleared == [out[0].open] and out[0].open.cleared_at == T0 + H
    assert out[1].references is None


def test_red_proposal_clears_when_risk_drops_to_orange_then_orange_is_proposed():
    timeline = {T0: risk({"VD-OLD-01": 3}), T0 + H: risk({"VD-OLD-01": 2}), T0 + 2 * H: risk({"VD-OLD-01": 3})}
    out, cleared = propose(TOPO, timeline, [], 2)
    assert [(p.level, p.trigger_ts) for p in out] == [(3, T0), (2, T0 + H), (3, T0 + 2 * H)]
    assert cleared == [out[0].open]
    assert out[2].references is out[1].open


def test_rerun_over_stored_alerts_is_idempotent():
    timeline = {T0: risk({"VD-OLD-01": 2}), T0 + H: risk({"VD-OLD-01": 0}), T0 + 2 * H: risk({"VD-OLD-01": 3})}
    first, _ = propose(TOPO, timeline, [], 2)
    stored = [OpenAlert(i, p.segment_ids, p.level, p.trigger_ts) for i, p in enumerate(first, 1)]
    again, cleared = propose(TOPO, timeline, stored, 2)
    assert again == [] and [a.id for a in cleared] == [1]


def test_action_text_from_plan_templates():
    out, _ = propose(TOPO, {T0: risk({"VD-OLD-01": 2, "VD-TRUNK-10": 3})}, [], 2)
    by_level = {p.level: p.proposed_action for p in out}
    assert by_level[2] == "Hold pilgrims at Adhkuwari (track junction); stop ascent beyond VD-OLD-01"
    assert by_level[3] == "Clear segment VD-TRUNK-10 (near Banganga); move pilgrims to Banganga"


def test_context_uses_landmark_inside_run_and_root_fallback():
    ctx = templates.context(TOPO, ["VD-TRUNK-01", "VD-TRUNK-02"])
    assert ctx["place"] == ctx["nearby"] == "Katra (Banganga Road start)"
    assert ctx["upstream"] == "Katra (Banganga Road start)"
    assert ctx["segments"] == "VD-TRUNK-01 to VD-TRUNK-02"
