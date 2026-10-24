"""Call workstream A's hazard engine if it is merged. B never writes `segment_hazard` itself.

Calls `app.hazard.engine.run(mode=, source=, start=, end=)`, the entry point on branch ws-a-hazard (3c99189).
If A's engine is missing (not merged yet), the replay run continues with whatever `segment_hazard` rows exist.
"""
import importlib
import inspect
from datetime import datetime


def run_hazard(mode: str, source: str, start: datetime, end: datetime) -> dict:
    try:
        engine = importlib.import_module("app.hazard.engine")
    except ModuleNotFoundError:
        return {"ran": False, "source": source, "reason": "app.hazard.engine not present (workstream A not merged)"}
    fn = getattr(engine, "run", None)
    if not callable(fn):
        return {"ran": False, "source": source, "reason": "app.hazard.engine has no run(); update hazard_adapter.py"}
    wanted = {"mode": mode, "source": source, "start": start, "end": end}
    params = inspect.signature(fn).parameters
    summary = fn(**{k: v for k, v in wanted.items() if k in params})
    return {"ran": True, "source": source, "summary": summary}
