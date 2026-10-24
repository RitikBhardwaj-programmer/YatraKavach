# Demo video script: YatraKavach (target 4:00, limit 3-5 min strict)

Format: MP4, at least 720p, max 80 MB. Screen recording of the console at `http://localhost:8000/` in REPLAY
mode, with your face in a small corner box for the intro and the end. Record voice separately if the room is noisy.
Before recording: run the replay (`POST /api/replay/run`), reload the console, close other tabs, zoom browser to 110%.

| Time | Screen | Voice (say it in your own words; ~130 words per minute) |
|---|---|---|
| 0:00-0:20 | Face + title card "YatraKavach — team kavach, J&K" | "I'm Ritik, IT student at NIT Srinagar. This is YatraKavach: it tells an officer which 500-metre stretch of a pilgrim track is dangerous, how many people are on it, and makes sure someone decides — in time, on record." |
| 0:20-0:55 | Slide: three dated events | "26 August 2025, 2:40 pm: a landslide on the old Vaishno Devi track at Adhkuwari killed at least 34 pilgrims. Twelve days earlier at Chasoti, IMD alerts existed and the yatra went on. In 2022 at Amarnath, there was no rain data from above the cave. Each time a warning existed somewhere. What was missing was the step from a district alert to: close this stretch, move these people, now." |
| 0:55-1:25 | Console, LIVE then REPLAY; map of 35 segments, legend | "The tracks are cut into 35 segments of about 500 metres. Every hour each segment gets a hazard level from rain over 3 hours, a day and 15 days, using published Himalayan thresholds, plus slope. Everything you see is open data; crowd numbers are simulated and labelled so." |
| 1:25-2:10 | Slider to 25 Aug 15:00 → 26 Aug 05:00; click VD-OLD-01; show "Why" | "This is a replay of the real forecasts. 25 August, 3 pm: the old track turns orange. 26 August, 5 am: red — nine and a half hours before the slide. Click a segment and it says why: 24-hour rain, threshold, slope. With a second forecast model the lead is only one and a half hours, and I show that too, because coarse forecasts can't see single storms. That's why a human decides." |
| 2:10-2:40 | Click VD-TRUNK-01: held queue, crowd ORANGE | "Closing a track isn't free. When the ascent stops, pilgrims queue below. In this simulated scenario the queue at Katra reaches 5.4 people per square metre — inside a segment that is itself red. So the system weighs hazard and people together." |
| 2:40-3:25 | Alerts panel: RED alert; approve as Officer A (1 of 2); try again (refused); approve as Officer B → SENT; open CAP XML (Hindi/Urdu); audit trail + "verified" | "The system only proposes — one alert per track. Red needs two different officers. Officer A approves: one of two. The same officer can't approve twice. Officer B approves, and it goes out as a CAP alert — the standard format NDMA's SACHET uses — in English, Hindi and Urdu. Every step is in a hash-chained log nobody can edit. So afterwards, everyone can see who decided, and when." |
| 3:25-3:45 | Slide: integrate, not replace + roadmap | "YatraKavach doesn't replace IMD, RFID or SACHET. It's the thin layer that joins them at the scale of one stretch. Next step: a one-monsoon pilot with the shrine board and SDRF, with radar and track rain gauges, to calibrate the thresholds." |
| 3:45-4:00 | Face + repo URL + "Built with AI assistance — see README" | "It's open source. Thank you." |

## Recording checklist
- [ ] 3:00-5:00 exactly; trim silence. 720p or higher; under 80 MB (OBS: 1280x720, 30 fps, ~2.5 Mbps ≈ 75 MB for 4 min).
- [ ] Say "simulated" whenever crowd numbers or delivery are on screen.
- [ ] Don't claim the system "predicts landslides"; say "the warning signal was there in time".
- [ ] File name: `JK_kavach_DemoVideo.mp4`.

## 3-minute stall pitch (national round)
Cut the video script to: 0:00-0:20 intro, the Adhkuwari event only (20 s), replay 05:00 RED + why (40 s),
two-officer approval + CAP + audit (50 s), integrate-not-replace + pilot ask (30 s), close (10 s).
