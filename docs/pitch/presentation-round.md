# State/UT presentation round (NIT Srinagar, HSC 2027)

Format (email from the HSC nodal officer, 2026-11-23): online PPT presentation to a jury, **5 min talk + 5 min Q&A**.
Date and slot: not announced yet.

Deck: `JK_kavach_Deck.pdf` / `.pptx` already follows the prescribed template slide for slide
(Cover, Problem – Proposed Solution, Technical Approach, Impact Potential, Feasibility and Risk Analysis, Team,
References; 7 slides; instruction slide removed; team-name oval, logo and footer kept). No rebuild needed.

## 5-minute talk track (~700 words, rehearse with a timer)

Target split: 20 s / 75 s / 60 s / 50 s / 45 s / 30 s / 20 s = 300 s. If you run long, cut the bracketed lines.

**1. Cover (20 s)**
Good morning. I am Ritik Bhardwaj, team kavach, ID HSC|JK|00032, a solo entry from NIT Srinagar under Theme 11,
Disaster Mitigation and Resilience. My project is YatraKavach: landslide and crowd risk early warning for the
Vaishno Devi route. One line sums it up: the warning existed; the decision did not.

**2. Problem – Proposed Solution (75 s)**
Three disasters on J&K pilgrim routes. Amarnath, July 2022: a flash flood with no rain data from the upper reaches.
Chasoti on the Machail yatra, August 2025: IMD alerts were out for the region, the yatra went on, and about 61 to 64
people died. Adhkuwari on the Vaishno Devi track, 26 August 2025: a landslide at 14:40, at least 34 dead.
Each time, a warning reached some official. What was missing was the step from a district warning to "close this
500-metre stretch, move these people, now", and a record of who decided.
YatraKavach is that step. It cuts the three Vaishno Devi tracks into 35 segments of about 500 m. Every hour it scores
landslide hazard per segment from rainfall against published Himalayan thresholds, raised on steep slopes. It adds
how many people are on that segment, and proposes one action per track: hold, clear or reopen. A named officer
approves; RED needs two officers. The approved alert goes out as CAP 1.2, the format NDMA's SACHET already uses, in
English, Hindi and Urdu. What is new: hazard times the people exposed right now, the queue a hold creates, and a
tamper-evident log of every decision.

**3. Technical Approach (60 s)**
This is a working prototype, not a mock-up. Python and FastAPI with PostgreSQL and PostGIS, a MapLibre map console,
and 258 automated tests that pass. It uses only open data: OpenStreetMap tracks, Copernicus elevation for slope, and
Open-Meteo rainfall from three weather models. An AI model, DM-Count, counts people in a camera frame.
This screenshot is a replay of 26 August 2025 at 5 a.m.: the old track is already RED, and the panel shows the rain
numbers that caused it. The code is on GitHub and the demo video was submitted with the entry.
On AI use: I used Claude Code as a coding and research agent. About 60 to 65 percent of the code and documents are
AI-generated under my direction. I chose the problem, set the requirements, approved every design and checked the
results.

**4. Impact Potential (50 s)**
Vaishno Devi alone allows up to 50,000 pilgrims a day. In the replay, the old track turned RED 9.5 hours before the
slide with the GFS model, and about 1.5 hours before with ECMWF and ERA5. I show the weak case on purpose.
In the simulation, if the hold had been approved at the first ORANGE, zero pilgrims would have been on the slide
segment at 14:00, instead of 674. [The users are the shrine-board control room, SDMA, SDRF and police; the people
protected are pilgrims, pony and palki operators and shopkeepers.] The same engine scales to Amarnath, Machail,
Char Dham and Sabarimala; only the segments and thresholds change.

**5. Feasibility and Risk Analysis (45 s)**
It already runs end to end, on open data and one small server, and it plugs into SACHET. The risks, honestly: the
rain thresholds come from NH-44 and Nepal studies and are not calibrated for these tracks. So the plan is a
read-only pilot for one monsoon with the shrine board and SDRF, then calibration with local slide records, IMD radar
and a few rain gauges. [Alert fatigue: grouping cut 27 open alerts to 6.] And a hold moves the risk: stopping the
ascent packs the Katra gate to 5.4 people per square metre, so the officer sees that queue before approving.

**6. Team (30 s)**
I am a solo team, third-year B.Tech IT at NIT Srinagar. I framed the problem, made the design decisions, directed the
AI agent and validated the replay. Two hard lessons: Machail is incomplete in OpenStreetMap, so I narrowed the scope
to Vaishno Devi; and my first replay used the very slide it was predicting as an input. I fixed that by dating every
past-slide factor.

**7. References + close (20 s)**
All sources are on the last slide, and every simulated number is labelled SIMULATED. To close: the forecast is not
the gap; the decision is. YatraKavach makes that decision fast, owned and recorded. Thank you.

## Q&A prep (answer in 2-3 sentences, then stop)

| Likely question | Short answer |
|---|---|
| GSI and IMD already issue warnings. Why this? | GSI bulletins are district-scale (no J&K district on the 2025 list) and IMD alerts cover regions. A 13 km trek needs per-segment action and a named decision-maker; that step is what failed in 2025. |
| Your lead time is only 1.5 h with two models. Is that useful? | It is enough to stop the ascent and clear a 500 m stretch, and with GFS it was 9.5 h. I show the spread to officers instead of one number; IMD radar input is the first upgrade. |
| Thresholds are not calibrated. Can you trust them? | Not yet, and I say so. That is why the pilot is read-only for one monsoon: compare proposals with real decisions and local slide records, then calibrate. |
| The crowd data is simulated. What is real? | Rain, terrain, tracks, scoring, approval flow, CAP output and audit log are real. Pilgrim counts stand in for the shrine board's RFID data, which needs a data-sharing MoU. |
| Won't it raise false alarms all monsoon? | Alerts are grouped: one per track and level (27 down to 6 in the replay). An officer approves every action, so nothing goes public automatically. |
| What if the officer ignores it or delays? | Escalation after 10 minutes, two officers for RED, break-glass with a written reason, and every step is in a hash-chained log. Accountability is the point. |
| Mobile coverage is weak on the track. | The action is a hold at a gate or holding point, done by shrine-board staff and police, so it does not need the pilgrim's phone. Phase 3 of the roadmap sends approved CAP to the public-address system as well as SACHET (planned, not built). |
| How much did you build vs the AI? | About 60-65% of code and documents are AI-generated under my direction. I chose the problem, set every requirement, approved each design and fix, and validated the replay numbers myself. |
| Cost to deploy? | One small server and open data; open source (MIT). The real costs are a few rain gauges and staff time for the pilot. |
| Why Vaishno Devi first, not Amarnath or Machail? | It has the best data (RFID, CCTV, a fixed track) and the 2025 slide to validate against. Machail is incomplete in OpenStreetMap; it is the next site. |
| How does the AI crowd count work and how good is it? | DM-Count estimates a density map from a camera frame; error is about 60 people per image on the ShanghaiTech A benchmark. It must be checked on shrine-board CCTV. |
| Who would own and run it? | The shrine-board control room with J&K SDMA; SDRF and police act on the proposals. |
| What do you need from the next round / mentor? | A contact at SMVDSB or SDMA for the pilot, local landslide records, and feedback on the officer workflow. |

## Before the slot
- [ ] Rehearse the talk with a timer twice; stop at 5:00.
- [ ] Open the PDF in full-screen in the meeting app and test screen sharing once.
- [ ] Keep the GitHub page and the demo video open in tabs in case the jury asks to see it.
- [ ] Repo public and README current.
- [ ] Mentor details sent to the nodal officer (draft kept outside the repo).
