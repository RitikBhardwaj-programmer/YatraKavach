# International best-practice systems and open-source components (landslide/flash-flood EWS and mass-gathering crowd management)

Scope: lessons for a student prototype ("YatraKavach") that warns pilgrims on J&K mountain routes per route segment and requires an officer to approve each alert. Research date: 23 Oct 2026. Labels: **[sourced]** = backed by the linked page; **[inference]** = my reasoning from sourced facts, not tested; **[estimate]** = own arithmetic. Claims that I could not verify this session are in the Gaps sections only.

## 1. Hong Kong GEO Landslip Warning System

### Takeaway
Hong Kong runs a territory-wide, rainfall-driven warning that is a *joint human decision* by the Hong Kong Observatory (HKO) and the Geotechnical Engineering Office (GEO), fed by a rain-gauge network, short-range rainfall forecasts and a rainfall-to-landslide-count correlation model. Since May 2024 it also has an area-specific "Special Landslip Advisory", which is the closest analogue to per-segment warnings.

### Cited Findings
- [sourced] The warning decision combines real-time rainfall, rainfall forecasts for the next few hours, the spatial distribution of slope features, and a rainfall-landslide correlation model. More than 120 automatic rain gauges send real-time data to the GEO control centre over the mobile phone network. — [HK Slope Safety: Landslip Warning System](https://ginfo.cedd.gov.hk/hkss/en/protection-against-landslide-emergency/landslip-warning-system/index.html)
- [sourced] The warning targets a high risk of *many* landslips from persistent heavy rain. A "Special Landslip Advisory" (introduced May 2024) names specific areas with higher risk when heavy rain persists locally but territory-wide risk is below warning level. — [HK Slope Safety](https://ginfo.cedd.gov.hk/hkss/en/protection-against-landslide-emergency/landslip-warning-system/index.html)
- [sourced] Dissemination: TV and radio broadcasts at regular intervals with precautionary advice; Slope Safety website; MyObservatory app; GEO social media. Government departments activate Emergency Control Centres. Updates continue until landslip likelihood drops. — [HK Slope Safety](https://ginfo.cedd.gov.hk/hkss/en/protection-against-landslide-emergency/landslip-warning-system/index.html)
- [sourced] The agency openly states the system has false alarms, and that sudden heavy rain can cause landslips before a warning is issued; isolated landslips can occur with no warning in force. — [HK Slope Safety](https://ginfo.cedd.gov.hk/hkss/en/protection-against-landslide-emergency/landslip-warning-system/index.html)
- [sourced] Landslip Warnings are issued by HKO in consultation with GEO when recorded and forecast rainfall meet prescribed criteria; decisions to issue or cancel are joint. The Landslip Warning is separate from the Amber/Red/Black Rainstorm Warnings. — [GEO Information Note IN 2025/18](https://www.cedd.gov.hk/filemanager/eng/content_454/IN_2025_18E.pdf)
- [sourced] Older GEO papers describe the core metric as rolling 24-hour rainfall, with the warning issued when the *predicted number of landslides* exceeded a threshold, then set at 15 (2004 figure; historical, may have changed). — [Yu et al. 2004, Recent advance in Landslip Warning System](https://ginfo.cedd.gov.hk/hkss/filemanager/common/publications-resources/list-of-technical-papers/304_Yu%20et%20al%20(2004)_Recent%20advance%20in%20Landslip%20Warning%20System.pdf); see also [Chan et al. 2003](https://ginfo.cedd.gov.hk/hkss/filemanager/common/publications-resources/list-of-technical-papers/303_Chan%20et%20al%20(2003)_Recent%20developments%20in%20the%20Landslip%20Warning%20System%20in%20Hong%20Kong.pdf)

### Inferences
- [inference] Pattern to copy: model output is *decision support*; the warning itself is a human (two-agency) decision. This maps directly to YatraKavach's "officer approves alert" requirement.
- [inference] Two-tier design (territory-wide warning + area-specific advisory) fits a route: a route-wide "Warning" plus segment-level "Advisories".
- [inference] Using "expected number of landslides" rather than raw rainfall as the trigger is a useful abstraction: per segment, the score can be "probability of a slide on this segment in the next N hours".
- [inference] Publishing a candid limitations statement (false alarms, missed sudden events) is good practice for a student prototype's UI and documentation.

### Gaps
- The current numeric rainfall criteria were not found on official pages; the "15 landslides" threshold is from 2004.
- The 1977 start year was not confirmed on the pages fetched (the brief states it; the official page fetched does not give a start year).

## 2. Other landslide early warning systems (Italy, USGS/NWS, Norway, Japan, Nepal, Sri Lanka) and which use per-area/per-grid risk

### Takeaway
Japan (5 km grid mesh, soil water index + 60-min rain) and Norway (regional daily levels, 4 colours, 3-day horizon, forecaster tool xgeo) are the best grid/region models; USGS/NWS shows short-duration (15-min) intensity thresholds for post-fire debris flows; Sri Lanka NBRO shows a simple, communicable 24-hour rainfall ladder (75/100/150 mm). All use colour-level ladders with human forecasters in the loop.

### Cited Findings
**Japan (JMA)**
- [sourced] JMA's sediment-disaster early warning sets criteria for debris flows and multiple slope failures using 60-minute cumulative rainfall and the Soil Water Index (SWI) in every 5 km grid mesh over Japan. — [Geotechnics 2023 via DOAJ](https://doaj.org/article/12fa7c063b384fa2bbf9e0c371e6763e); [JSECE study](https://jsece.or.jp/?p=3819)
- [sourced] SWI is computed with a tank model (a conceptual model that treats soil as stacked water tanks that fill and drain); tank parameters are unified nationally (granite parameters). The 2023 paper notes the system does not consider slope angle or geology. — [Geotechnics 2023 via DOAJ](https://doaj.org/article/12fa7c063b384fa2bbf9e0c371e6763e)
- [sourced] JMA issues Sediment Disaster Alerts jointly with prefectural sediment-control departments and Local Meteorological Observatories; criteria were lowered locally (Nara, Wakayama) after Typhoon Talas damage. — [JMA: Talas soil water index](https://www.jma.go.jp/jma/en/News/Talas_soil_water_index.html)
- [sourced] JMA displays risk distribution derived from the 5 km SWI at 1 km resolution in some prefectures. — [JMA notice 2019 (Japanese)](https://www.data.jma.go.jp/add/suishin/oshirase/pdf/20190919.pdf)

**Norway (NVE / varsom.no / xgeo)**
- [sourced] National landslide EWS launched 21 Oct 2013, run by NVE, MET Norway and the Norwegian Public Roads Administration; daily regional hazard assessments for mainland Norway using precipitation, snowmelt, groundwater, past events and regional susceptibility. Over 800 warnings in 10 years (30–120/yr); 92% yellow, 7% orange, 1% red. — [varsom.no 10-year article](https://www.varsom.no/en/news/general/the-norwegian-landslide-early-warning-service-turns-10-years-old/)
- [sourced] Forecasters evaluate model outputs (discharge, snowmelt, soil water, exceeded landslide thresholds) in the web decision tool xgeo.no; the same colour scale (green/yellow/orange/red) is used for flood and landslide, with different thresholds; varsom.no shows levels for today and the next two days. — [Colleuille, WMO RA VI 2016](https://old.wmo.int/extranet/pages/prog/hwrp/RA6/documents/2016/session1/Colleuille_Norwegian_flood_landslide_hazard_forecasting_warning.pdf); [EGU2015-13384](https://opac.geologie.ac.at/ais312/dokumente/EGU/EGU2015-13384.pdf)
- [sourced] The road administration (NPRA) is a co-operator, so road networks are a direct user of the warnings. — [varsom.no](https://www.varsom.no/en/news/general/the-norwegian-landslide-early-warning-service-turns-10-years-old/)

**USA (USGS / NWS post-fire debris flows)**
- [sourced] USGS provides threshold guidance to NWS Los Angeles/Oxnard and San Diego offices, fed into NWS flash-flood monitoring; 15-minute rainfall intensity is the key predictor. USGS FlowAlert tracks when nearby gauges cross thresholds. — [Staley (USGS) slides](https://www.varsom.no/media/1444/3_usa_postfiredfwarning_staley_usgs.pdf); [USGS FlowAlert](https://www.usgs.gov/programs/landslide-hazards/flowalert)
- [sourced] Thresholds are regional and limited by short historical records; Arizona work found triggering intensities ~22 mm/h lower than older peak-intensity methods. — [USGS Pinal Fire thresholds](https://pubs.usgs.gov/publication/70208100)
- [sourced] NASA's LHASA repo also includes a post-fire debris-flow ("pfdf") component. — [nasa/lhasa](https://github.com/nasa/lhasa)

**Sri Lanka (NBRO)**
- [sourced] NBRO issues district/divisional warnings in a 3-level ladder tied to 24-hour rainfall: Level 1 Yellow (>75 mm, "be watchful"), Level 2 Amber (>100 mm, "be ready to evacuate"), Level 3 Red (>150 mm, "evacuate if rain continues"). — [Newsfirst May 2020](https://www.newsfirst.lk/2020/05/15/nbro-issues-early-landslide-warning); [Newsfirst May 2023](https://english.newsfirst.lk/2023/5/7/early-landslide-warnings-issued-showers-over-75mm-expected-in-many-provinces); [Ada Derana](https://www.adaderana.lk/news.php?nid=63749) (news reports, not the official rulebook)

**Research context**
- [sourced] Rainfall thresholds world-wide produce many false alarms; soil moisture data can reduce them. — [TU Delft: Soil moisture can improve shallow landslide forecasting](https://research.tudelft.nl/en/publications/soil-moisture-information-can-improve-shallow-landslide-forecasti)
- [sourced] A 2025 preprint states no operational example yet models landslide *impact* spatially at high temporal resolution. — [EGUsphere 2025-4940](https://egusphere.copernicus.org/preprints/2025/egusphere-2025-4940/egusphere-2025-4940.pdf)
- [sourced] International practitioners network: LandAware (workshops Oslo 2016, Perugia 2020). — [varsom.no](https://www.varsom.no/en/news/general/the-norwegian-landslide-early-warning-service-turns-10-years-old/)

### Inferences
- [inference] Per-grid/per-area systems most similar to route segments: Japan (5 km mesh, shown at 1 km), Norway (regions), HK Special Landslip Advisory (named areas), NBRO (districts/divisions), LHASA (1 km global grid). A route segment can inherit the max (or weighted) value of the grid cells it crosses.
- [inference] A prototype can combine two indicators like JMA: a short-window intensity (60-min, or 15-min for debris flow) and a "memory" indicator (antecedent / soil-water proxy such as 3–7-day accumulated rain). This is cheap to compute from Open-Meteo hourly data.
- [inference] Sri Lanka's ladder is the simplest explainable baseline for a demo; its thresholds are Sri Lankan and must not be presented as valid for the Himalaya without calibration.
- [inference] Norway's xgeo pattern (forecaster dashboard showing which thresholds are exceeded, then a human sets the level) is the right UI model for the officer-approval screen.
- [inference] Allow local lowering of thresholds after damage (JMA Talas example): segments recently hit by slides or fire could get a "sensitised" flag.

### Gaps
- Italy SANF (national rainfall-threshold system by CNR-IRPI): no source fetched this session; not verified.
- Nepal (DHM flood EWS, landslide efforts): no source fetched this session; not verified.
- Current official NBRO and JMA threshold tables were not retrieved; values above come from news and secondary papers.
- Norway's level definitions and false-alarm statistics were not found.

## 3. Hajj crowd management (Mina, Jamarat redesign, 2015 crush, current technology)

### Takeaway
Hajj shows that infrastructure redesign (one-way flow, more capacity) plus scheduled group dispatch (tafweej) matters more than detection alone; 2015 shows that crossing flows on approach roads remained the failure point even after the Jamarat redesign. Current Saudi practice is large CCTV networks with AI density analytics feeding a central operations function.

### Cited Findings
- [sourced] 2006: 362 died in a crush at Mina near the Jamarat Bridge; Foreign Policy attributes the trigger to pilgrims tripping over luggage at an entrance. — [Nature 2007](https://www.nature.com/news/2007/070115/full/news070115-13.html); [Foreign Policy 2015](https://foreignpolicy.com/2015/09/24/the-deadliest-stop-on-the-road-on-mecca/)
- [sourced] The redesign used crowd-dynamics modelling; basins changed from circular to oval; an electronic system directs pilgrim movement, and a warning system serves the tents. — [MEED: The model crowd](https://www.meed.com/the-model-crowd/); [AIP Inside Science](https://www.aip.org/inside-science/to-stone-the-devil-safely); [ArchDaily](https://www.archdaily.com/en/881030/how-meccas-jamarat-bridge-was-engineered-for-increased-crowd-safety)
- [sourced] 2015: two large flows met at right angles at a street corner in Mina on the way to the bridge. Death tolls conflict: Saudi official 769; AP count up to 2,411. Keith Still: too many potential intersections of crowd flows towards Jamarat. — [Foreign Policy](https://foreignpolicy.com/2015/09/24/the-deadliest-stop-on-the-road-on-mecca/) (AP figure as reported in search summaries; conflicting numbers)
- [sourced] Hajj 2026 Jamarat: 340 escalators and 682 digital surveillance cameras monitoring density; systems support tafweej (group dispatching) — operator Kidana (official claim). — [Arab News 2026](https://www.arabnews.com/node/2643925/amp)
- [sourced] SDAIA's Baseer and Sawaher platforms (with Ministry of Interior) use computer vision, thermal imaging and AI to track density and movement in real time at the Grand Mosque, Mina, Arafat and Muzdalifah; >5,000 cameras in Sawaher across 80+ sites; an envoy cites >15,000 cameras around Makkah for Hajj 2025 (~1.7 M pilgrims). Figures are official/diplomatic claims and may describe different scopes. — [Arab News: Saudi AI system](https://www.arabnews.com/node/2603629/saudi-arabia); [Arab News: Sri Lanka envoy](https://www.arabnews.com/node/2604563/amp); [Al Arabiya May 2026](https://english.alarabiya.net/News/saudi-arabia/2026/05/23/how-saudi-arabia-is-using-ai-to-transform-the-hajj-experience)
- [sourced] Academic crowd analytics for Masjid al-Haram: camera-based density, dominant motion and congestion localisation; substantial site customisation needed. — [Towards a Crowd Analytic Framework (arXiv 1709.05952)](https://ar5iv.arxiv.org/html/1709.05952)

### Inferences
- [inference] Tafweej = time-slot scheduling of groups. For J&K yatras this maps to segment-level "slot" or "hold at base camp" advice, which an officer approves, rather than only alerting.
- [inference] The 2015 lesson (crossing flows at junctions) suggests YatraKavach should model junctions/bottlenecks (bridges, narrow ledges, helipad queues) as their own segments with capacity attributes.
- [inference] A student prototype cannot replicate 5,000+ camera networks; a realistic scope is manual/periodic headcounts at checkpoints (RFID/registration counts) plus an optional single-camera density demo.

### Gaps
- Nusuk app / Nusuk smart card functions for crowd control: no source fetched this session.
- No public technical description of the Saudi crowd-monitoring centre architecture or density thresholds was found.

## 4. Other mass gatherings: Love Parade 2010, Itaewon 2022, Astroworld 2021

### Takeaway
Crushes are system failures (single entry/exit, counter-flows, no live density feedback). Seoul's post-Itaewon answer is a CCTV people-counting network with threshold-based alerts shared across city, police, fire and districts, with staged responses (separate entry/exit at "warning", trains skip station at "severe").

### Cited Findings
- [sourced] Love Parade (Duisburg, 2010): Helbing & Mukerji attribute deaths to "crowd turbulence"/"crowd quakes" from amplifying feedback and cascading effects, not deliberate pushing; forces add up unevenly at very high density; they propose a scale to assess criticality earlier. — [arXiv 1206.5856](https://arxiv.org/abs/1206.5856v1); [MIT Technology Review](https://www.technologyreview.com/2012/06/28/85633/crowd-quakes-were-a-key-factor-in-loveparade-disaster/)
- [sourced] The venue was a fenced former freight yard for ~250,000 people with a single dedicated entrance/exit route. — [MIT Technology Review](https://www.technologyreview.com/2012/06/28/85633/crowd-quakes-were-a-key-factor-in-loveparade-disaster/); follow-up eyewitness analysis: [Sieben & Seyfried 2023, arXiv 2303.03977](https://www.arxiv.org/pdf/2303.03977)
- [sourced] Seoul after Itaewon: AI "intelligent people-counting system" analyses CCTV to estimate people per unit area; above a threshold it shares data with districts, city, police and fire. 2023 plan: 909 cameras at 71 sites; later 1,086 cameras at 91 sites. Staged response in Itaewon: separate entry/exit routes at "warning" stage; trains may skip Itaewon Station at "severe congestion". City is building a crowd-density safety map and a "crowd accident prevention index". — [PS News: Seoul crowd alert system](https://psnews.com.au/south-korea-seoul-to-implement-crowd-alert-system/121528/); [Korea Herald](https://www.koreaherald.com/article/10600671); [SCMP](https://mcdn.i-scmp.com/news/asia/east-asia/article/3239180/ahead-itaewon-halloween-crush-anniversary-south-korea-tests-crowd-safety-plan-so-not-single-person)
- [sourced] WADEM case summary of the Itaewon crush. — [WADEM PDF](https://wadem.org/wp-content/uploads/2023/11/Itaewon-Crowd-Crush.pdf)
- [sourced] No source found on how accurate Seoul's system is at predicting crushes. — (absence noted from the same search results)

### Inferences
- [inference] Seoul's design is the closest blueprint for YatraKavach's crowd side: per-location density estimate → threshold levels → multi-agency notification → pre-defined staged action per level. Copy the "pre-agreed action per level" idea into the officer-approval screen (officer picks from templated actions).
- [inference] Love Parade argues for monitoring *flow and counter-flow* at single-route bottlenecks, which is exactly the geometry of a mountain pilgrim path.

### Gaps
- Astroworld 2021: no source fetched this session.
- Numeric density thresholds (people per m²) from Helbing or Still were not retrieved; widely quoted figures (e.g., danger above ~5–6 persons/m²) are unverified here.

## 5. Open-source components and their licences

### Takeaway
A full open stack exists: NASA LHASA (landslide nowcast, 1 km, Python), Open-Meteo (weather API; data CC BY 4.0, code AGPLv3, free tier non-commercial), WMO CAP Composer (Wagtail/Django, CAP 1.2 drafting–review–publish workflow, which already models approval), Sahana Eden (MIT, emergency-management framework), and DM-Count (MIT) / P2PNet for crowd counting. Licences must be checked per repo; several crowd-counting repos and datasets do not clearly state terms.

### Cited Findings
**Landslide model**
- [sourced] NASA LHASA 2.x (`github.com/nasa/lhasa`): machine-learning daily landslide probability at 30 arcsec (~1 km), real-time predictions usually four times a day (best effort); also population/road exposure and post-fire debris-flow basins. Python (`lhasa.py`, conda env), shell runner; needs static data zip, IMERG rainfall and NASA Earthdata login. Licence is in a `LICENSE.pdf` (text not read). — [nasa/lhasa](https://github.com/nasa/lhasa)
- [sourced] NASA catalogue lists LHASA v2.0 as "Open Source" release (NASA Open Source Agreement type not confirmed). — [NASA software GSC-18595-1](https://software.nasa.gov/software/GSC-18595-1)
- [sourced] Nowcast values are a hazard ranking, not calibrated probabilities for risk modelling; v2 replaced v1's decision tree with ML. — [Global Landslide Nowcast 2.0.0 README](https://acdisc.gsfc.nasa.gov/data/Landslide/Global_Landslide_Nowcast.2.0.0/doc/README.Global_Landslide_Nowcast_2.0.0.pdf)
- [sourced] LHASA data are on the AWS open data registry. — [AWS Registry: NASA Landslide Project](https://registry.opendata.aws/nasa-landslide-project/)

**Weather data**
- [sourced] Open-Meteo: API data under CC BY 4.0 (attribution required next to displayed data); free API only for non-commercial use, < 10,000 calls/day, 5,000/hour, 600/minute; source code AGPLv3. — [Open-Meteo terms](https://open-meteo.com/en/terms); [open-meteo.com](https://open-meteo.com/)

**Alerting (CAP)**
- [sourced] WMO CAP Composer: web app for producing OASIS CAP 1.2 alerts with drafting, review and publishing; RSS feed for downstream systems; developed by WMO and NORCAP; part of ClimWeb (`github.com/wmo-raf/nmhs-cms`), built on Wagtail; PyPI packages `cap-composer`, `capeditor`. — [CAP Composer docs](https://cap-composer.readthedocs.io/en/latest/); [ClimWeb Technology doc](https://github.com/wmo-raf/nmhs-cms/blob/main/docs/_docs/Technology.md)
- [sourced] Wagtail is a BSD-licensed Django CMS. — [PyPI wagtail](https://pypi.org/project/wagtail/6.1.2/)
- [sourced] Sahana Eden: open-source emergency-management framework (Python, web2py; PostgreSQL/MySQL), listed under MIT licence; Sahana ran CAP workshops. — [OSGeo Live: Sahana overview](https://live-archive.osgeo.org/7.9/en/overview/sahana_overview.html); [Sahana CAP workshop 2016](https://preparecenter.org/wp-content/uploads/2020/04/cap-workshop-2016-sahana-welcome_0.pdf)

**Crowd counting**
- [sourced] DM-Count (`cvlab-stonybrook/DM-Count`): MIT licence; pretrained models for UCF-QNRF, NWPU, ShanghaiTech A/B on Google Drive. — [DM-Count GitHub](https://github.com/cvlab-stonybrook/DM-Count)
- [sourced] P2PNet (`TencentYoutuResearch/CrowdCounting-P2PNet`): point-based counting and localisation; ships weights trained on ShanghaiTech A (MAE 51.96); licence file exists but terms not read. — [P2PNet GitHub](https://github.com/TencentYoutuResearch/CrowdCounting-P2PNet); [paper arXiv 2107.12746](https://arxiv.org/pdf/2107.12746)
- [sourced] CSRNet (dilated CNN density-map model, CVPR 2018); community PyTorch re-implementation exists; licence not established. — [CSRNet paper arXiv 1802.10062](https://arxiv.org/abs/1802.10062v1); [CSRNet-pytorch](https://github.com/CommissarMa/CSRNet-pytorch)

### Inferences
- [inference] Suggested prototype stack: PostGIS (route segments as LINESTRINGs) + FastAPI backend + MapLibre/Leaflet front end; risk score per segment from Open-Meteo hourly precipitation (+ optional LHASA tile sampled along each segment); CAP 1.2 XML as the alert format; officer approval as a status workflow (draft → approved → published) like CAP Composer.
- [inference] Using CAP 1.2 even in a prototype makes alerts interoperable with India's NDMA CAP-based SACHET platform (not verified this session) and with any CAP consumer.
- [inference] For a student demo, Open-Meteo's free tier is fine (non-commercial). A production deployment for a government would need the commercial plan or self-hosting (AGPLv3 obligations).
- [inference] DM-Count (MIT) is the safest crowd-counting choice licence-wise; but ShanghaiTech/UCF/NWPU dataset terms may be research-only, so weights trained on them may carry dataset restrictions.
- [inference] LHASA at 1 km and daily cadence is too coarse to be the sole trigger on a narrow mountain trail; use it as a background susceptibility layer, not as the alert trigger.

### Gaps
- Exact licences not verified this session: LHASA (`LICENSE.pdf`), P2PNet, CSRNet, ShanghaiTech dataset terms, CAP Composer repo licence, Ushahidi, GeoServer, MapLibre GL JS, Leaflet, OSRM, Valhalla, pgRouting, OpenStreetMap data (ODbL) — all need a check of each LICENSE file. (From general knowledge, unverified: OSM data ODbL; Leaflet BSD-2; MapLibre BSD-3; OSRM BSD-2; Valhalla MIT; pgRouting GPL-2; GeoServer GPL-2; Ushahidi AGPL-3.)
- Google CAP tools / CAP validator and FastAPI–PostGIS templates: no source fetched.

## 6. Design lessons: false vs missed alarms, impact-based forecasting, Early Warnings for All, four pillars

### Takeaway
UN "Early Warnings for All" (Executive Action Plan 2023–2027) frames an end-to-end, people-centred multi-hazard EWS on four pillars; WMO and Sendai push impact-based warnings. Rainfall-threshold systems are known to over-warn, and operators (HK, Norway) accept and publicly document false alarms, with a human forecaster making the final call.

### Cited Findings
- [sourced] Four pillars of people-centred end-to-end MHEWS: (1) disaster risk knowledge, (2) detection, monitoring, analysis and forecasting, (3) warning dissemination and communication, (4) preparedness and response capabilities. Co-led by WMO, UNDRR, ITU, IFRC; WMO leads pillar 2, UNDRR pillar 1. Executive Action Plan 2023–2027 targets universal coverage by 2027. — [WMO Bulletin: Overview of EW4All Executive Action Plan 2023–2027](https://wmo.int/resources/wmo-bulletin/wmo-bulletin-vol-72-1-2023/overview-of-early-warnings-all-executive-action-plan-2023-2027); [WMO and EW4All](https://wmo.int/site/wmo-and-early-warnings-all-initiative)
- [sourced] WMO, the Sendai Framework and EW4All encourage impact-based warnings (warning about what the weather will *do*, not only what it will *be*). — [EGUsphere 2025-4940](https://egusphere.copernicus.org/preprints/2025/egusphere-2025-4940/egusphere-2025-4940.pdf)
- [sourced] Rainfall thresholds produce many false alarms; soil moisture can reduce them. — [TU Delft](https://research.tudelft.nl/en/publications/soil-moisture-information-can-improve-shallow-landslide-forecasti)
- [sourced] Norway's warnings are 92% yellow / 7% orange / 1% red: a steep pyramid keeps high levels rare and meaningful. — [varsom.no](https://www.varsom.no/en/news/general/the-norwegian-landslide-early-warning-service-turns-10-years-old/)
- [sourced] HK publicly states its warning can give false alarms and can miss sudden events. — [HK Slope Safety](https://ginfo.cedd.gov.hk/hkss/en/protection-against-landslide-emergency/landslip-warning-system/index.html)

### Inferences
- [inference] Map the four pillars to YatraKavach modules: pillar 1 = segment susceptibility layer (slope, past slides, LHASA); pillar 2 = rainfall/crowd scoring engine; pillar 3 = CAP alerts to SMS/app/PA; pillar 4 = officer playbooks (hold, reroute, evacuate) with templated actions.
- [inference] Missed alarms cost lives; false alarms cost trust and compliance ("cry wolf"). For pilgrims, asymmetric costs justify a low threshold for *advisories* (low-cost action: "be watchful") and a higher threshold plus officer approval for *closures/evacuations* (high-cost action).
- [inference] Track a verification log (each alert: approved by whom, outcome, slide or no slide) so thresholds can be tuned; this is how HK, Norway and JMA improve over time.
- [inference] Impact-based framing per segment: risk = hazard (rain score) × exposure (pilgrims on segment now, from checkpoint counts) × vulnerability (segment type: ledge, bridge, open slope). This gives a natural reason why the same rain warns one segment and not another.

### Gaps
- The WMO "Guidelines on Multi-hazard Impact-based Forecast and Warning Services" (WMO-No. 1150) were not fetched; content not verified.
- EW4All 2026 progress status (coverage reached so far) not found.
- No quantitative study on cry-wolf effects specific to landslide warnings was retrieved.
