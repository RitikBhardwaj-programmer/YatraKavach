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

## Not done
- Machail / Chasoti (14 Aug 2025): OpenStreetMap has no trek line past the road end (about 33.338 N,
  76.207 E), and the Chasoti point is not in OSM. Overpass was failing (HTTP 502 / timeouts) on 2026-10-23.
  Stretch goal only.
