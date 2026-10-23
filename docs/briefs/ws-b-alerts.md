# Brief: workstream B — crowd, risk fusion, alert workflow, CAP, audit

Read `CLAUDE.md` and `docs/PLAN.md` first; they are binding. Work on branch `ws-b-alerts` and open a PR to `main`.
Two other cloud sessions work at the same time: A (hazard) writes `segment_hazard`; C builds the console against
the API contract. Touch only B's paths: `backend/app/crowd/`, `backend/app/risk/`, `backend/app/alerts/`,
`backend/tests/{crowd,risk,alerts}/`, `db/init/020-029_*.sql`.

## Build
1. `db/init/020_alerts.sql`: tables `alerts`, `alert_approvals`, `audit_log` as described in PLAN "Alert workflow".
   `audit_log` gets a trigger that rejects UPDATE and DELETE. Store `prev_hash` and `hash`.
2. `backend/app/crowd/simulator.py`: SIMULATED RFID gate events. Pilgrims enter at Katra, walk up at 2-3 km/h,
   pick the old or Himkoti track, spend time at Bhawan and walk down. Use a seeded random generator, a daily
   cap of 50,000 (sourced NGT cap) and a realistic daytime peak. Produce `segment_crowd` rows per hour
   (`simulated = true`) for live and replay modes. Density = persons / (length_m x width_m); levels from
   `config/thresholds.yaml`.
3. `backend/app/risk/fuse.py` (pure) + writer: risk = max(hazard, crowd); if hazard >= 2 and crowd >= 1,
   risk = min(3, hazard + 1). Write `segment_risk` with merged `drivers`. Read `segment_hazard` only; never write it.
4. `backend/app/alerts/workflow.py` (pure state machine) + `service.py` (DB):
   - States, transitions, approval counts (RED needs 2 different officers), escalation after 10 min,
     break-glass by a `senior` with a reason, expiry. Auto-propose when risk_level >= 2 on a segment with no open alert.
   - Action text from templates (PLAN). Every transition appends an audit row; hash = sha256(prev_hash + canonical JSON).
5. `backend/app/alerts/cap.py`: CAP 1.2 XML (`urn:oasis:names:tc:emergency:cap:1.2`), `status=Exercise`,
   `msgType` Alert/Update/Cancel with `references`, one `<info>` per language (en-IN, hi-IN, ur-IN) from templates
   in `backend/app/alerts/templates/`, and an `<area>` polygon = 100 m buffer of the alert's segments.
   Hindi and Urdu text: write simple, short sentences and mark them "needs native-speaker review" in a comment.
6. Routers exposing `router` in `backend/app/risk/router.py` (segments GeoJSON, segment history, `POST /replay/run`
   that runs hazard via A's engine if present, then crowd, risk and proposals) and `backend/app/alerts/router.py`
   (alerts, approve/reject/cancel/ack/break-glass/PATCH, cap.xml, audit, audit/verify, officers). Contract: PLAN "HTTP API".
   If A's engine is not merged yet, call it through a small adapter and test with hand-made `segment_hazard` rows.
7. Tests: state machine (every allowed and forbidden transition, same officer approving twice, break-glass
   needs senior + reason), audit chain (tampering is detected), CAP XML (parses, required elements, three
   languages, polygon closed), crowd density bands, risk fusion. DB tests skip with a clear message if no DB.

## Done
PR open, tests passing, and the PR description lists what you verified and any contract questions.
Run pytest before you report.
If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
Never mock, substitute or guess real-world data.
