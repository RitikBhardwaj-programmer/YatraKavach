# Landslide, cloudburst and flash-flood EWS: architecture, models and open data for a 3-day J&K pilgrim-route prototype

Scope: how rainfall-induced landslide / flash-flood early-warning systems (EWS) are built, and what a student can build in 3 days as a risk score per 500 m route segment, updated every 15 minutes, for Amarnath, Vaishno Devi and Machail Mata routes. Research date: 2026-10-23. Labels used: **sourced** (link given), **estimate** (own arithmetic, assumptions stated), **inference** (reasoned, not tested).

## Q1. Models that turn rainfall into landslide risk (thresholds, antecedent rain, susceptibility x trigger, TRIGRS/SHALSTAB, ML)

### Takeaway
Operational regional EWS (GSI/LANDSLIP, NASA LHASA) combine a static susceptibility layer with a dynamic rainfall trigger: empirical intensity-duration (ID) or event-duration (ED) power-law thresholds plus antecedent rainfall, or an ML model (XGBoost in LHASA 2). For J&K the only published, region-specific thresholds found are Shah et al. 2024 (Kashmir valley and NH-44 Udhampur-Banihal), given as daily intensity and antecedent totals, not as a full I = aD^b curve in the abstract.

### Cited Findings
**General form and global thresholds**
- The standard empirical threshold is the power law I = α·D^β (I = mean rainfall intensity, mm/h; D = duration, h), first proposed by Caine (1980) — [Cepeda et al., EGU2009 abstract](https://meetingorganizer.copernicus.org/EGU2009/EGU2009-12290.pdf).
- Caine (1980) global threshold for shallow landslides/debris flows: I = 14.82·D^-0.39 (as reproduced in a later paper) — [arXiv 1306.1529](https://arxiv.org/pdf/1306.1529).
- Guzzetti et al. compiled a catalogue of 125 empirical thresholds (1970–2006) and proposed global thresholds; CNR-IRPI maintains a threshold database — [EGU2007 abstract](https://www.meetings.copernicus.org/www.cosis.net/abstracts/EGU2007/11113/EGU2007-J-11113.pdf); [CNR IRPI rainfall thresholds site](https://rainfallthresholds.irpi.cnr.it/extent_info.htm).

**J&K-specific (most relevant)**
- Shah, Bhat, Alam, Malik, Ali, Sheikh (2024), "Establishing the landslide-triggering rainfall thresholds for the Kashmir Himalaya", *Natural Hazards* 120(2):1319–1341, DOI 10.1007/s11069-023-06254-w. Method: empirical + automatic lower-bound algorithm; 220 landslides in the Kashmir valley and 190 along NH-44 (Jammu–Srinagar highway, Udhampur–Banihal stretch), 1990–2021 — [IDEAS/RePEc abstract](https://ideas.repec.org/a/spr/nathaz/v120y2024i2d10.1007_s11069-023-06254-w.html).
  - Daily intensity threshold: **9.4 mm/day (Kashmir valley)**, **14.35 mm/day (NH-44)** — same source.
  - Antecedent threshold: **55 mm over 15 days (valley)**, **53 mm over 20 days (NH-44)** — same source.
  - The paper states no prior rainfall-threshold study existed for the Kashmir Himalaya — same source.

**Uttarakhand / western-central Himalaya**
- Saha & Bera (2024), Garhwal (four districts): power-law threshold fitted to the lower boundary with quantile regression; reported as I = 1.38·D^-0.126; 0.45–0.50 mm/h over 48 h can trigger landslides — [DOAJ, Geosystems and Geoenvironment, Aug 2024](https://doaj.org/article/c56b9ddca08a4bc99ae1d3b804ba7145). Caution: the search-tool summary flagged the exponent form as unusual; verify against the full paper.
- Uttarkashi: 15-day antecedent rainfall of ~109 mm is associated with ~99% of landslides (EGU26 abstract); a separate Uttarkashi study uses an event-rainfall–duration (ED) model at several exceedance probabilities, validated on 2014 data — [EGU26-18511](https://meetingorganizer.copernicus.org/EGU26/EGU26-18511.html); [Springer s00531-023-02337-y](https://link.springer.com/article/10.1007/s00531-023-02337-y).
- A mid-Himalayan roadside study (57 events, 2017–2024) finds high landslide probability at ~1.75 mm/h over 48 h and notes extra destabilisation from moderate rain lasting >72 h — reported via search summary of [EGU26-18511](https://meetingorganizer.copernicus.org/EGU26/EGU26-18511.html) / [peeref 439852](https://peeref.com/works/439852) (attribution between these two not fully confirmed).
- Himachal Pradesh: a Dec 2025 review of 74 studies (2014–2024) finds Shimla, Mandi, Solan and Sirmaur have the highest landslide frequency and calls for real-time rainfall integration in EWS — [Cogent Engineering via DOAJ](https://doaj.org/article/d54b8cc4e3a8437ea35a782ca33a960c). 2023 monsoon: ~6,500 landslides mapped in Mandi and Kullu — [Durham repository](https://durham-repository.worktribe.com/output/3480848/investigation-of-landslides-triggered-by-unprecedented-rainfall-events-during-2023-monsoon-in-himachal-pradesh-india).

**Eastern Himalaya / Nepal comparators**
- Darjeeling–Kalimpong (NH-10): exceedance-probability ED threshold T5 = 26.92·D^0.44 (E in mm, D in h); a 48-h event of ~36.7 mm cumulative rain can trigger landslides (CTRL-T tool) — [NHESS 24, 465, 2024](https://nhess.copernicus.org/articles/24/465/2024/nhess-24-465-2024-metrics.html).
- Nepal Himalaya, Dahal & Hasegawa (2008): I = 73.90·D^-0.79 (mm/h, h), from 193 landslides; daily rainfall >144 mm gives high landslide risk — [dpnet.org.np PDF](https://dpnet.org.np/uploads/files/rainfall%20threshold2008%202021-09-17%2006-39-49.pdf).

**Physically based models**
- TRIGRS uses an infinite-slope model and computes a transient factor of safety per pixel; applied at Kalimpong (Dikshit et al. 2019), calibrated on a June–July 2015 storm with 18 landslides — [UTS repository](https://opus.lib.uts.edu.au/handle/10453/139458).
- A Delhi University thesis modified TRIGRS for spatially variable soil hydraulic parameters in Uttarakhand, validated at 9 landslide locations — [EGU22-273](https://meetingorganizer.copernicus.org/EGU22/EGU22-273.html).
- Of TRIGRS and SHALSTAB, only TRIGRS includes time (transient infiltration); SHALSTAB is steady-state — [Water 7(8) 4362, 2015](https://dx.doi.org/10.3390/w7084362).

**ML approach (LHASA 2)**
- NASA LHASA 2.0 uses XGBoost trained on global landslide inventories; inputs: snow mass, soil moisture, slope, distance to faults, lithologic strength, antecedent and current daily rainfall (IMERG), forecasts from GEOS-FP; ~1 km grid, 60°N–60°S; twice as likely to predict historical landslides as LHASA 1.1 at the same false-positive rate — [NASA software catalog GSC-18595-1](https://software.nasa.gov/software/GSC-18595-1); [NASA ARSET slides](https://appliedsciences.nasa.gov/sites/default/files/2024-05/Day2_P1.pdf).

### Inferences
- For a 3-day prototype, the defensible core model is: `risk = susceptibility_class(segment) × trigger_level(rain)`, where trigger_level compares (a) 24-h rainfall against Shah et al. 14.35 mm/day (Jammu side, Vaishno Devi / Machail lie in the Jammu division, closer to NH-44 conditions) or 9.4 mm/day (Kashmir side, Amarnath via Pahalgam/Baltal), and (b) 15–20-day antecedent rain against 55/53 mm. Plus a short-duration ID check using a Himalayan curve (e.g., Dahal & Hasegawa) as a conservative upper reference. (inference)
- Shah et al. thresholds are very low (a single wet monsoon day exceeds 14 mm). They will fire often; treat them as "watch" level and use higher multiples or ID curves for "warning". (inference)
- TRIGRS is not realistic in 3 days: it needs soil depth, cohesion, friction angle and hydraulic conductivity per pixel, which are not available for J&K routes. (inference)
- Running LHASA 2 locally is possible but outputs daily ~1 km rasters, which is coarser in time than 15 min; it is best used as a cross-check layer. (inference)

### Gaps
- Exact I = aD^b coefficients from Shah et al. 2024 (abstract gives only daily intensity and antecedent values); full paper not accessed.
- Guzzetti et al. (2008) global threshold coefficients not confirmed in fetched sources (commonly cited as I = 2.20·D^-0.44, unverified here).
- No Himachal-specific I–D equation found; Kanungo & Sharma (2014) Chamoli–Joshimath threshold not located.
- No SHALSTAB application to the Indian Himalaya found.

## Q2. GSI National Landslide Forecasting Centre (NLFC), regional landslide forecasting, and Bhukosh data access

### Takeaway
GSI's regional landslide early warning grew out of the UK-India LANDSLIP project: daily monsoon bulletins began in 2020 for Darjeeling and the Nilgiris, expanded to 21 districts in 8 states by 2025, with a national target of 2030. Bulletins use empirical rainfall thresholds and a 4-level (Low to Very High) 48-h outlook. GSI's 1:50k susceptibility map and ~91,000-landslide inventory are stated to be free to download from Bhukosh / NGDR, but file formats and WMS endpoints were not confirmed.

### Cited Findings
- Since the 2020 monsoon, GSI issues daily landslide forecast bulletins to district administrations in Darjeeling and the Nilgiris (pilot areas) — [MoES Rajya Sabha reply, Dec 2021](https://www.moes.gov.in/sites/default/files/RS-in-English-495-2-12-2021.pdf).
- LANDSLIP method: empirical rainfall thresholds; warning levels Low → Very High for landslide potential in the next 48 h; bulletin also summarises the medium-range forecast; distributed to district administrators — [LANDSLIP Knowledge Product: Landslide Forecast Bulletin (BGS/NERC, 2022)](https://nora.nerc.ac.uk/id/eprint/532238/1/LANDSLIP_KP_LandslideForecastBulletin_3March2022_OR21070.pdf); [LANDSLIP KP Landslide Forecasting](https://nora.nerc.ac.uk/532237/1/LANDSLIP_KP_LandslideForecasting_3March2022_OR21069.pdf).
- NLFC coverage grew from 16 districts in 6 states to 21 districts in 8 states (July 2025); target is a nationwide regional landslide EWS by 2030; operational bulletins for Rudraprayag (Uttarakhand) planned; AI-based forecasting model under research — [Business Standard / PTI, 20 Jul 2025](https://www.business-standard.com/india-news/gsi-plans-to-use-ai-to-develop-robust-landslide-forecasting-model-dg-125072000196_1.html); [The Week](https://www.theweek.in/wire-updates/national/2025/07/20/ces5-wb-gsi-landslide.html).
- Public channels: Bhusanket web portal and Bhooskhalan mobile app — [IAS Gyan](https://iasgyan.in/daily-current-affairs/bhusanket-web-portal); [Business Standard](https://www.business-standard.com/india-news/gsi-plans-to-use-ai-to-develop-robust-landslide-forecasting-model-dg-125072000196_1.html).
- National Landslide Susceptibility Mapping (NLSM) covers all landslide-prone hilly areas at 1:50,000; classes High / Moderate / Low; inventory ~91,000 historical landslides (33,904 field-validated); maps and inventory uploaded to NGDR and Bhukosh "for free download by all the stakeholders", also viewable in Bhusanket and Bhooskhalan — [MoES/PIB release](https://moes.gov.in/sites/default/files/PIB2158420.pdf); [Lok Sabha reply Sep 2020](https://www.moes.gov.in/sites/default/files/LS_EN_23092020_2169_0.pdf).
- A J&K survey reportedly classified 65% of landslide areas as low risk and 12% high risk — [Kashmir Despatch](https://kashmirdespatch.com/65-of-jks-landslide-areas-classified-as-low-risk-12-high-risk-survey/) (news source; not verified against GSI data).

### Inferences
- J&K is not confirmed among the NLFC bulletin districts in any source found, so a J&K route prototype fills a real gap. (inference)
- Practical access path: Bhukosh (bhukosh.gsi.gov.in) normally requires a free user login for downloads; vector layers are commonly offered as shapefile/KML. Not verified in this research; budget ~1 hour on day 1 to test, and keep a fallback (derive susceptibility from slope + NASA Global Landslide Catalog + OSM). (inference)

### Gaps
- Bhukosh download format, licence text, login steps, and any WMS/WFS endpoint: not confirmed by any fetched source.
- Whether any J&K district receives NLFC bulletins as of Oct 2026.
- Exact threshold values used in GSI bulletins.

## Q3. IoT / sensor EWS designs (Amrita Munnar, IIT Mandi): architecture and cost

### Takeaway
Two Indian reference designs exist: Amrita's multi-sensor wireless sensor network (WSN) at Munnar (since 2009, ~25 nodes, two-layer hierarchy, real evacuation warning in 2009) and IIT Mandi's low-cost sub-surface IoT nodes (~Rs 11,000 install + ~Rs 5,000/yr, solar, SMS alerts, 13–15+ sites in Himachal). Neither is replicable physically in 3 days; a prototype should simulate a sensor feed.

### Cited Findings
- Amrita WSN, Munnar (Idukki, Kerala): ~7 acres, ~25 nodes in a two-layer hierarchy; issued a 2009 warning that led to state-ordered evacuations — [Amrita landslide monitoring page](https://www.amrita.edu/center/awna/research/landslide-monitoring/); [Amrita news](https://www.amrita.edu/news/amritawna-secures-multi-crore-funding-from-ministry-to-deploy-wsns-for-landslide-detection/).
- Amrita sensor suite: pore-pressure sensors (piezometers), geophones, tilt meters, inclinometers, strain gauges, moisture sensors, rain gauges; MoES-funded upgrade to low-cost "intelligent wireless probes" feeding a central analysis centre — [Amrita news](https://www.amrita.edu/news/amritawna-secures-multi-crore-funding-from-ministry-to-deploy-wsns-for-landslide-detection/).
- Amrita wireless geophone network detects landslide initiation and localises it from surface-wave travel-time differences — [Amrita publication](https://www.amrita.edu/publication/wireless-geopbone-network-for-remote-monitoring-and-detection-of-landslides/).
- BGS-Amrita added electrical resistivity tomography on the Munnar slope — [BGS](https://www.bgs.ac.uk/?p=30132).
- IIT Mandi: low-cost sub-surface IoT framework that sends SMS warnings on significant sub-surface movement; "mass deployable" — [IIT Mandi SCENE publication 479](https://scene.iitmandi.ac.in/pages/publication/publication_details/479).
- IIT Mandi cost: ~Rs 11,000 install and ~Rs 5,000/yr running vs ~Rs 1 crore quoted for a conventional sensor (researcher quote in press, not peer-reviewed); solar + battery powered; 13 devices deployed in HP (one report), 15+ locations in Mandi (another) — [Tribune](https://m.tribuneindia.com/news/archive/himachal/archive-608331); [The Better India](https://www.thebetterindia.com/259584/iit-mandi-innovation-himachal-landslide-rainfall-early-warning-device-save-lives); [IIT Mandi press releases](https://research.iitmandi.ac.in/main/newslisting/press_release.php).
- DST-funded IIT Mandi extensometer project (2020–2023) total budget INR 44,87,288 — [India Science & Technology portal](https://www.indiascienceandtechnology.gov.in/hi/research/low-cost-extensometer-based-landslide-monitoring-and-early-warning-device).

### Inferences
- Reference architecture for a prototype: sensor node (rain gauge tipping bucket + MEMS tilt/accelerometer + soil moisture) → LoRa or GSM/NB-IoT uplink → MQTT broker → ingest service → time-series DB → rule engine → SMS/push. For 3 days, emulate nodes with a Python script publishing MQTT messages. (inference)
- Point sensors cover tens of metres; a 500 m-segment route score must rely mainly on gridded rainfall, with sensors as optional "override" inputs. (inference)

### Gaps
- No itemised BOM, radio protocol (LoRa vs GSM) or node firmware details for either system were found.
- No published false-alarm statistics for either system found.

## Q4. Cloudburst / flash-flood nowcasting: IMD nowcasts, J&K Doppler radars, FFGS

### Takeaway
J&K has three operational Doppler Weather Radars (Srinagar, Jammu, Banihal) with four more planned (Rajouri, Doda, Anantnag, Sopore). IMD runs a South Asia Flash Flood Guidance System covering India, Bangladesh, Bhutan, Nepal and Sri Lanka. None of these was confirmed as a public machine-readable API; a prototype should treat them as links/overlays and use gridded model or satellite rain for computation.

### Cited Findings
- J&K has three operational DWRs (Srinagar, Jammu, Banihal); IMD plans four more at Rajouri, Doda, Anantnag and Sopore (total seven) — [News On AIR, Aug 2026](https://newsonair.gov.in/imd-to-install-4-additional-doppler-weather-radars-in-jk/).
- In July 2022 the Banihal Top radar was still being installed — [MoES Rajya Sabha reply, Jul 2022](https://www.moes.gov.in/sites/default/files/RS-in-English-1300-28-07-2022.pdf). Deccan Herald reported it was non-functional at the time of the July 2022 Amarnath flash flood and described it as an X-band radar with ~100 km range covering the Pir Panjal — [Deccan Herald](https://www.deccanherald.com/amp/story/india%2Famarnath-tragedy-could-have-been-averted-if-doppler-radar-at-banihal-was-functional-1125159.html). Conflict resolved by date: operational as of 2026 per News On AIR.
- IMD issues flash flood guidance for India, Bangladesh, Bhutan, Nepal and Sri Lanka — [MoES reply](https://moes.gov.in/sites/default/files/2112English.pdf). Early description: FFGS forecasts flash floods up to 6 h ahead using soil-moisture/absorption state — [Mongabay India, 2018](https://india.mongabay.com/2018/07/early-warning-system-for-flash-floods-can-save-thousands-of-lives-at-risk/).
- Recent events on the target routes:
  - 14 Aug 2025 cloudburst/flash flood at Chasoti (Kishtwar), the last motorable village on the Machail Mata Yatra route; Wikipedia lists 68 deaths, ~300 injured, ≥38 missing; yatra suspended — [Wikipedia: 2025 Kishtwar district flash flood](https://en.wikipedia.org/wiki/2025_Kishtwar_district_flash_flood); [Down To Earth](https://www.downtoearth.org.in/amp/story/natural-disasters/massive-cloudburst-in-jammu-and-kashmirs-kishtwar-kills-30-100-injured-and-200-missing).
  - 26 Aug 2025 landslide near Inderprastha Bhojnalaya, Ardhkuwari, on the Katra–Vaishno Devi track (~midway on the 12 km trek), around 3 pm; toll ≥34 with 23 missing by 28 Aug, amid days of heavy rain in Jammu — [Free Press Journal](https://www.freepressjournal.in/amp/india/mata-vaishno-devi-landslide-death-toll-rises-to-30-over-20-injured-as-heavy-rains-batter-jammu-10-points); [New Indian Express via Magzter](https://www.magzter.com/fr/stories/newspaper/The-New-Indian-Express-Kannur/LANDSLIDE-TOLL-ON-VAISHNO-DEVI-ROUTE-REACHES-34).

### Inferences
- Cloudbursts (IMD definition commonly ≥100 mm/h over ~20–30 km²; definition not re-verified here) are below the resolution of 9–25 km models and 0.1° IMERG; any 15-min prototype will under-detect them. Be honest in the UI: show "convective watch" from model CAPE/precipitation rate, not a cloudburst prediction. (inference)
- The two Aug 2025 events are good replay test cases: Chasoti (flash flood, Machail route) and Ardhkuwari (landslide, Vaishno Devi route). (inference)

### Gaps
- No public API or open data feed for IMD DWR imagery, IMD nowcasts, or FFGS outputs was confirmed.
- No observed rainfall totals for Katra on 25–26 Aug 2025 or Chasoti on 14 Aug 2025 were found.

## Q5. Open data and APIs (IMD, Open-Meteo, IMERG, DEM, OSM, NASA GLC / LHASA): access terms

### Takeaway
Best 3-day stack: Open-Meteo (no key, CC BY 4.0, forecast + historical-forecast API from ~2022 for replaying Aug 2025) for 15-min-cadence polling; IMERG Early (0.1°, 30 min, ~4 h latency, Earthdata login) as observed-rain cross-check; NASA LHASA 2.1.1 (Python, GeoTIFF, Earthdata login) as a hazard reference layer. IMD APIs are free for non-commercial use but registration details were not confirmed.

### Cited Findings
**Open-Meteo**
- Data licence CC BY 4.0: credit, licence link, indicate changes; display a link next to the data. Code is AGPLv3 — [Open-Meteo licence](https://open-meteo.com/en/licence).
- Free API is non-commercial with call limits; commercial use needs a subscription or self-hosting (secondary source, verify on Open-Meteo pricing) — [packagist omnilab/open-meteo README](https://packagist.org/packages/omnilab/open-meteo).
- Historical Forecast API endpoint `https://historical-forecast-api.open-meteo.com/v1/forecast`, same parameters as the Forecast API; built by stitching the first hours of successive forecast runs; start dates by model: ECMWF IFS HRES 2017, GFS 2021, most ICON 2022 — [Open-Meteo Historical Forecast API docs](https://open-meteo.com/en/docs/historical-forecast-api).
- 15-minutely variables (precipitation, rain, snowfall, snowfall height) are native only in Central Europe and North America; elsewhere they are interpolated from hourly — same source.
- Resolutions: ECMWF IFS HRES 9 km; ICON Global ~11 km; GFS ~13 km (0.11°) — same source.
- ERA5 (Historical Weather API) goes back to 1940 at 0.25°; ERA5-Land 0.1° — same source.

**NASA IMERG**
- IMERG Early Run: 0.1° every half-hour, ~4 h latency; V07 current (AWS listing mentions V07B) — [data.gov GPM_3IMERGHHE](https://catalog.data.gov/dataset/gpm-imerg-early-precipitation-l3-half-hourly-0-1-degree-x-0-1-degree-v07-gpm-3imerghhe-at--020d4); [GPM IMERG Early Run](https://gpm.nasa.gov/taxonomy/term/1357); [AWS registry](https://registry.opendata.aws/nasa-gpm3imerghhe).
- Final Run has ~3.5-month latency (not for real time) — [UCAR GDEX d731000](https://gdex.ucar.edu/datasets/d731000/).

**NASA LHASA**
- github.com/nasa/LHASA: Python (`lhasa.py`, `lhasa.sh`, conda `lhasa.yml`), current version 2.1.1; static inputs `static.zip`, exposure `exposure.zip`; dynamic input IMERG HDF5; output GeoTIFF hazard + CSV exposure; ~1 km (30 arc-s), daily; includes forecast (`fcast/`) folders; needs NASA Earthdata login and PPS registration; licence in `LICENSE.pdf` — [GitHub nasa/LHASA](https://github.com/nasa/LHASA). Listed as open source in NASA catalog — [NASA software GSC-18595-1](https://software.nasa.gov/software/GSC-18595-1).
- LHASA validated against NASA Global Landslide Catalog (GLC) — [NASA ARSET](https://appliedsciences.nasa.gov/sites/default/files/2024-05/Day2_P1.pdf).

**IMD**
- IMD API reference at api.imd.gov.in/public/api_reference.html (observation and forecast products) — [IMD API_doc.pdf](https://mausam.imd.gov.in/Forecast/marquee_data/API_doc.pdf).
- IMD RTI reply: APIs provided without charge for non-commercial use only — [IMD RTI 211 (2026-01-12)](https://internal.imd.gov.in/section/rti/rticases/20260112_rti_211.pdf).

### Inferences
- **Polling budget (estimate):** 3 routes × ~30 km each / 0.5 km = ~180 segments (assumes ~90 km total route length incl. Baltal & Pahalgam options; Vaishno Devi ~12–14 km). Open-Meteo grid cells are ~9–11 km, so ~15–25 unique grid points cover all segments; at one call per 15 min with multi-location requests, that is ~100 calls/day, far under typical free limits. (estimate)
- Because 15-minutely data are interpolated outside Europe/N. America, a "15-minute update" in India means re-pulling the latest hourly forecast and nowcast blend every 15 min, not true 15-min observations. State this in the demo. (inference)
- Replay of Aug 2025: use Historical Forecast API (ECMWF IFS 9 km or best_match) for 2025-08-10 → 2025-08-28 to show the score rising before Chasoti (14 Aug) and Ardhkuwari (26 Aug). (inference)
- DEM: Copernicus GLO-30 (30 m) or SRTM 30 m for slope per segment; OSM has trekking paths for these routes (e.g., `highway=path` Katra–Bhawan; Baltal–Holy Cave). Neither licence nor OSM coverage was checked in this research. (inference)

### Gaps
- IMD API registration process, key/IP whitelisting, and rate limits: not confirmed.
- Open-Meteo exact free-tier rate limits (commonly cited ~10,000 calls/day, unverified here).
- Copernicus DEM licence, SRTM access, OSM route completeness for Amarnath/Machail, NASA GLC download: not researched in this pass.

## Q6. Typical software stack (PostGIS, GeoServer, Python, TSDB, Leaflet/MapLibre)

### Takeaway
Published EWS outputs are raster/vector GIS layers (LHASA GeoTIFF + CSV; GSI shapefile-style layers on Bhukosh). A lean 3-day stack: Python (geopandas/rasterio/shapely) for segmenting OSM routes and sampling DEM/susceptibility; PostGIS or even SQLite/GeoPackage for segments; a time-series table for scores; a scheduler (cron/APScheduler) every 15 min; Leaflet or MapLibre for the map. GeoServer is optional overhead.

### Cited Findings
- LHASA outputs GeoTIFF hazard rasters and CSV exposure tables, runs from a shell script at a chosen cadence (e.g., daily) — [GitHub nasa/LHASA](https://github.com/nasa/LHASA).
- GSI publishes inventory and susceptibility layers via a map portal (Bhukosh) and NGDR, plus a web portal and mobile app (Bhusanket, Bhooskhalan) — [MoES/PIB](https://moes.gov.in/sites/default/files/PIB2158420.pdf).
- LANDSLIP bulletins are district-level, 48-h, four-level categorical outputs sent to administrators — [LANDSLIP KP](https://nora.nerc.ac.uk/id/eprint/532238/1/LANDSLIP_KP_LandslideForecastBulletin_3March2022_OR21070.pdf).

### Inferences
- Pipeline (inference):
  1. Day 1: pull OSM route lines (Overpass) → `shapely.ops.substring` into 500 m segments → sample slope from Copernicus DEM (rasterio) → attach GSI susceptibility class (or slope-based proxy) → store in PostGIS/GeoPackage.
  2. Day 2: scheduler every 15 min → Open-Meteo forecast (`precipitation`, past 24 h + next 6–24 h) per unique grid point → compute 1-h/24-h/48-h/15-day sums → threshold ratios (Shah et al. daily + antecedent; Dahal & Hasegawa ID as upper check) → score 0–100 and 4 levels (mirroring LANDSLIP Low/Moderate/High/Very High) → write to `segment_scores(segment_id, ts, score, level, drivers)`.
  3. Day 3: FastAPI GeoJSON endpoint + Leaflet/MapLibre colour-coded segments; replay mode on Aug 2025; optional simulated MQTT sensor override.
- A time-series DB (TimescaleDB/InfluxDB) is unnecessary at ~180 segments × 96 updates/day ≈ 17,000 rows/day (estimate); plain Postgres or SQLite suffices. (estimate)
- Show "drivers" per segment (e.g., "24 h rain 38 mm = 2.6× threshold; slope 41°; high susceptibility") for explainability; LANDSLIP's design shows operators need categorical levels, not raw probabilities. (inference)

### Gaps
- No published reference architecture of the GSI NLFC backend (databases, servers) was found.
- No published validation of any EWS on J&K pilgrim routes was found; the prototype's thresholds will be uncalibrated for these routes.
