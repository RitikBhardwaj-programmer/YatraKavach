"""YatraKavach API entry point. Each workstream adds its router in its own package (docs/PLAN.md)."""
import importlib
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

log = logging.getLogger("yatrakavach")
app = FastAPI(title="YatraKavach", version="0.1.0",
              description="Route-segment hazard + crowd risk with officer-approved alerts (prototype).")


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Workstream routers: each package exposes `router` in router.py. Missing ones are skipped
# so the app runs while workstreams are still in progress.
for pkg in ("hazard", "risk", "alerts", "impact", "vision"):
    try:
        app.include_router(importlib.import_module(f"app.{pkg}.router").router, prefix="/api")
    except ModuleNotFoundError as e:
        log.warning("router app.%s not loaded: %s", pkg, e)

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if not FRONTEND.exists():
    FRONTEND = Path("/app/frontend")
if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
