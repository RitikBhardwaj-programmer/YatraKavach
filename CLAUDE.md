# YatraKavach — notes for coding agents

Prototype for Hack for Social Cause 2027 (deadline 26 Oct 2026). Read `docs/PLAN.md` first: it is the
contract (schema, rules, API, ownership). `docs/research.md` holds the sourced research;
`docs/replay-findings.md` holds the measured replay data.

## Rules
- Touch only the paths your workstream owns (table in `docs/PLAN.md`). Shared files need a note in the PR.
- Never change the API or DB contract silently. If you must, update `docs/PLAN.md` in the same PR and say why.
- Simulated data must stay labelled: `simulated: true` in data, "SIMULATED" in the UI.
- No secrets in the repo. The DB password in `docker-compose.yml` is a local demo value only.
- Every threshold comes from `config/thresholds.yaml`; no magic numbers in code.
- Python: type hints, small functions, pure logic separated from DB code so it is testable without a DB.
- Commit messages: imperative ("Add hazard scoring engine"). Open a PR per workstream branch.
- If something you need is missing (a file, a secret, access, a tool, network), say exactly what and stop.
  Never mock, substitute or guess real-world data.

## Commands
- `docker compose up -d db` then `cd backend && pip install -r requirements.txt && pytest`
- Without Docker: install PostgreSQL 16 + PostGIS 3 (`apt-get install postgresql-16-postgis-3`), create db
  `yatrakavach` (user `yk`, password `yk_dev_only`), run `db/init/*.sql` in order. If neither works,
  run only the pure-logic tests and say so in the PR.
- Run the API: `cd backend && uvicorn app.main:app --reload` -> http://localhost:8000/

## Data (already in the repo; do not re-download unless asked)
- `data/segments_vaishno_devi.geojson`: 35 segments, OSM (ODbL) + Copernicus DEM via Open-Meteo.
- `data/replay/rain_<point>_<model>.json`: hourly rain 10-28 Aug 2025, IST, Open-Meteo (CC BY 4.0).
- Attribution for both must appear in the UI footer and the README.
