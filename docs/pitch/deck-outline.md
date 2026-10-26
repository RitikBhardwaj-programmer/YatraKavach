# Deck outline: YatraKavach (HSC 2027, 7 slides)

Format: the IIT Bombay template from the portal's submission page, PPT or PDF, max 10 MB.
File name: `JK_kavach_Deck.pdf`. Order required by the guidelines: problem (1-2), solution (3-4),
impact and scale (5), team and implementation with AI disclosure (6-7).
Rule for every slide: one message in the title, one visual, at most ~40 words of text.
Numbers marked [measured] come from this repo; [sourced] from `docs/research.md`; [verify] must be checked first.

---

## Slide 1 — The warning existed. The decision did not.
**Visual:** timeline strip of three dated events, each with a photo-free icon and one line.
- 8 Jul 2022, Amarnath: flash flood; no rain data from the upper reaches [sourced]
- 14 Aug 2025, Chasoti (Machail yatra): IMD alerts for the region; yatra continued; ~61-64 dead [sourced]
- 26 Aug 2025, Adhkuwari (Vaishno Devi): landslide at 14:40; ≥34 dead; old track "closed by 12:00" [sourced]

**Say:** "In all three, a warning reached some official. Nobody turned it into 'close this stretch, move these
people, now' — and nobody can show who decided."

## Slide 2 — Who is affected, and where the gap is
**Visual:** four boxes in a row (IMD/GSI forecasts · RFID/CCTV crowd · SACHET mass alerts · shrine-board
control room) with a red gap between "district alert" and "pilgrim on segment X".
- Beneficiaries: pilgrims on mountain tracks (Vaishno Devi cap: 50,000/day [sourced]), pony and palki
  operators, shopkeepers on the track, SDRF and police on duty.
- Gaps: warnings are district-scale; crowd systems have no hazard input; mass alerts target areas, not people in
  transit; no record of who approved what [sourced/inference].
- SDG 11.5 (reduce deaths from disasters), SDG 3.

## Slide 3 — YatraKavach: risk per 500 m, decided by a named officer
**Visual:** the architecture flow from the README, simplified to 5 boxes:
Rain + slope → segment hazard → + people on segment → proposed action → officer approves → CAP alert (en/hi/ur).
- 35 segments on the three Vaishno Devi tracks; hazard every hour from published Himalayan rain thresholds.
- Fuses hazard with people on the segment; models the queue created when the ascent is stopped (SIMULATED).
- One proposal per track and level; RED needs two officers; escalation after 10 min; break-glass with a reason.
- AI crowd count from a camera frame (DM-Count) feeds the crowd level; demo on licensed festival photos.
- Hash-chained, append-only audit log. CAP 1.2, the format SACHET already uses.
- Stack: FastAPI, PostgreSQL/PostGIS, MapLibre; open source (MIT).

## Slide 4 — Replay: 26 August 2025
**Visual:** two console screenshots side by side: (a) 26 Aug 05:00 — old track RED, "Why" panel with rain
numbers; (b) the RED alert approved by two officers, CAP text in Hindi/Urdu, audit "verified" badge.
- Old track at Adhkuwari reaches RED at 05:00 IST (GFS), 9.5 h before the slide [measured].
- With ECMWF/ERA5 the lead is ~1.5 h [measured] — say it: honesty is a feature.
- Holding scenario: stopping the ascent fills Katra to 5.4 persons/m² inside a RED segment [measured, SIMULATED].
  "Closing a track moves the risk to the people below it."
- Impact panel: "If the hold had been approved at the first ORANGE warning, 0 simulated pilgrims would have been on
  the slide segment at 14:00, instead of 674" [measured, SIMULATED]; the cost is a queue at the Katra gate.
  A hold at ~12:00 (when the track was closed) at the Katra gate is too late for this segment: the people there had
  already passed the gate. The real closure was at Adhkuwari; modelled there, 236 descending pilgrims remain
  [measured in PR 9, not in the API].

## Slide 5 — Impact, KPIs and scale
**Visual:** KPI table (left), map of J&K yatra routes (right).
| KPI | Prototype result | Pilot target |
|---|---|---|
| Lead time of RED before a slide | 1.5-9.5 h on 26 Aug 2025 replay [measured] | ≥ 3 h with radar input |
| Alerts with a named approver and timestamp | 100% [measured] | 100% |
| Open alerts at peak (26 Aug, 14:00) | 6, one per track and level [measured] | ≤ 1 per track and level |
| Pilgrims on the slide segment at 14:00 | 674 no action → 0 if held at first ORANGE (all 3 models); at first RED 93 (GFS) / 674 (ECMWF, ERA5) [measured, SIMULATED] | decision within 1 h of ORANGE |
| Camera crowd count error | MAE 60 people/image on ShanghaiTech A [measured] | validated on SMVDSB CCTV |
| Time from proposal to decision | logged per alert | median < 10 min |
- Scale: same engine for Amarnath, Machail, Char Dham, Sabarimala — only segments and thresholds change.
- Languages: templates per language; add Dogri, Kashmiri, Pahari with native speakers.
- Sustainability: open source; runs on one small server; fits into shrine-board control rooms and SDMA.

## Slide 6 — Implementation roadmap and what it needs
**Visual:** 3-phase arrow.
1. Pilot (one monsoon): old track + Himkoti with SMVDSB control room and SDRF; read-only, no public alerts;
   compare proposals with real decisions.
2. Calibrate: local slide records, IMD radar feed, 3-5 rain gauges on the track, GSI susceptibility layer.
3. Integrate: RFID gate counts, CCTV density, approved CAP to SACHET, app and PA.
- Needs: data-sharing MoU, one server, a field officer champion, native-speaker review.
- Limits shown openly: uncalibrated thresholds, 9-25 km rain grid, simulated crowd and channels.

## Slide 7 — Team and AI-use disclosure
**Visual:** photo + one line, then the disclosure box.
- Ritik Bhardwaj, B.Tech IT, NIT Srinagar (solo): problem framing, design decisions, validation, pitch.
- Stakeholder feedback: [add the SDRF / district / shrine-board conversation if you get one — it is the
  strongest single addition, per the 2026 winners pattern].
- AI disclosure: built with Claude Code (Anthropic, Claude Opus 5.5) as coding and research agent. AI generated
  ~60-65% of code and documents under the team's direction; the team chose the problem, set requirements,
  approved every design and fix, and validated results [confirm the share].
- Repo: github.com/RitikBhardwaj-programmer/YatraKavach (make it public before submitting).

---

## Checklist before export
- [ ] Use the official IIT Bombay template; keep 7 slides.
- [ ] Replace screenshot placeholders with real console screenshots (replay at 26 Aug 05:00 and the approved alert).
- [ ] Confirm the AI share; confirm every [verify] number.
- [ ] Export PDF < 10 MB; name `JK_kavach_Deck.pdf`.
