"""Alert approval state machine (pure, no DB). Contract: docs/PLAN.md "Alert workflow".

PROPOSED -> APPROVED -> SENT -> ACKED; PROPOSED -> REJECTED; PROPOSED -> ESCALATED (no action in time)
-> APPROVED/REJECTED; any open state -> CANCELLED; SENT/ACKED -> EXPIRED; PROPOSED/ESCALATED -> SENT by
break-glass (senior + written reason); PROPOSED/ESCALATED -> CANCELLED by the system (WITHDRAW) when the
risk condition cleared before anyone acted. Sending is SIMULATED and happens as soon as approvals are complete.
Every function returns the new alert plus the events to append to the audit log.
"""
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any


class State(StrEnum):
    PROPOSED = "PROPOSED"
    ESCALATED = "ESCALATED"
    APPROVED = "APPROVED"
    SENT = "SENT"
    ACKED = "ACKED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


PENDING = frozenset({State.PROPOSED, State.ESCALATED})
OPEN = frozenset({State.PROPOSED, State.ESCALATED, State.APPROVED, State.SENT, State.ACKED})
LIVE = frozenset({State.SENT, State.ACKED})
SYSTEM = "system"


class WorkflowError(ValueError):
    """A forbidden transition or an invalid request (maps to HTTP 409/403/422)."""

    def __init__(self, message: str, kind: str = "conflict"):
        super().__init__(message)
        self.kind = kind  # conflict | forbidden | invalid


@dataclass(frozen=True)
class Rules:
    escalate_after: timedelta
    expires_after: timedelta
    red_needs: int
    orange_needs: int
    propose_at: int

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> "Rules":
        a = cfg["alerts"]
        return cls(timedelta(minutes=a["escalate_after_min"]), timedelta(minutes=a["expires_after_min"]),
                   a["red_needs_approvals"], a["orange_needs_approvals"], a["propose_at_risk_level"])

    def needs_approvals(self, level: int) -> int:
        return self.red_needs if level >= 3 else self.orange_needs


@dataclass(frozen=True)
class Officer:
    id: str
    role: str  # officer | senior


@dataclass(frozen=True)
class Alert:
    level: int
    state: State
    proposed_action: str
    created_at: datetime
    needs_approvals: int
    approvals: tuple[str, ...] = ()
    sent_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class Event:
    action: str
    actor: str
    from_state: State | None
    to_state: State
    at: datetime
    reason: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


def _require(alert: Alert, allowed: frozenset[State], action: str) -> None:
    if alert.state not in allowed:
        raise WorkflowError(f"cannot {action} an alert in state {alert.state}")


def _reason(reason: str | None, action: str) -> str:
    if not reason or not reason.strip():
        raise WorkflowError(f"{action} needs a written reason", "invalid")
    return reason.strip()


def propose(level: int, action_text: str, now: datetime, rules: Rules) -> tuple[Alert, list[Event]]:
    if level < rules.propose_at:
        raise WorkflowError(f"level {level} is below the proposal level {rules.propose_at}", "invalid")
    alert = Alert(level, State.PROPOSED, action_text, now, rules.needs_approvals(level))
    return alert, [Event("PROPOSE", SYSTEM, None, State.PROPOSED, now)]


def _send(alert: Alert, actor: str, action: str, now: datetime, rules: Rules,
          reason: str | None = None) -> tuple[Alert, Event]:
    sent = replace(alert, state=State.SENT, sent_at=now, expires_at=now + rules.expires_after)
    return sent, Event(action, actor, alert.state, State.SENT, now, reason, {"delivery": "SIMULATED"})


def approve(alert: Alert, officer: Officer, now: datetime, rules: Rules,
            reason: str | None = None) -> tuple[Alert, list[Event]]:
    _require(alert, PENDING, "approve")
    if officer.id in alert.approvals:
        raise WorkflowError(f"officer {officer.id} has already approved this alert")
    approvals = alert.approvals + (officer.id,)
    detail = {"approvals": len(approvals), "needs_approvals": alert.needs_approvals}
    if len(approvals) < alert.needs_approvals:
        return replace(alert, approvals=approvals), [
            Event("APPROVE", officer.id, alert.state, alert.state, now, reason, detail)]
    approved = replace(alert, state=State.APPROVED, approvals=approvals)
    sent, send_event = _send(approved, SYSTEM, "SEND", now, rules)
    return sent, [Event("APPROVE", officer.id, alert.state, State.APPROVED, now, reason, detail), send_event]


def reject(alert: Alert, officer: Officer, now: datetime, reason: str | None = None) -> tuple[Alert, list[Event]]:
    _require(alert, PENDING, "reject")
    return replace(alert, state=State.REJECTED), [Event("REJECT", officer.id, alert.state, State.REJECTED, now, reason)]


def cancel(alert: Alert, officer: Officer, now: datetime, reason: str | None = None) -> tuple[Alert, list[Event]]:
    _require(alert, OPEN, "cancel")
    return replace(alert, state=State.CANCELLED), [
        Event("CANCEL", officer.id, alert.state, State.CANCELLED, now, reason)]


def withdraw(alert: Alert, now: datetime, reason: str) -> tuple[Alert, list[Event]]:
    """System cancel of a proposal that nobody acted on before its risk condition cleared."""
    _require(alert, PENDING, "withdraw")
    return replace(alert, state=State.CANCELLED), [
        Event("WITHDRAW", SYSTEM, alert.state, State.CANCELLED, now, reason)]


def ack(alert: Alert, officer: Officer, now: datetime, reason: str | None = None) -> tuple[Alert, list[Event]]:
    _require(alert, frozenset({State.SENT}), "acknowledge")
    return replace(alert, state=State.ACKED), [Event("ACK", officer.id, alert.state, State.ACKED, now, reason)]


def break_glass(alert: Alert, officer: Officer, now: datetime, rules: Rules,
                reason: str | None) -> tuple[Alert, list[Event]]:
    if officer.role != "senior":
        raise WorkflowError("break-glass needs a senior officer", "forbidden")
    text = _reason(reason, "break-glass")
    _require(alert, PENDING, "break-glass")
    sent, event = _send(alert, officer.id, "BREAK_GLASS", now, rules, text)
    return sent, [event]


def edit(alert: Alert, officer: Officer, now: datetime, action_text: str | None) -> tuple[Alert, list[Event]]:
    _require(alert, PENDING, "edit")
    if alert.approvals:
        raise WorkflowError("cannot edit an alert after it has an approval")
    text = (action_text or "").strip()
    if not text:
        raise WorkflowError("proposed_action must not be empty", "invalid")
    return replace(alert, proposed_action=text), [
        Event("EDIT", officer.id, alert.state, alert.state, now, None, {"before": alert.proposed_action, "after": text})]


def tick(alert: Alert, now: datetime, rules: Rules) -> tuple[Alert, list[Event]]:
    """Time-driven transitions: escalation of an unanswered proposal, expiry of a sent alert."""
    if alert.state == State.PROPOSED and now - alert.created_at >= rules.escalate_after:
        return replace(alert, state=State.ESCALATED), [
            Event("ESCALATE", SYSTEM, State.PROPOSED, State.ESCALATED, now,
                  f"no officer action within {int(rules.escalate_after.total_seconds() // 60)} min")]
    if alert.state in LIVE and alert.expires_at is not None and now >= alert.expires_at:
        return replace(alert, state=State.EXPIRED), [Event("EXPIRE", SYSTEM, alert.state, State.EXPIRED, now)]
    return alert, []
