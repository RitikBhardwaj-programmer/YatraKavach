"""Load the versioned rule set (config/thresholds.yaml) and the segments file for workstream B."""
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_REPO = Path(__file__).resolve().parents[3]


def _find(rel: str, env: str) -> Path:
    if os.environ.get(env):
        return Path(os.environ[env])
    for base in (_REPO, Path("/app")):
        if (base / rel).exists():
            return base / rel
    raise FileNotFoundError(f"{rel} not found (set {env})")


@lru_cache(maxsize=1)
def thresholds() -> dict[str, Any]:
    return yaml.safe_load(_find("config/thresholds.yaml", "THRESHOLDS_PATH").read_text(encoding="utf-8"))


def segments_geojson() -> dict[str, Any]:
    return json.loads(_find("data/segments_vaishno_devi.geojson", "SEGMENTS_PATH").read_text(encoding="utf-8"))
