"""Impact API (workstream I): GET /api/impact/counterfactual. Contract: docs/PLAN.md "HTTP API". SIMULATED."""
from fastapi import APIRouter, HTTPException

from app import db
from app.impact import service
from app.risk.repo import ist
from app.risk.router import DEFAULT_REPLAY_SOURCE

router = APIRouter(tags=["impact"])


@router.get("/impact/counterfactual")
def impact_counterfactual(source: str = DEFAULT_REPLAY_SOURCE) -> dict:
    with db.conn() as c:
        try:
            return ist(service.run(c, source))
        except LookupError as e:
            raise HTTPException(404, str(e)) from e
        except ValueError as e:
            raise HTTPException(409, str(e)) from e
