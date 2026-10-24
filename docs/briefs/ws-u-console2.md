# Brief: workstream U — console 2 (impact, camera, polish)

Read `CLAUDE.md` and `docs/PLAN.md` first; they are binding (see the impact and vision endpoints in "HTTP API").
Work on branch `ws-u-console2` and open a PR to `main`. Two other sessions build the backend at the same time, so
build against the contract with fixtures. Touch only U's paths: `frontend/` and `docs/api-fixtures/`.
If a `ui-design` skill is available, use it.

## Build
1. Fixtures in `docs/api-fixtures/` for `GET /api/impact/counterfactual`, `GET /api/vision/cameras`,
   `GET /api/vision/samples` and `POST /api/vision/count`, in the exact contract shapes, labelled EXAMPLE in
   `docs/api-fixtures/README.md`. Example numbers must look like examples (round, and labelled), not results.
   Add them to the `?fixtures=1` API layer in `frontend/app.js`.
2. Impact panel ("What if the hold had been approved earlier?"):
   - Horizontal bars: persons on the target segment at the snapshot, per scenario, in time order, with the decision
     time on each bar. Plain SVG or CSS; no new libraries.
   - A "SIMULATED" tag and one line under it: "Simulated pilgrims; only the ascent is stopped; see README".
3. Camera panel ("AI crowd count"):
   - Camera picker (from `/api/vision/cameras`), sample picker (from `/api/vision/samples`) and an image upload.
   - Show the image with the heatmap overlay (`heatmap_png_b64`), count, density, persons on segment, level, and ms.
   - A tag "AI model output on a demo photo, not a Vaishno Devi camera" and the photo's attribution line.
   - "Apply to live crowd" button only in LIVE mode (`persist=true`); it then reloads the segments.
4. KPI strip in the header: lead time shown as both models together, e.g. "first RED: GFS 9.5 h before, ECMWF 1.5 h
   before" (compute from the API if the data is there, else from `docs/replay-findings.md` text in a fixture, labelled),
   open alerts, audit status. Never show the GFS lead time without the ECMWF one.
5. Visual polish inside the current design: typography, spacing, header, panel hierarchy, focus states. Keep every
   "SIMULATED" label, the officer workflow and the attribution footer. Add "Crowd model: DM-Count (MIT)" and
   the photo credits to the footer.
6. Must work at 1366x768 and at phone width (390 px), with no horizontal scroll.

## Check your work
Serve the repo root (`python -m http.server`) and open `frontend/index.html?fixtures=1` in a headless browser
(Playwright if available). Save screenshots of the impact panel, the camera panel and the phone view to
`frontend/screenshots/` and attach them to the PR. Check that the browser console has no errors. If no browser is
available, say so in the PR.

## Done
PR open with screenshots or an exact note of what you could not check. Commit messages are imperative and end with
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the PR body ends with
`🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
Never mock, substitute or guess real-world data.
