"""Alerts API (workstream B): workflow actions, CAP XML, audit. Contract: docs/PLAN.md "HTTP API".

No authentication (prototype): the officer is named in the request body and checked against `officers`.
"""
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from app import db
from app.alerts import service
from app.alerts.workflow import WorkflowError
from app.risk.repo import ist

router = APIRouter(tags=["alerts"])
_STATUS = {"conflict": 409, "forbidden": 403, "invalid": 422, "not_found": 404}


class ActionBody(BaseModel):
    officer_id: str
    reason: str | None = None


class EditBody(BaseModel):
    officer_id: str
    proposed_action: str


def _run(fn):
    try:
        with db.conn() as c:
            return ist(fn(c))
    except WorkflowError as e:
        raise HTTPException(_STATUS[e.kind], str(e)) from e


@router.get("/alerts")
def list_alerts(state: str | None = None):
    return _run(lambda c: service.list_alerts(c, state))


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int):
    return _run(lambda c: service.get_alert(c, alert_id))


def _action(name: str):
    def handler(alert_id: int, body: ActionBody):
        return _run(lambda c: service.act(c, alert_id, name, body.officer_id, body.reason))
    handler.__name__ = f"alert_{name.replace('-', '_')}"
    return handler


for _name in ("approve", "reject", "cancel", "ack", "break-glass"):
    router.post(f"/alerts/{{alert_id}}/{_name}")(_action(_name))


@router.patch("/alerts/{alert_id}")
def edit_alert(alert_id: int, body: EditBody):
    return _run(lambda c: service.act(c, alert_id, "edit", body.officer_id, proposed_action=body.proposed_action))


@router.get("/alerts/{alert_id}/cap.xml")
def cap_xml(alert_id: int):
    try:
        with db.conn() as c:
            return Response(service.cap_xml(c, alert_id), media_type="application/cap+xml")
    except WorkflowError as e:
        raise HTTPException(_STATUS[e.kind], str(e)) from e


@router.get("/audit")
def audit(alert_id: int | None = None):
    return _run(lambda c: service.audit_rows(c, alert_id))


@router.get("/audit/verify")
def audit_verify():
    return _run(service.verify_chain)


@router.get("/officers")
def officers():
    return _run(service.officers)
