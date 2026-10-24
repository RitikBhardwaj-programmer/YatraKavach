# Replay findings: Adhkuwari landslide, 26 Aug 2025

Data spike run on 2026-10-23 with `scripts/fetch_replay_rain.py` (Open-Meteo, CC BY 4.0).
Point: Adhkuwari track junction (33.0085 N, 74.9447 E). Times are IST.

## Event (sourced in `docs/research.md`)
- 26 Aug 2025, about 14:40 IST: landslide on the old track near Adhkuwari, Vaishno Devi. About 34 dead.
- The shrine board says it closed the old track by about 12:00. Critics say IMD alerts were ignored.

## What the archived model rain shows

Cumulative rain on 26 Aug from 00:00 IST (measured from the saved files):

| Model (source) | 25 Aug total | by 06:00 | by 09:00 | by 12:00 | by 14:00 | 26 Aug total |
|---|---|---|---|---|---|---|
| ECMWF IFS 0.25 (historical forecast) | 22.2 mm | 36.0 | 63.9 | 120.9 | 183.3 | 300.0 mm |
| GFS (historical forecast) | 48.2 mm | 131.8 | 184.9 | 217.6 | 222.7 | 230.3 mm |
| ERA5 (reanalysis, not real-time) | 24.1 mm | 50.3 | 77.9 | 111.2 | 147.0 | 234.0 mm |

Thresholds (sourced: Shah et al. 2024 for NH-44; Dahal & Hasegawa 2008 for the Himalaya):
- 14.35 mm/day: watch level. Crossed before 06:00 on 26 Aug in every model.
- 144 mm/day: high-risk level. Crossed by 06:00 in GFS and between 12:00 and 14:00 in ECMWF and ERA5.

## What this means (inference)
- A rule-based system reading these feeds would have raised the Adhkuwari segments to WARNING several
  hours before 14:40, and to SEVERE by about midday or earlier.
- "Historical forecast" data are short-lead forecasts stitched together. They are close to what a live
  system would have seen, but not identical. Say this on the replay screen.
- The models are 9-25 km grids. They show a very wet day over the whole area, not the exact slope.
  The replay proves "the signal existed in time", not "the model predicts landslides".

## System result (measured 2026-10-24, thresholds version 2026-10-24.1)
Full replay through the API (`POST /api/replay/run?until=2025-08-26T14:00+05:30`), segment `VD-OLD-01`
(old track at Adhkuwari). The past slide on this segment is dated 14:40, so it does not raise these levels.

| Source | First ORANGE (25-26 Aug storm) | First RED | Lead time of RED before 14:40 |
|---|---|---|---|
| GFS (historical forecast) | 25 Aug 15:00 IST | 26 Aug 05:00 IST | about 9.5 h |
| ECMWF IFS (historical forecast) | 26 Aug 02:00 IST | 26 Aug 13:00 IST | about 1.5 h |
| ERA5 (reanalysis, not real-time) | 26 Aug 01:00 IST | 26 Aug 13:00 IST | about 1.5 h |

- Alerts (GFS): at 26 Aug 14:00 there are 6 open proposals, one per track and level (old track, Himkoti
  track, trunk; ORANGE and RED). Earlier storms (11-24 Aug) produced 22 proposals, all withdrawn by the system
  when the risk cleared before anyone acted.
- SIMULATED holding-area scenario: with ascent stopped at the Katra gate from 25 Aug evening, the held queue
  reaches the 15,000 cap by about 06:00 on 26 Aug: 5.4 persons/m2 on segment `VD-TRUNK-01` (crowd ORANGE),
  inside a segment whose own hazard is RED. Closing the track moves the risk to the people held below it.

## Impact counterfactual (measured 2026-10-24, thresholds version 2026-10-24.2; all persons SIMULATED)
`GET /api/impact/counterfactual` on a fresh database after the replay to 26 Aug 14:00. Persons on `VD-OLD-01`
at 14:00, the last whole hour before the 14:40 slide, if officers had approved the hold at each time:

| Hold approved at | GFS | ECMWF IFS | ERA5 |
|---|---|---|---|
| First ORANGE of the 25-26 Aug storm | **0** (25 Aug 15:00) | **0** (26 Aug 02:00) | **0** (26 Aug 01:00) |
| First RED | **93** (26 Aug 05:00) | 674 (26 Aug 13:00) | 674 (26 Aug 13:00) |
| Shrine board closure (~12:00, approximate) | 674 | 674 | 674 |
| No action | 674 | 674 | 674 |

- In every case the hold point is the Katra gate (`VD-TRUNK-01`), because the trunk itself is ORANGE/RED. The gate
  is 6.3 km below `VD-OLD-01`: anyone there at 14:00 passed the gate before about 11:53, so a later hold cannot
  change that count. Only the ascent is stopped; pilgrims already above the hold keep walking.
- 674 = 438 ascending + 236 descending, checked by an independent re-implementation (PR 9). If the 12:00 closure
  is modelled at Adhkuwari (`VD-TRUNK-13`) instead of the gate, 236 remain (descending only); not in the API.
- "First ORANGE/RED" = first hour of the warning still in force at the snapshot. A storm on 14-15 Aug also took
  `VD-OLD-01` to ORANGE; that warning had cleared and is not counted.
- What it means (inference): acting on the ORANGE warning would have emptied the slide segment in all three
  weather models; acting on the GFS RED would have cut exposure from 674 to 93. Acting at the time the track was
  actually closed changes nothing in this model.

## Camera crowd count (measured 2026-10-24)
- Model: DM-Count (MIT), official ShanghaiTech A weights, ONNX fp16, 43.0 MB, sha256 pinned in
  `config/thresholds.yaml`. ONNX matches torch exactly on two images; fp16 is within 0.03% of fp32 (PR 10).
- Accuracy on the 182 ShanghaiTech Part A test images: **MAE 60.10** (fp16), 60.09 (fp32), RMSE 96.16 (PR 10).
  The DM-Count paper reports 59.7.
- Demo photos through `POST /api/vision/count` in the Docker image (Python 3.12, CPU): Kumbh 2019: 340 people,
  4.3 s; Kumbh 2025: 65, 1.9 s; Ganesh Visarjan 2025: 746, 4.1 s; Rath Yatra 2007: 716, 4.9 s (model time).
  The whole request takes 3-8 s, because the heatmap is returned as a 0.6-2.5 MB PNG.

## Not done
- Machail / Chasoti (14 Aug 2025): OpenStreetMap has no trek line past the road end (about 33.338 N,
  76.207 E), and the Chasoti point is not in OSM. Overpass was failing (HTTP 502 / timeouts) on 2026-10-23.
  Stretch goal only.
