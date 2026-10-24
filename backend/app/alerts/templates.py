"""Alert text templates (backend/app/alerts/templates/*.yaml) and their placeholder values (pure)."""
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.risk.topology import Topology

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
LANGUAGES = ("en-IN", "hi-IN", "ur-IN")


@lru_cache(maxsize=None)
def load(language: str) -> dict[str, Any]:
    return yaml.safe_load((TEMPLATE_DIR / f"{language}.yaml").read_text(encoding="utf-8"))


def context(topo: Topology, segment_ids: list[str]) -> dict[str, str]:
    """Placeholder values for a run of segments on one route (ascent order).

    No shelter dataset exists, so `shelter` is the nearest named landmark below the run (stated in the PR).
    """
    first = segment_ids[0]
    named = next((topo.by_id[s].landmark for s in segment_ids if topo.by_id[s].landmark), None)
    below = topo.landmark_below(first)
    root = topo.ascent_path(topo.by_id[first].route_id)[0]
    upstream = below.landmark if below else topo.label(root.id)
    return {
        "segments": first if len(segment_ids) == 1 else f"{first} to {segment_ids[-1]}",
        "place": named or first,
        "nearby": named or upstream,
        "upstream": upstream,
        "shelter": upstream,
    }


def officer_action(level: int, ctx: dict[str, str]) -> str:
    return load("en-IN")["officer_action"][level].format(**ctx)


def cap_text(language: str, key: int | str, ctx: dict[str, str]) -> dict[str, str]:
    """headline / description / instruction for one language; key = level (2, 3) or 'cancel'."""
    return {k: v.format(**ctx) for k, v in load(language)["cap"][key].items()}


def event_name(language: str) -> str:
    return load(language)["event"]
