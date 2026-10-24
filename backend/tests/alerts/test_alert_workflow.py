from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from app.alerts import workflow as wf
from app.alerts.workflow import Alert, Officer, Rules, State, WorkflowError
from app.risk.config import thresholds

RULES = Rules.from_config(thresholds())
T0 = datetime.fromisoformat("2025-08-26T11:00:00+05:30")
OFF1, OFF2, SENIOR = Officer("off-1", "officer"), Officer("off-2", "officer"), Officer("sen-1", "senior")


def alert(level: int = 2, state: State = State.PROPOSED, **kw) -> Alert:
    a, _ = wf.propose(level, "Hold pilgrims at X; stop ascent beyond Y", T0, RULES)
    return replace(a, state=state, **kw)


ACTIONS = {
    "approve": lambda a: wf.approve(a, OFF1, T0, RULES),
    "reject": lambda a: wf.reject(a, OFF1, T0, "not needed"),
    "cancel": lambda a: wf.cancel(a, OFF1, T0, "rain stopped"),
    "ack": lambda a: wf.ack(a, OFF1, T0),
    "break_glass": lambda a: wf.break_glass(a, SENIOR, T0, RULES, "slope cracking, no time"),
    "edit": lambda a: wf.edit(a, OFF1, T0, "Hold pilgrims at Banganga"),
    "withdraw": lambda a: wf.withdraw(a, T0, "risk cleared"),
}
ALLOWED = {
    "approve": {State.PROPOSED, State.ESCALATED},
    "reject": {State.PROPOSED, State.ESCALATED},
    "cancel": {State.PROPOSED, State.ESCALATED, State.APPROVED, State.SENT, State.ACKED},
    "ack": {State.SENT},
    "break_glass": {State.PROPOSED, State.ESCALATED},
    "edit": {State.PROPOSED, State.ESCALATED},
    "withdraw": {State.PROPOSED, State.ESCALATED},
}
RESULT = {"approve": State.SENT, "reject": State.REJECTED, "cancel": State.CANCELLED, "ack": State.ACKED,
          "break_glass": State.SENT, "edit": None,
          "withdraw": State.CANCELLED}


@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("state", list(State))
def test_transition_matrix(action, state):
    a = alert(state=state)
    if state not in ALLOWED[action]:
        with pytest.raises(WorkflowError):
            ACTIONS[action](a)
        return
    new, events = ACTIONS[action](a)
    assert new.state == (RESULT[action] or state)
    assert events and events[0].from_state == state
    assert events[-1].to_state == new.state


def test_propose_needs_level_two():
    with pytest.raises(WorkflowError):
        wf.propose(1, "x", T0, RULES)
    a, events = wf.propose(2, "x", T0, RULES)
    assert (a.state, a.needs_approvals, events[0].action, events[0].from_state) == (State.PROPOSED, 1, "PROPOSE", None)


def test_orange_needs_one_approval_and_is_sent():
    new, events = wf.approve(alert(2), OFF1, T0, RULES)
    assert [e.action for e in events] == ["APPROVE", "SEND"]
    assert [e.to_state for e in events] == [State.APPROVED, State.SENT]
    assert new.sent_at == T0 and new.expires_at == T0 + RULES.expires_after
    assert events[1].detail == {"delivery": "SIMULATED"}


def test_red_needs_two_different_officers():
    a = alert(3)
    assert a.needs_approvals == 2
    a1, ev = wf.approve(a, OFF1, T0, RULES)
    assert a1.state == State.PROPOSED and a1.approvals == ("off-1",) and ev[0].to_state == State.PROPOSED
    with pytest.raises(WorkflowError, match="already approved"):
        wf.approve(a1, OFF1, T0, RULES)
    a2, ev = wf.approve(a1, OFF2, T0, RULES)
    assert a2.state == State.SENT and a2.approvals == ("off-1", "off-2")


def test_break_glass_needs_senior():
    with pytest.raises(WorkflowError) as e:
        wf.break_glass(alert(3), OFF1, T0, RULES, "urgent")
    assert e.value.kind == "forbidden"


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_break_glass_needs_reason(reason):
    with pytest.raises(WorkflowError) as e:
        wf.break_glass(alert(3), SENIOR, T0, RULES, reason)
    assert e.value.kind == "invalid"


def test_break_glass_sends_and_logs_reason():
    new, events = wf.break_glass(alert(3, State.ESCALATED), SENIOR, T0, RULES, "slope cracking")
    assert new.state == State.SENT and new.approvals == ()
    assert (events[0].action, events[0].actor, events[0].reason) == ("BREAK_GLASS", "sen-1", "slope cracking")


def test_escalation_after_configured_minutes():
    a = alert(2)
    same, events = wf.tick(a, T0 + RULES.escalate_after - timedelta(seconds=1), RULES)
    assert same.state == State.PROPOSED and events == []
    esc, events = wf.tick(a, T0 + RULES.escalate_after, RULES)
    assert esc.state == State.ESCALATED and events[0].actor == wf.SYSTEM
    again, events = wf.tick(esc, T0 + timedelta(hours=5), RULES)
    assert again.state == State.ESCALATED and events == []


@pytest.mark.parametrize("state", [State.SENT, State.ACKED])
def test_expiry(state):
    sent, _ = wf.approve(alert(2), OFF1, T0, RULES)
    a = replace(sent, state=state)
    assert wf.tick(a, sent.expires_at - timedelta(seconds=1), RULES)[0].state == state
    expired, events = wf.tick(a, sent.expires_at, RULES)
    assert expired.state == State.EXPIRED and events[0].action == "EXPIRE"


@pytest.mark.parametrize("state", [State.REJECTED, State.CANCELLED, State.EXPIRED, State.APPROVED])
def test_tick_leaves_other_states(state):
    a = alert(2, state, expires_at=T0)
    assert wf.tick(a, T0 + timedelta(days=1), RULES) == (a, [])


def test_edit_rules():
    with pytest.raises(WorkflowError):
        wf.edit(alert(2), OFF1, T0, "  ")
    partly, _ = wf.approve(alert(3), OFF1, T0, RULES)
    with pytest.raises(WorkflowError, match="after it has an approval"):
        wf.edit(partly, OFF2, T0, "new text")
    new, events = wf.edit(alert(2), OFF1, T0, " Hold at Banganga ")
    assert new.proposed_action == "Hold at Banganga" and events[0].detail["after"] == "Hold at Banganga"
