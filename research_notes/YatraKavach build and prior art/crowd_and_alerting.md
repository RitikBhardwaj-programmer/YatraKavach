# Crowd Safety and Public Alerting for Indian Pilgrimages (YatraKavach prototype)

Labels used: **sourced** = a cited link is given inline; **estimate** = own arithmetic with assumptions stated; **inference** = reasoned, not tested or not confirmed by a source fetched in this session. Research date: 2026-10-23. Searches ran on 2026-10-23. Some sources are secondary (news, exam-prep sites). These are marked where it matters.

## 1. Crowd density sensing options (accuracy, cost, prototype realism)

### Takeaway
Indian pilgrimages already use three of the sensing layers: CCTV with AI density estimation (Kumbh 2025), RFID gate and card counts (Amarnath and Vaishno Devi), and mandatory registration or booking data. A prototype can use open crowd-counting datasets and community CSRNet code for camera density, plus simulated RFID gate events and booking caps for segment counts. Telecom, Wi-Fi/BLE and drone data are not realistic for a student prototype.

### Cited Findings
**CCTV + computer vision (Kumbh 2025)**
- Maha Kumbh 2025: of 1,800 CCTV cameras, about 160 had AI. The AI calculated crowd density per square metre to estimate people in specific areas at specific times. Monitoring ran through four Integrated Command and Control Centres (ICCC) in the fair area — [Drishti IAS](https://www.drishtiias.com/state-pcs-current-affairs/ai-in-maha-kumbh-2025)
- Conflicting count: The Federal reports about 250 AI-enabled cameras out of about 2,750 cameras feeding the ICCC. It says the system flagged crowd density at bathing ghats and raised alerts on pre-set danger thresholds. Two of the four ICCC units were temporary set-ups at the Mela site — [The Federal](https://thefederal.com/category/states/north/uttar-pradesh/ai-surveillance-to-enhance-kumbh-mela-pilgrim-safety-officials-173089). Camera counts conflict between sources; treat both as approximate.
- AI headcount cameras ran 3 am to 7 pm on peak bathing days and were tested against a 95% accuracy target — [The Statesman](https://www.thestatesman.com/india/mahakumbh-2025-setting-a-global-benchmark-in-event-headcount-with-advanced-technology-1503374303.html). The 95% figure is a target, not a measured result.
- A stampede on 29 January 2025 killed at least 30 people and injured over 90, despite the AI camera system — [The Hitavada](https://www.thehitavada.com/Encyc/2025/2/23/-AI-based-surveillance-to-boost-safety-of-pilgrims-.html). After it, the ICCC officer said AI data would be analysed after the event and thresholds might be revised — [The Federal](https://thefederal.com/category/states/north/uttar-pradesh/ai-surveillance-to-enhance-kumbh-mela-pilgrim-safety-officials-173089).
- Vaishno Devi: the shrine board runs a dedicated CCTV network of over 700 cameras with real-time MIS reporting — [Tribune India](https://www.tribuneindia.com/news/j-k/vaishno-devi-shrine-sets-up-dedicated-network-of-over-700-cameras-for-e-surveillance-474077)
- Amarnath 2025: facial recognition systems (FRS) were installed on both Pahalgam and Baltal routes for the first time, with CCTV along the route — [The Week](https://www.theweek.in/news/sci-tech/2025/07/01/amarnath-yatra-goes-high-tech-top-of-the-line-facial-recognition-rfid-tagging-and-more-security-measures-in-place.amp.html)

**Crowd-counting models and open datasets**
- CSRNet (dilated CNN that outputs a density map (a per-pixel heat map whose sum equals the head count)) — paper at [arXiv 1802.10062](https://ar5iv.labs.arxiv.org/html/1802.10062)
- Reported CSRNet MAE (mean absolute error (average miss in head count per image)): about 68.2 on ShanghaiTech Part A, 10.6 on Part B — [arXiv 2004.03597](https://arxiv.org/pdf/2004.03597); [arXiv 1910.12384](https://arxiv.org/pdf/1910.12384)
- CSRNet on JHU-Crowd: 78.4 overall MAE, vs 66.1 for CG-DRCN — [arXiv 1910.12384](https://arxiv.org/pdf/1910.12384)
- CSRNet on UCF-QNRF: 110.6 MAE (third-party aggregator only, not the original paper) — [wizwand](https://www.wizwand.com/paper/68fa64441e209131cea039f3)
- Dataset splits (train/test images): UCF-QNRF 1,201/334; JHU-Crowd++ 2,722/1,600; ShanghaiTech A 482/300; ShanghaiTech B 716/400 — [arXiv 2212.04127](https://arxiv.org/pdf/2212.04127)
- JHU-CROWD++ is a large-scale dataset with weather and condition labels — [arXiv 2004.03597](https://arxiv.org/pdf/2004.03597)
- Open code: no single official CSRNet repo was found. Community ports include CommissarMa/CSRNet-pytorch and leeyeehoo/CSRNet-pytorch — [hyper.ai](https://vercel.hyper.ai/en/papers/1802.10062). PeekingDuck ships a ready CSRNet node; its reproduction gives 65.92 MAE on ShanghaiTech A (vs 68.2 in the paper) — [PeekingDuck docs](https://peekingduck.readthedocs.io/en/latest/resources/01d_crowd_counting.html)

**RFID cards and gate counts**
- Amarnath Yatra: RFID tags are mandatory for all pilgrims. They help authorities track movement, improve security and give help when needed. Counters were at Lakhanpur, Samba, Jammu, Udhampur, Ramban — [J&K SASB RFID page](https://jksasb.nic.in/rfid.html)
- RFID tags help locate missing pilgrims or respond to emergencies; RFID counters were set up in 2025 — [Punjab Kesari](https://english.punjabkesari.com/india/2025/07/07/rfid-counters-set-up-to-track-amarnath-yatra-pilgrims-movement)
- Amarnath 2025: solo travel banned; pilgrims had to move in government-supervised convoys from 1 July — [India TV](https://www.indiatvnews.com/jammu-and-kashmir/amarnath-yatra-2025-solo-travel-banned-security-convoys-mandatory-key-rule-changes-for-pilgrims-2025-06-27-996503)
- Vaishno Devi: free RFID yatra access cards track pilgrims in real time. Flow is checked "as per the holding capacity of the track, area and location". Only pilgrims with valid RFID cards may proceed; handheld scanners were recommended — [The Statesman](https://www.thestatesman.com/india/lg-sinha-orders-introduction-rfid-tracking-crowd-management-vaishnodevi-1503035742.html); [Tribune](https://www.tribuneindia.com/news/j-k/radio-frequency-identity-cards-in-offing-for-pilgrims-visiting-mata-vaishno-devi-shrine-in-jammu-and-kashmir-397085/amp)
- Vaishno Devi stampede, 1 January 2022: 12 dead, 16 injured. Afterward the LG ordered 100% online booking and RFID tracking — [The Statesman](https://www.thestatesman.com/india/lg-sinha-orders-introduction-rfid-tracking-crowd-management-vaishnodevi-1503035742.html)

**Registration / booking caps**
- Vaishno Devi: 35,000 pilgrims allowed on 31 Dec and 1 Jan, against an NGT cap of 50,000/day — [Tribune](https://www.tribuneindia.com/news/j-k/vaishno-devi-shrine-board-gears-up-to-meet-new-year-rush-of-pilgrims-573247)
- A 250 m Sky Walk (queue management system), 20 ft above the track, opened at Bhawan in October 2023 to separate flows — [Wikipedia: SMVDSB](https://en.wikipedia.org/wiki/Shri_Mata_Vaishno_Devi_Shrine_Board) (secondary)

### Inferences
- **Inference:** RFID reader gates give a cheap, robust segment count: occupancy(segment) = entries − exits between two readers. Divided by usable segment area, this gives a density (persons/m²). This is a better primary signal for narrow mountain trails than CCTV, which needs line-of-sight, light and power.
- **Inference:** For a prototype, CCTV density should be one input, not the only one. Use CSRNet (or a similar density-map model) on sample frames from ShanghaiTech/JHU-Crowd. Convert the count to persons/m² with a per-camera ground-area calibration (a homography (a 2D mapping from image pixels to ground coordinates)).
- **Inference:** YOLO-style detectors (draw a box per person) under-count in dense scenes because heads overlap. Density-map models (CSRNet) are the standard choice above roughly 2–3 persons/m². This is consistent with why benchmark datasets of dense scenes use density-map methods, but no head-to-head source was fetched.
- **Estimate:** A dense-scene MAE of ~68 on ShanghaiTech A (average ~500 people per image per common descriptions, not verified here) means ~10–15% count error. That is enough to place a segment in a Fruin band, but not enough to separate 4 from 5 persons/m² reliably. Use hysteresis (different thresholds for raising and clearing a level) to avoid flapping.
- **Inference:** Mobile-network (telecom CDR/tower) data, Wi-Fi/BLE probes and drones are not realistic for a student prototype. They need operator agreements, privacy approvals (DPDP Act 2023 context) or DGCA drone permits. Simulate them or omit them.

### Gaps
- No source fetched on telecom-data crowd estimation in India, Wi-Fi/BLE sensing accuracy, or drone use at Amarnath/Kumbh 2025.
- No published accuracy figures for the deployed Kumbh/Amarnath/Vaishno Devi systems (only the 95% target).
- No per-unit cost found for RFID readers, AI cameras or analytics licences.
- Vaishno Devi RFID scanning points along the track and their reporting interval were not found.

## 2. Crowd-crush risk science and thresholds

### Takeaway
Risk rises non-linearly with density. Flow peaks near a critical density of about 2–3 persons/m² (Still) and drops above it. Above roughly 6 persons/m², crowd turbulence (Helbing) can occur. Stop-and-go waves have preceded fatal turbulence by about 20 minutes in the 2006 Hajj data. Thresholds are site- and crowd-specific, so a prototype should use configurable bands, not hard-coded constants.

### Cited Findings
- Still: "As density increased flow increases, but only until critical density is reached (2-3 people per square metre)." Above critical density, flow rate drops. "This critical density can be different for different events/crowds." Flow is also a function of crowd order — [G. Keith Still, Fruin page](https://gkstill.com/Support/crowd-flow/fruin/Fruin1.html)
- Still also notes that Fruin measured in a pedestrian street setting, and modern stadiums exceed Fruin's observed densities — [Still PhD, Crowd Dynamics](https://gkstill.com/CV/PhD/CrowdDynamics.html); density–flow page at [gkstill.com](https://gkstill.com/Support/crowd-flow/DensityFlow.html)
- Fruin's Levels of Service (LOS A–F) were defined as area per person (ft²/person) and have been converted to persons/m² by later users — [Copenhagen BLM safety report](https://legacy.mm.dk/misc/BLM-Copenhagen-2020-V1.0.pdf). Still's thesis labels LOS D at about 1 person/m² in one illustration — [Still PhD Chapter 3](https://gkstill.com/CV/PhD/Chapter3.html)
- Flow rates tend to drop from about 3 persons/m² (citing Still) — [Copenhagen BLM report](https://legacy.mm.dk/misc/BLM-Copenhagen-2020-V1.0.pdf)
- Helbing, Johansson, Al-Abideen (2007), "The Dynamics of Crowd Disasters: An Empirical Study", Phys. Rev. E 75, 046109: video of the January 2006 Mina/Hajj disaster shows two sudden transitions, laminar → stop-and-go → "turbulent" flow, with pressure releases like earthquakes — [arXiv physics/0701203](https://arxiv.org/abs/physics/0701203)
- Deaths began about 10 minutes after turbulence started and about 30 minutes after stop-and-go started — [Physics World](https://physicsworld.com/a/crowd-turbulence-has-deadly-consequences/) (secondary summary)
- Local densities above 6 persons/m² drastically reduce crowd flow — secondary summary, not checked against the paper — [Physics World](https://physicsworld.com/a/crowd-turbulence-has-deadly-consequences/); Scroll.in also gives ~6/m² as the turbulence threshold and says turbulence killed 362 pilgrims in Mecca in 2006 — [Scroll.in](https://scroll.in/article/915498/scroll_in)
- Helbing & Mukerji (2012), Love Parade Duisburg 2010 (21 dead): deaths came from a domino effect of "crowd turbulence"/"crowd quake", not panic. At high density, forces pass body to body as in granular material. They propose a new scale for assessing the criticality of crowd conditions for earlier prevention — [arXiv 1206.5856](https://arxiv.org/abs/1206.5856v1); [EPJ Data Science summary](https://www.epj.org/113-epj-ds/537-epj-data-science-countering-crowd-control-collapse)
- Video analysis can move "from crowd dynamics to crowd safety" (Johansson, Helbing et al.) — [arXiv 0810.4590](https://arxiv.org/pdf/0810.4590)

### Inferences
- **Inference (prototype risk bands, configurable):** green < 2 p/m² (free flow); amber 2–4 p/m² (at or past critical density, flow falling); red 4–6 p/m² (congested, stop-and-go likely); black ≥ 6 p/m² (turbulence possible). The 2–3 and 6 numbers are sourced above; the 4 cut-off is an interpolation.
- **Inference:** Density alone misses dynamics. Add a second feature: a stop-and-go indicator from the time series of RFID gate rates or optical-flow speed (variance of speed rising while mean speed falls). Helbing's "crowd pressure" is commonly defined as density × local velocity variance; this definition and any numeric threshold (often quoted as 0.02 s⁻²) were **not** verified in this session.
- **Inference (fundamental diagram):** Flow q = density ρ × speed v. Since v falls as ρ rises, q has a peak (capacity) near critical density. A trail segment's safe inflow is about capacity × usable width. If measured inflow at the upstream gate exceeds downstream outflow for several minutes, occupancy grows; this is an early warning that needs no camera.
- **Inference:** Combined segment risk for YatraKavach can be R = max(crowd_level, hazard_level) with an escalation rule when both are ≥ amber (e.g., crowded segment + landslide/flash-flood watch → red), because the danger of a hazard depends on how many people are exposed and how fast they can leave.

### Gaps
- Fruin's full LOS A–F table in persons/m² was not retrieved (the page shows it only as an image). Primary sources: Fruin, *Pedestrian Planning and Design* (1971/1987); Still, *Introduction to Crowd Science* (2014).
- The exact Helbing crowd-pressure formula and threshold were not verified from the PDF.
- No Indian standard (NDMA) numeric density threshold was found. NDMA's 2014 guide "Managing Crowds at Events and Venues of Mass Gathering" exists but was not fetched in this session.

## 3. Emergency routing on trails and roads

### Takeaway
pgRouting on PostGIS with OSM data is the most flexible fit: closed or high-risk segments can be removed or penalised in the edges SQL per query, and "nearest shelter/medical post" maps to one-to-many shortest paths with points. Request-time avoid polygons exist in openrouteservice and HERE; Valhalla and GraphHopper behaviour was not confirmed in this session.

### Cited Findings
- `pgr_withPointsCost` uses Dijkstra and returns only the aggregate cost of shortest paths, not the path. Graph vertices are positive ids; points from `points_sql` are negative ids — [pgRouting docs 3.6](https://docs.pgrouting.org/3.6/en/pgr_withPointsCost.html)
- Only edges with positive cost are processed — [pgRouting docs 3.5](https://docs.pgrouting.org/3.5/en/pgr_withPointsCost.html)
- The docs show `pgr_findCloseEdges` inside Points SQL to snap locations to the graph, and warn that being close to the graph does not mean a shorter route — [pgRouting docs 3.6](https://docs.pgrouting.org/3.6/en/pgr_withPointsCost.html)
- `pgr_withPoints` returns route details (seq, node, edge, cost, agg_cost) for one-to-many and other combinations — [pgRouting 3.4 pgr_withPoints](https://access.crunchydata.com/documentation/pgrouting/3.4.2/pgr_withPoints.html)
- `pgr_withPointsDD` (proposed) returns all nodes and points within a given cost of a start point (an isochrone (area reachable within a time/distance)) — [pgRouting 3.4 pgr_withPointsDD](https://access.crunchydata.com/documentation/pgrouting/3.4.2/pgr_withPointsDD.html)
- Column names changed: 3.x uses `start_pid/end_pid`, 4.0 uses `start_vid/end_vid` — [pgRouting 4.0 docs](https://docs.pgrouting.org/4.0/en/pgr_withPointsCost.html)
- openrouteservice directions accept `options.avoid_polygons` as GeoJSON Polygon/MultiPolygon; malformed values give HTTP 400 — [ORS forum](https://ask.openrouteservice.org/t/is-there-a-way-to-exclude-a-rectangle-or-any-other-shape-area-from-the-routing/3298/5)
- HERE Routing API accepts up to 20 avoid polygons per request — [HERE blog](https://www.here.com/learn/blog/routing-supports-polygons-for-avoid-areas)

### Inferences
- **Inference (pattern):** Keep a `segment_status` table (segment_id, closed bool, risk_level). Edges SQL: `SELECT id, source, target, CASE WHEN s.closed THEN -1 ELSE length_m * penalty(s.risk_level) END AS cost ...`. Negative cost removes the edge; risk penalty discourages but allows it. Test before relying on it; the docs confirm only the "positive cost" rule.
- **Inference:** Nearest shelter/medical post = `pgr_withPointsCost` (or `pgr_dijkstraCost`) from the pilgrim's snapped point to all facility vertices, then `ORDER BY agg_cost LIMIT 1`. For many pilgrims, run reverse (many-to-one) from each facility.
- **Inference:** OSRM pre-processes the graph (contraction hierarchies), so per-request closures are not its strength; it needs re-processing or traffic-update files. Valhalla is understood to support `exclude_polygons`/`exclude_locations` and pedestrian hiking options; GraphHopper supports custom models with area blocks. None of these were verified here (the Valhalla docs page redirected). For a dynamic-closure prototype, pgRouting is the safer choice.
- **Inference:** OSM coverage of pilgrim trails (Baltal–Holy Cave, Pahalgam–Chandanwari–Sheshnag–Panchtarni, Katra–Bhawan) should be checked in the OSM data before relying on it; shelter, langar, medical camp and camp-site points will probably need manual digitising from SASB/SMVDSB maps.

### Gaps
- Valhalla, GraphHopper and OSRM closure docs were not retrieved (redirect / no result).
- Completeness of OSM trail geometry for Amarnath and Vaishno Devi routes was not checked.

## 4. Alert dissemination in India (CAP, Sachet, Cell Broadcast, SMS, WhatsApp, IVR)

### Takeaway
India's public alerting stack is SACHET, a CAP-based integrated alert system built by C-DOT and run with NDMA. It is live in all 36 states/UTs for geo-targeted SMS. A Cell Broadcast System (CBS) was launched nationally on 2 May 2026 on top of it. A prototype cannot inject into SACHET or CBS. It should emit valid CAP 1.2 XML and deliver through commercial channels (WhatsApp Cloud API test number, DLT-registered SMS via MSG91/Twilio/Exotel, IVR), and can consume SACHET's public feed.

### Cited Findings
- SACHET is C-DOT's integrated alert system based on CAP as recommended by ITU. It operates in all 36 states/UTs and sends disaster alerts via SMS to mobile users in geo-targeted areas — [iasgyan](https://www.iasgyan.in/daily-current-affairs/cell-broadcasting-system) (secondary)
- C-DOT's CAP platform integrates multiple stakeholders and channels: SMS, Cell Broadcast, mobile app, TV, radio, social media, RSS feed, browser notification and satellite — [C-DOT brochure (PDF)](https://cdot.in/cdotweb/assets/docs/products/dms/cap.pdf)
- CBS sends alerts from a central platform to selected cell towers (BTS), which broadcast to every handset in range, and does not depend on congested SMS delivery — [ETV Bharat](https://www.etvbharat.com/en/bharat/ndma-tests-cell-broadcast-message-to-alert-citizens-on-severe-disaster-enn26050201915)
- CBS was developed by DoT with NDMA, with C-DOT as R&D centre. It integrates SACHET with Cell Broadcast for real-time, geo-targeted alerts — [OpenGov Asia](https://opengovasia.com/india-launches-cell-broadcast-system-to-strengthen-nationwide-disaster-alerts/)
- PIB pre-release (30 Apr 2026): the Home Minister and Communications Minister to launch nationwide mobile-based disaster communication systems on 2 May 2026 — [tele.net](https://tele.net.in/union-home-minister-along-with-communications-minister-to-launch-nationwide-mobile-based-disaster-communication-systems/)
- NDMA ran a nationwide CBS test on 2 May 2026; the test text said recipients might get it multiple times and no action was needed — [ETV Bharat](https://www.etvbharat.com/en/bharat/ndma-tests-cell-broadcast-message-to-alert-citizens-on-severe-disaster-enn26050201915)
- Test messages reach only devices where CB test channels are enabled — [OpenGov Asia](https://opengovasia.com/india-launches-cell-broadcast-system-to-strengthen-nationwide-disaster-alerts/)
- SACHET SMS volume figures conflict: ~134 billion vs 6,899 crore (~69 billion) — [OpenGov Asia](https://opengovasia.com/india-launches-cell-broadcast-system-to-strengthen-nationwide-disaster-alerts/); [TaxGuru](https://taxguru.in/corporate-law/india-deploys-mobile-alert-system-due-rising-disaster-preparedness.html). Unresolved.
- CAP 1.2 = ITU-T X.1303bis (approved 2014-03), equivalent to OASIS CAP 1.2; ITU gives XML schema and ASN.1 — [ITU work item](https://www.itu.int/ITU-T/workprog/wp_item.aspx?isn=8066); [ITU ASN.1 module](https://www.itu.int/wftp3/Public/t/fl/itu-t/x/x1303bis/2014/CAP-1-2.html)
- CAP `urgency`: Immediate, Expected, Future, Past, Unknown. `severity`: Extreme, Severe, Moderate, Minor, Unknown. `certainty`: likely, observed, possible, unknown, unlikely (schema enum; WMO slides say "Very Likely", which does not match the schema) — [ITU ASN.1 module](https://www.itu.int/wftp3/Public/t/fl/itu-t/x/x1303bis/2014/CAP-1-2.html); [WMO CAP slides](https://old.wmo.int/extranet/pages/prog/drr/events/Barbados/Pres/3-WMO-CAP.pdf)
- ITU example: severe thunderstorm warning with Immediate / Severe / Observed — [ITU X.1303bis example](https://www.itu.int/ITU-T/formal-language/itu-t/x/x1303bis/2014/x1303bis-AppI.3-Earthquake%20report-Update%20message.html)
- SMS in India: TRAI DLT (distributed-ledger registry run by telecom operators) registration is required. Steps: entity registration (gives a PE ID), sender ID/header registration, content template approval; "Service Implicit" templates cover transactional content. SMS is delivered only if the template is DLT-approved and the template ID is passed with each SMS — [MSG91 DLT help](https://msg91.com/help/dlt-registration-in-india); [MSG91 step-by-step](https://msg91.com/help/dlt-registration-in-india/step-by-step-guide-to-implement-dlt-in-sms); [WebEngage TRAI DLT](https://docs.webengage.com/docs/trai-sms-dlt-regulations-india)
- WhatsApp Cloud API: Meta's test setup allows up to 5 recipient numbers, each verified by a code; the pre-approved `hello_world` template is the first test — [Meta developer docs](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/)
- Test numbers can message only the added test recipients, and templates made on a test number cannot be reused on a production number — [WANotifier help](https://help.wanotifier.com/en/article/test-phone-number-limitations-kt0ly2/)
- India utility-message pricing (third-party, conflicting): ₹0.145 per utility message — [Eazybe](https://help.eazybe.com/es/waba/pricing); ~₹0.115 outside the 24-hour window, free inside it — [WhAutomate](https://whautomate.com/whatsapp-business-api-pricing-india). Check Meta's official pricing page.

### Inferences
- **Inference:** The prototype should generate CAP 1.2 XML per approved alert (identifier, sender, sent, status=`Exercise` or `Test` during demos, msgType, scope, info blocks per language, area as polygon of affected segments). This keeps it compatible in principle with SACHET-style ingest and shows standards awareness.
- **Inference:** SACHET publishes a public CAP RSS feed (C-DOT lists "RSS Feed" as a channel). A prototype can poll it to import official IMD/state alerts as hazard inputs. The exact feed URL was not verified in this session.
- **Inference:** Demo channels in order of setup effort: (1) in-app push / web dashboard; (2) WhatsApp Cloud API test number to ≤5 team phones; (3) SMS via Twilio trial (international route; Indian delivery may still hit DLT rules) or MSG91 after DLT registration, which needs a registered entity and takes time; (4) IVR via Exotel/Twilio Voice with pre-recorded Hindi/Urdu/Dogri/Kashmiri audio. Cell broadcast and sirens should be simulated (log + UI), since only government and operators can trigger them.
- **Inference:** Using CAP `status=Exercise` and an obvious "TEST/DRILL" prefix on every demo message prevents real-world confusion.

### Gaps
- No primary NDMA/PIB page was fetched for SACHET API access, onboarding of third-party alert originators, or the public feed URL.
- No source fetched on Exotel/Twilio IVR language support or pricing in India, or Twilio trial delivery to Indian numbers under DLT.
- No source fetched on sirens at Amarnath/Vaishno Devi.

## 5. Human-in-the-loop alert approval, SOPs, alert fatigue, ICCC model

### Takeaway
Indian mass-gathering command is centred on ICCCs (four at Kumbh 2025) where AI raises threshold alerts and officers decide. The 2025 Kumbh stampede shows that detection without fast, clear human action is not enough. A prototype should make the AI propose and a human approve, with two-person approval for public broadcast, full audit logs and threshold review after events.

### Cited Findings
- Kumbh 2025: four ICCCs monitored the fair; AI flagged ghat density and raised alerts against pre-set thresholds — [Drishti IAS](https://www.drishtiias.com/state-pcs-current-affairs/ai-in-maha-kumbh-2025); [The Federal](https://thefederal.com/category/states/north/uttar-pradesh/ai-surveillance-to-enhance-kumbh-mela-pilgrim-safety-officials-173089)
- After the 29 Jan 2025 stampede, the ICCC officer said AI data would be analysed after the congregation and thresholds might be revised — [The Federal](https://thefederal.com/category/states/north/uttar-pradesh/ai-surveillance-to-enhance-kumbh-mela-pilgrim-safety-officials-173089)
- Stop-and-go flow preceded deaths by about 30 minutes in the 2006 Hajj disaster, giving a usable warning window — [Physics World](https://physicsworld.com/a/crowd-turbulence-has-deadly-consequences/)
- Vaishno Devi uses real-time MIS reporting with a 700+ camera network, i.e., a command-centre model — [Tribune](https://www.tribuneindia.com/news/j-k/vaishno-devi-shrine-sets-up-dedicated-network-of-over-700-cameras-for-e-surveillance-474077)
- NDMA's CBS test text warned that people might receive the message multiple times and no action was needed — an example of explicit test labelling — [ETV Bharat](https://www.etvbharat.com/en/bharat/ndma-tests-cell-broadcast-message-to-alert-citizens-on-severe-disaster-enn26050201915)

### Inferences
- **Inference (workflow):** state machine `DETECTED → PROPOSED (auto-drafted CAP + message per language) → APPROVED_1 (operator) → APPROVED_2 (supervisor; required for severity ≥ Severe or public broadcast) → SENT → ACKED/UPDATED → CANCELLED/EXPIRED`. Use CAP `msgType` Alert/Update/Cancel so corrections reference the original.
- **Inference:** Two-person rule should be bypassable only with a logged "break-glass" reason, so approval delay never blocks a life-safety alert (the Hajj data suggest a 10–30 minute window).
- **Inference (alert fatigue):** Reduce false alarms with hysteresis, a minimum dwell time (e.g., density above band for ≥ N minutes), multi-sensor confirmation (RFID occupancy and camera agree), and rate limits per segment. Track precision of past alerts on the dashboard.
- **Inference (audit):** Append-only audit table: who, when, inputs snapshot (sensor values, model version, thresholds), message text per language, channels, delivery receipts. This also supports the post-event threshold review the Kumbh ICCC described.

### Gaps
- No primary NDMA SOP or ICCC SOP document on alert approval chains was retrieved. NDMA mass-gathering guidelines (2014) and MoHUA Smart Cities ICCC docs should be checked.
- No WHO/IFRC early-warning guidance was fetched in this session (e.g., the UN "Early Warnings for All" four pillars).
- No measured data on alert fatigue in Indian SMS alerting.

## 6. Multilingual / low-literacy alert design and offline-first apps

### Takeaway
Pilgrims come from all over India, while local staff in J&K speak Hindi, Urdu, Dogri and Kashmiri. CAP supports multiple language `info` blocks, and C-DOT's platform lists many channels. Few India-specific design sources were found, so most design guidance below is inference.

### Cited Findings
- CAP allows multiple `info` blocks; the language-tagged structure is part of the CAP 1.2 schema — [ITU ASN.1 module](https://www.itu.int/wftp3/Public/t/fl/itu-t/x/x1303bis/2014/CAP-1-2.html)
- C-DOT's alert platform spans SMS, cell broadcast, mobile app, TV, radio, social media, RSS, browser notification and satellite — [C-DOT brochure](https://cdot.in/cdotweb/assets/docs/products/dms/cap.pdf)
- Cell broadcast reaches all handsets in range without per-number SMS delivery, which helps in congested networks — [ETV Bharat](https://www.etvbharat.com/en/bharat/ndma-tests-cell-broadcast-message-to-alert-citizens-on-severe-disaster-enn26050201915)
- Amarnath pilgrims hold RFID cards and travel in convoys, so group leaders and convoy staff are a reachable relay layer — [J&K SASB](https://jksasb.nic.in/rfid.html); [India TV](https://www.indiatvnews.com/jammu-and-kashmir/amarnath-yatra-2025-solo-travel-banned-security-convoys-mandatory-key-rule-changes-for-pilgrims-2025-06-27-996503)

### Inferences
- **Inference (message design):** Short, action-first text: WHAT (hazard) – WHERE (segment name + landmark) – DO (one action: "stop at Sangam camp", "go back to Baltal") – UNTIL (time). Add a pictogram/colour code and a voice version for low-literacy users.
- **Inference (languages):** Pre-approve templates per language (also needed for DLT and WhatsApp template rules) instead of machine-translating at send time. Hindi + English minimum; add Urdu, Dogri, Kashmiri, Punjabi, plus pilgrim-origin languages from registration data. Have native speakers check them.
- **Inference (offline-first app):** Cache route graph, segment polygons, shelter/medical points and pre-recorded audio on the phone. Store last-known alerts locally; sync deltas when signal appears; fall back to SMS when data is down. Cell broadcast needs no app and no data, which makes it the strongest last-mile channel in valleys with weak data signal.
- **Inference:** Use RFID gate events and booking/registration data to target alerts to pilgrims known to be on or heading to a segment, instead of only geofencing by phone location.

### Gaps
- No India-specific research was retrieved on alert comprehension in low-literacy pilgrims, or on mobile connectivity along the Amarnath/Vaishno Devi tracks.
- Cell-broadcast language support in India (which scripts/languages, character limits) was not confirmed.
- No source on IVR voice availability in Dogri or Kashmiri from commercial providers.
