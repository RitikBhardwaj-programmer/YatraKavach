# Brief: workstream I — impact counterfactual (SIMULATED)

Read `CLAUDE.md` and `docs/PLAN.md` first; they are binding (see "Impact counterfactual" and
`GET /api/impact/counterfactual` in "HTTP API"). Work on branch `ws-i-impact` and open a PR to `main`. Two other
sessions work at the same time (V: vision, U: console). Touch only I's paths: `backend/app/impact/`,
`backend/tests/impact/`, `backend/app/crowd/simulator.py` (the new optional parameter only), and new test files in
`backend/tests/crowd/`.

Question to answer: "If officers had approved the hold at time T, how many (SIMULATED) pilgrims would have been on
the slide segment at the last hourly snapshot before the slide?" The numbers go on a pitch slide, so a quietly
wrong number is the main risk. Prefer simple, checkable logic.

## Build
1. `backend/app/crowd/simulator.py`: add `stop_ascent: dict[str, tuple[str, datetime]] | None = None` to
   `simulate()`. For a leaf route in `stop_ascent`, an ascending pilgrim who reaches the start of the hold segment
   at or after the hold time stays at the hold segment for the rest of the window: counted on the hold segment, not
   on any segment above it, and no descent. Pilgrims who passed the hold point earlier are unchanged.
   With `stop_ascent=None` the output must be exactly the current output. Do not change any other behaviour.
2. `backend/app/impact/` with `__init__.py`, `counterfactual.py` (pure), `service.py` (DB), `router.py`
   (exposes `router`; `main.py` already loads `app.impact.router`):
   - Targets = segments with `past_slide_at`; event = their `past_slide_at`; snapshot = the last whole IST hour
     at or before the event.
   - Decision times for the source: `first_orange` / `first_red` = first replay hour the target reaches level >= 2 /
     >= 3 in `segment_hazard` (mode `replay`, that source). `official_closure` = the "~12:00 shrine board" event
     from the replay timeline in `app/hazard/router.py` (import it; do not copy the timestamp). Label it approximate.
   - Hold points per leaf route at a decision time: `app.crowd.simulator.hold_points()` with the hazard levels of
     that hour (same source) and `app.crowd.service.holding_params()`.
   - Run `simulate()` over a window that ends at the snapshot (start early enough that pilgrims from the day before
     are included, as `simulate` already does) once per scenario, with the same seed and `SimParams` as the
     replay. Return persons on the target segment(s) at the snapshot.
   - Output exactly the shape in `docs/PLAN.md`, with `"simulated": true`. Omit a scenario whose decision time is
     missing or after the snapshot.
3. Tests (`backend/tests/impact/`, `backend/tests/crowd/test_stop_ascent.py`), no DB needed for the pure ones:
   - `stop_ascent=None` equals the old output on a small topology.
   - An earlier hold never gives more persons on the target than a later hold, and both are <= no action.
   - A hold point above the target changes nothing on the target. Pilgrims already above the hold are kept.
   - Held pilgrims appear on the hold segment.
   - The router returns the contract shape (DB test; skip with a clear message when no DB).

## Check your work
- `cd backend && pytest tests/impact tests/crowd` passes. If Docker or PostGIS is available, also run the full
  `pytest`, load the data (`scripts/load_segments.py`, `scripts/load_replay_rain.py`), run
  `POST /api/replay/run?until=2025-08-26T14:00:00%2B05:30`, then call the new endpoint for `gfs_seamless`,
  `ecmwf_ifs025` and `era5`, and put the three results in the PR. If there is no DB, say so in the PR.
- Hand-check one scenario: explain in the PR why its number is plausible (for example, persons on the target
  with no action vs the hourly arrivals on that track).

## Done
PR open with the results (or the exact reason they are missing) and the stated limitations (only ascent is stopped;
pilgrims already above the hold keep walking; all crowd numbers SIMULATED). Commit messages are imperative and end
with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the PR body ends with
`🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
Never mock, substitute or guess real-world data.
