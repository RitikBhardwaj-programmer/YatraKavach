# YatraKavach

**Route-segment landslide and crowd risk for the Vaishno Devi tracks, with alerts that a named officer approves,
in three languages, with a tamper-evident audit log.**

Prototype for **Hack for Social Cause 2027** (VBYLD 2027, Ministry of Youth Affairs & Sports; knowledge partner
IIT Bombay). Theme 11: Disaster Mitigation & Resilience. Team **kavach**, Jammu & Kashmir (HSC|JK|00032).

> **The warning existed. The decision did not.**
> On 26 Aug 2025 at 14:40 a landslide on the old Vaishno Devi track near Adhkuwari killed at least 34 pilgrims.
> In a replay of the rain forecasts of that day, YatraKavach raises the Adhkuwari segment to **RED at 05:00 IST**
> (GFS forecast), about 9.5 hours before the slide, and proposes "clear the old track" for officer approval.
> With the ECMWF forecast the lead time is about 1.5 hours. Details: [docs/replay-findings.md](docs/replay-findings.md).

## The problem
Three recent yatra disasters in J&K show the same break (sources in [docs/research.md](docs/research.md)):

| Date | Place | What happened |
|---|---|---|
| 8 Jul 2022 | Amarnath cave | Flash flood; no rain data from the upper reaches |
| 14 Aug 2025 | Chasoti, Machail yatra | IMD alerts existed for the region; the yatra went on; about 61-64 dead |
| 26 Aug 2025 | Adhkuwari, Vaishno Devi | Landslide at 14:40; at least 34 dead; the board says it closed the old track by 12:00 |

India already has forecasts (IMD), landslide bulletins (GSI), crowd systems (RFID, CCTV) and mass alerts
(NDMA SACHET, cell broadcast). They work in silos and at district scale. What was missing each time was the step
from "regional alert" to **"close this 500 m stretch now, move the people on it, and record who decided"**.

## What YatraKavach does
1. **Splits each track into ~500 m segments** (35 segments: trunk Katra-Adhkuwari, old track, Himkoti track),
   with slope from a digital elevation model.
2. **Scores landslide hazard per segment every hour** from rain over 3 h, 24 h and 15 days, using published
   Himalayan rainfall thresholds, plus a step-up for steep slopes and recorded past slides. Every level comes
   with its reasons in numbers ("24 h rain 191 mm = 1.3x the 144 mm threshold; slope 41 deg").
3. **Adds people:** pilgrims on each segment (SIMULATED RFID gate counts, capped at the 50,000/day limit), and a
   SIMULATED holding-area scenario: when the ascent is stopped, pilgrims queue at Katra, Banganga or Adhkuwari.
   Risk rises when a hazardous segment has people on it.
4. **Proposes one action per track and level** ("Hold pilgrims at Adhkuwari; stop ascent beyond ...",
   "Clear segments ...; move pilgrims to ..."). Nothing goes out automatically.
5. **A named officer approves.** RED needs two different officers. No answer in 10 minutes: escalation.
   A senior officer can "break glass" with a written reason. Every step is written to a hash-chained audit log
   that cannot be edited (database triggers block UPDATE and DELETE) and can be verified.
6. **Sends a CAP 1.2 alert** (Common Alerting Protocol, the format NDMA SACHET uses) in English, Hindi and Urdu,
   with the affected area as a polygon. In this prototype every message is `status=Exercise` and delivery is SIMULATED.
7. **Replays August 2025** hour by hour, so anyone can check what the system would have proposed and when.

## Architecture

```mermaid
flowchart LR
  subgraph Inputs
    OSM["OpenStreetMap tracks<br/>+ Copernicus DEM"] --> SEG[(segments<br/>PostGIS)]
    OM["Open-Meteo rain<br/>live + Aug 2025 archive"] --> RAIN[(rain_hourly)]
    SIM["Crowd simulator<br/>RFID gate counts<br/>SIMULATED"]
  end
  RAIN --> HZ["Hazard engine<br/>thresholds, slope,<br/>past slide, hysteresis"]
  SEG --> HZ
  HZ --> SH[(segment_hazard)]
  SH --> HOLD["Holding-area scenario<br/>SIMULATED"]
  SIM --> HOLD --> SC[(segment_crowd)]
  SH --> FUSE["Risk fusion"]
  SC --> FUSE --> SR[(segment_risk)]
  SR --> PROP["Proposals<br/>one per track + level"]
  PROP --> WF{"Officer approval<br/>2 officers for RED<br/>escalation, break-glass"}
  WF --> AUD[(audit_log<br/>hash chain)]
  WF --> CAP["CAP 1.2 XML<br/>en / hi / ur"]
  CAP --> OUT["SACHET, cell broadcast,<br/>SMS, PA: SIMULATED"]
  SR --> UI["Officer console<br/>map, replay, alerts"]
  WF --> UI
```

| Part | Code | Notes |
|---|---|---|
| Hazard rules (pure) and engine | `backend/app/hazard/` | Rules in `config/thresholds.yaml`, versioned; each row stores the version |
| Crowd simulator, holding scenario | `backend/app/crowd/` | Everything here is SIMULATED and labelled so |
| Risk fusion, segments API, replay | `backend/app/risk/` | `POST /api/replay/run` recomputes the whole chain |
| Alert workflow, CAP, audit | `backend/app/alerts/` | State machine is pure Python; DB layer locks and audits |
| Officer console | `frontend/` | Static HTML + MapLibre GL, no build step |
| Schema | `db/init/*.sql` | PostgreSQL 16 + PostGIS 3 |
| Contract and design | `docs/PLAN.md` | Schema, rules, API, workflow |

Stack: Python 3.12, FastAPI, PostgreSQL 16 + PostGIS 3, psycopg 3, pytest, MapLibre GL JS, Docker Compose.

## Run it

Requirements: Docker Desktop (or Docker Engine with Compose), Git, free ports 5432 and 8000.

```bash
git clone https://github.com/RitikBhardwaj-programmer/YatraKavach.git
cd YatraKavach
docker compose up -d --build
docker compose exec api python scripts/load_segments.py
docker compose exec api python scripts/load_replay_rain.py
curl -X POST "http://localhost:8000/api/replay/run"
```

Open http://localhost:8000/ and pick **REPLAY**. Move the slider to 26 Aug 2025 to watch the tracks turn red,
click a segment to see why, and approve an alert as two different demo officers.

- The replay run takes about 30-60 seconds.
- If a local PostgreSQL already uses port 5432 or something uses 8000, choose other host ports, for example
  `YK_DB_PORT=55432 YK_API_PORT=8010 docker compose up -d --build`.
- To replay only up to a moment (the console's clock), add `?until=2025-08-26T14:00:00%2B05:30`.
- Live mode: `curl -X POST "http://localhost:8000/api/hazard/run?mode=live"` fetches current Open-Meteo rain.
- API docs: http://localhost:8000/docs

### Tests
```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://yk:yk_dev_only@localhost:5432/yatrakavach pytest
```
197 tests (measured 2026-10-24). Pure-logic tests run without a database; database tests skip with a message when
none is reachable. Use the port you gave `YK_DB_PORT`.

## Data sources and licences
- Tracks: © OpenStreetMap contributors, [ODbL](https://opendatacommons.org/licenses/odbl/).
- Elevation: Copernicus DEM GLO-90 via the [Open-Meteo Elevation API](https://open-meteo.com/en/docs/elevation-api).
- Rain: [Open-Meteo.com](https://open-meteo.com/), CC BY 4.0. Live forecast; Historical Forecast API (ECMWF IFS
  0.25, NOAA GFS) and ERA5 reanalysis for the replay. Free tier, non-commercial use.
- Thresholds: Shah et al. 2024 (NH-44 / Kashmir daily and antecedent rain), Dahal & Hasegawa 2008 (Nepal
  Himalaya intensity-duration curve, 144 mm/day). Full list with links in [docs/research.md](docs/research.md).
- How the data files were made: `scripts/build_segments.py`, `scripts/fetch_replay_rain.py`.

## Limitations (read before judging the numbers)
- **Thresholds are not calibrated for these tracks.** They come from studies of NH-44 and the Nepal Himalaya.
  A real deployment needs local slide records and a calibration season.
- **Rain data are coarse.** Forecast models use 9-25 km grid cells. They show a dangerous day over the area; they
  cannot see a single cloudburst cell or the exact slope that fails. A real deployment would use IMD Doppler radar
  (Jammu, Srinagar, Banihal) and rain gauges on the track.
- **Replay is not a real-time test.** The "historical forecast" data are short-lead forecasts stitched together,
  close to what a live system would have seen, but not identical. ERA5 is a later reanalysis and was not
  available on the day.
- **Lead time depends on the model:** about 9.5 h with GFS, about 1.5 h with ECMWF and ERA5 on 26 Aug 2025.
- **Crowd numbers are SIMULATED.** No RFID or CCTV feed was used. The holding-area queue is a scenario with
  assumed sites, capacity and release rate. It does not reduce the flow above a hold, so exposure there is overstated.
- **No GSI susceptibility layer.** The GSI 1:50k map could not be obtained in time; slope is the stand-in.
- **Delivery is SIMULATED.** No SMS, SACHET, cell broadcast or siren is triggered. CAP messages are `Exercise`.
- **Hindi and Urdu texts need review by native speakers.** Dogri and Kashmiri are not done yet.
- **Machail route is not included:** OpenStreetMap has no trek line past the road end.
- **No authentication:** demo officers are picked from a list. Production needs real identity (e.g. government SSO).
- CAP XML is checked for structure in tests, but not yet against the official OASIS schema file.

## What it integrates, not replaces
YatraKavach is a thin decision layer. In a deployment it would read IMD radar and GSI bulletins, SMVDSB RFID gate
counts and CCTV density, and hand approved CAP messages to NDMA SACHET, the shrine-board app and camp PA systems.
It does not build its own sensors or alert network.

## AI-use disclosure
The HSC 2027 rules ask for a disclosure of AI use and an estimate of its share.

- **Tool:** Claude Code (Anthropic, model Claude Opus 5.5), used as a coding and research agent, including
  parallel agent sessions for the hazard engine, the alert workflow and the console.
- **What AI did:** web research and the sourced research report; most of the source code, tests and
  documentation; an independent code review that found the replay-hindsight bug and the alert flood.
- **What the team did:** chose the problem and the J&K focus; set the requirements and constraints; approved every
  design decision and each fix; ran, checked and judged the results; owns the pitch.
- **Share (team estimate):** about 85-90% of the code and documents were generated by AI under the team's
  direction; the problem framing, decisions and validation are the team's.

<!-- TODO before submission: confirm the share above is your honest estimate. -->

## Licence
Code: MIT, see [LICENSE](LICENSE). Data keep their own licences (above).
