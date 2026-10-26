// Builds docs/pitch/JK_kavach_Deck.pptx (7 slides, neutral layout for pasting into the IIT Bombay template).
// Run: NODE_PATH=<dir with pptxgenjs, react, react-dom, react-icons, sharp>/node_modules node docs/pitch/build_deck.js
// Numbers: docs/replay-findings.md [measured], docs/research.md [sourced]. Screenshots: docs/pitch/img/ (real API replay).
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const HERE = __dirname;
const IMG = (f) => path.join(HERE, "img", f);
const OUT = path.join(HERE, "JK_kavach_Deck.pptx");

const COL = {
  navy: "13294B", red: "C62828", orange: "E65100", text: "1F2937", muted: "5B6472",
  tint: "F1F4F8", line: "D5DBE3", purple: "6A1B9A", white: "FFFFFF", redTint: "FDECEC",
};
const FONT = "Calibri";
const FOOTER = "YatraKavach · team kavach · HSC|JK|00032 · Hack for Social Cause 2027 · Theme 11";

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function text(slide, t, o) {
  slide.addText(t, { fontFace: FONT, color: COL.text, margin: 0, valign: "top", isTextBox: true, ...o });
}

function simTag(slide, x, y) {
  slide.addText("SIMULATED", {
    x, y, w: 1.05, h: 0.26, fontFace: FONT, fontSize: 10, bold: true, color: COL.white, align: "center",
    valign: "middle", margin: 0, isTextBox: true,
    shape: "roundRect", rectRadius: 0.05, fill: { color: COL.purple },
  });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
  pres.author = "Team kavach (Ritik Bhardwaj)";
  pres.title = "YatraKavach: HSC 2027 pitch deck";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: COL.white },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 12.33, h: 0.8, fontFace: FONT,
        fontSize: 30, bold: true, color: COL.navy, valign: "middle", margin: 0 }, text: "" } },
      { text: { text: FOOTER, options: { x: 0.5, y: 7.0, w: 10.5, h: 0.3, fontFace: FONT, fontSize: 10,
        color: COL.muted, margin: 0, valign: "middle" } } },
    ],
    slideNumber: { x: 12.33, y: 7.0, w: 0.5, h: 0.3, fontFace: FONT, fontSize: 10, color: COL.muted, align: "right" },
  });
  const add = (title) => {
    const s = pres.addSlide({ masterName: "CONTENT" });
    s.addText(title, { placeholder: "title" });
    return s;
  };

  // ---------- Slide 1: problem, three dated events ----------
  {
    const s = add("The warning existed. The decision did not.");
    const events = [
      { ic: fa.FaWater, date: "8 Jul 2022", place: "Amarnath cave", line: "Flash flood. No rain data from the upper reaches." },
      { ic: fa.FaCloudShowersHeavy, date: "14 Aug 2025", place: "Chasoti, Machail yatra", line: "IMD alerts for the region; the yatra went on. About 61–64 dead." },
      { ic: fa.FaMountain, date: "26 Aug 2025", place: "Adhkuwari, Vaishno Devi", line: "Landslide at 14:40; at least 34 dead. Board: old track closed by ~12:00." },
    ];
    // timeline axis
    s.addShape(pres.shapes.LINE, { x: 1.0, y: 2.15, w: 11.33, h: 0, line: { color: COL.line, width: 2 }, objectName: "timeline" });
    for (let i = 0; i < 3; i++) {
      const e = events[i], x = 0.5 + i * 4.18, w = 3.97;
      s.addShape(pres.shapes.OVAL, { x: x + w / 2 - 0.45, y: 1.7, w: 0.9, h: 0.9, fill: { color: COL.red }, line: { color: COL.white, width: 3 }, objectName: `event-dot-${i + 1}` });
      s.addImage({ data: await icon(e.ic, COL.white), x: x + w / 2 - 0.25, y: 1.9, w: 0.5, h: 0.5, altText: e.place });
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.85, w, h: 2.0, rectRadius: 0.08, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: `event-card-${i + 1}` });
      text(s, e.date, { x: x + 0.25, y: 3.0, w: w - 0.5, h: 0.4, fontSize: 20, bold: true, color: COL.red });
      text(s, e.place, { x: x + 0.25, y: 3.4, w: w - 0.5, h: 0.35, fontSize: 16, bold: true, color: COL.navy });
      text(s, e.line, { x: x + 0.25, y: 3.8, w: w - 0.5, h: 0.95, fontSize: 15 });
    }
    text(s, [
      { text: "Each time, a warning reached some official. ", options: { bold: true, color: COL.navy } },
      { text: "Nobody turned it into “close this stretch, move these people, now” — and nobody can show who decided." },
    ], { x: 0.5, y: 5.2, w: 12.33, h: 0.75, fontSize: 18 });
    text(s, "Sources: Onmanorama, MoES (2022); ETV Bharat (2025); The Tribune (2025). Links in docs/research.md.",
      { x: 0.5, y: 6.25, w: 12.33, h: 0.3, fontSize: 10, color: COL.muted });
    s.addNotes("In all three, a warning reached some official. Nobody turned it into 'close this stretch, move these people, now' — and nobody can show who decided.\n\nFacts (docs/research.md): Amarnath 8 Jul 2022 — MoES said the upper reaches may have had more rain, 'for which data are not available'. Chasoti 14 Aug 2025 — IMD had issued alerts for the Chenab valley region; about 61-64 died; IMD's J&K director called compliance 'very little or negligible'. Adhkuwari 26 Aug 2025 — at least 34 died at 14:40; the board says it closed the old track by 12:00; the inquiry report is not public.");
  }

  // ---------- Slide 2: who is affected, where the gap is ----------
  {
    const s = add("Who is affected, and where the gap is");
    const boxes = [
      { ic: fa.FaSatelliteDish, h: "IMD / GSI forecasts", d: "District scale" },
      { ic: fa.FaVideo, h: "RFID / CCTV crowd", d: "No hazard input" },
      { ic: fa.FaBroadcastTower, h: "SACHET mass alerts", d: "Areas, not people in transit" },
      { ic: fa.FaDesktop, h: "Shrine-board control room", d: "No record of who approved what" },
    ];
    const bw = 2.85, gap = 0.31;
    for (let i = 0; i < 4; i++) {
      const x = 0.5 + i * (bw + gap);
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.4, w: bw, h: 1.95, rectRadius: 0.08, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: `system-${i + 1}` });
      s.addImage({ data: await icon(boxes[i].ic, COL.navy), x: x + 0.25, y: 1.6, w: 0.45, h: 0.45, altText: boxes[i].h });
      text(s, boxes[i].h, { x: x + 0.25, y: 2.15, w: bw - 0.5, h: 0.5, fontSize: 16, bold: true, color: COL.navy });
      text(s, boxes[i].d, { x: x + 0.25, y: 2.7, w: bw - 0.5, h: 0.55, fontSize: 14, color: COL.red });
    }
    // the gap
    const y = 3.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 3.4, h: 0.85, rectRadius: 0.08, fill: { color: COL.navy }, line: { color: COL.navy }, objectName: "district-alert" });
    text(s, "District alert", { x: 0.5, y, w: 3.4, h: 0.85, fontSize: 18, bold: true, color: COL.white, align: "center", valign: "middle" });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 9.43, y, w: 3.4, h: 0.85, rectRadius: 0.08, fill: { color: COL.navy }, line: { color: COL.navy }, objectName: "pilgrim-on-segment" });
    text(s, "Pilgrim on segment X", { x: 9.43, y, w: 3.4, h: 0.85, fontSize: 18, bold: true, color: COL.white, align: "center", valign: "middle" });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.2, y, w: 4.93, h: 0.85, rectRadius: 0.08, fill: { color: COL.redTint }, line: { color: COL.red, width: 2, dashType: "dash" }, objectName: "gap" });
    text(s, "GAP: nobody owns “close this 500 m now”", { x: 4.2, y, w: 4.93, h: 0.85, fontSize: 17, bold: true, color: COL.red, align: "center", valign: "middle" });
    // beneficiaries
    s.addImage({ data: await icon(fa.FaUsers, COL.navy), x: 0.5, y: 5.05, w: 0.5, h: 0.5, altText: "Beneficiaries" });
    text(s, [
      { text: "Who it protects: ", options: { bold: true, color: COL.navy } },
      { text: "pilgrims on mountain tracks (Vaishno Devi cap: 50,000 a day), pony and palki operators, shopkeepers on the track, SDRF and police on duty." },
    ], { x: 1.2, y: 5.0, w: 11.63, h: 0.9, fontSize: 17 });
    text(s, "Sources: The Tribune (SMVDSB RFID, 700+ CCTV, 50,000/day cap); ETV Bharat (SACHET); Business Standard, MoES (GSI bulletins). Gap: team inference from these. Links in docs/research.md.",
      { x: 0.5, y: 6.3, w: 12.33, h: 0.5, fontSize: 10, color: COL.muted });
    s.addNotes("India already has the pieces, in silos. IMD and GSI warn at district scale (no J&K district is on GSI's published bulletin list). The shrine boards know where people are through RFID and CCTV, but those systems have no slope-hazard input. SACHET sends CAP alerts to areas, not to people in transit on a track with weak mobile coverage. And nobody records who approved what. The missing step is from 'district alert' to 'pilgrim on segment X'.\n\nWho benefits: pilgrims (Vaishno Devi cap 50,000 a day), pony and palki operators, shopkeepers on the track, SDRF and police on duty.");
  }

  // ---------- Slide 3: solution ----------
  {
    const s = add("YatraKavach: risk per 500 m, decided by a named officer");
    const steps = ["Rain + slope", "Segment hazard", "+ people on segment", "Proposed action", "Officer approves", "CAP alert (en/hi/ur)"];
    const sw = 1.92, sg = 0.164;
    for (let i = 0; i < steps.length; i++) {
      const x = 0.5 + i * (sw + sg), last = i >= 4;
      s.addShape(i === 0 ? pres.shapes.PENTAGON : pres.shapes.CHEVRON, {
        x, y: 1.45, w: sw + 0.12, h: 1.0, fill: { color: last ? COL.red : COL.navy }, line: { color: COL.white, width: 1 }, objectName: `flow-${i + 1}`,
      });
      text(s, steps[i], { x: x + (i === 0 ? 0.1 : 0.5), y: 1.45, w: i === 0 ? sw - 0.4 : sw - 0.6, h: 1.0, fontSize: 14, bold: true, color: COL.white, align: "center", valign: "middle" });
    }
    const cols = [
      { ic: fa.FaRoute, h: "Where", b: "35 segments on the three Vaishno Devi tracks. Hazard every hour from published Himalayan rain thresholds." },
      { ic: fa.FaUsers, h: "Who is there", b: "People per segment and the queue a hold creates. AI crowd count from a camera frame (DM-Count).", sim: true },
      { ic: fa.FaUserCheck, h: "Who decides", b: "RED needs two officers; escalation after 10 min; break-glass with a reason. Hash-chained audit log." },
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.5 + i * 4.18, w = 3.97;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.85, w, h: 2.15, rectRadius: 0.08, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: `feature-${i + 1}` });
      s.addImage({ data: await icon(cols[i].ic, COL.navy), x: x + 0.25, y: 3.05, w: 0.45, h: 0.45, altText: cols[i].h });
      text(s, cols[i].h, { x: x + 0.85, y: 3.05, w: 1.9, h: 0.45, fontSize: 18, bold: true, color: COL.navy, valign: "middle" });
      if (cols[i].sim) simTag(s, x + w - 1.3, 3.15);
      text(s, cols[i].b, { x: x + 0.25, y: 3.7, w: w - 0.5, h: 1.2, fontSize: 16 });
    }
    text(s, "CAP 1.2, the format NDMA SACHET uses · FastAPI · PostgreSQL / PostGIS · MapLibre · open source (MIT). Crowd counts on tracks and delivery channels are SIMULATED in the prototype; camera demo uses licensed festival photos.",
      { x: 0.5, y: 5.3, w: 12.33, h: 0.7, fontSize: 13, color: COL.muted });
    s.addNotes("YatraKavach splits the three Vaishno Devi tracks into 35 segments of about 500 m. Every hour it scores landslide hazard per segment from rain over 3 h, 24 h and 15 days against published Himalayan thresholds, with a step-up for steep slopes. It adds the people on each segment (SIMULATED RFID counts) and models the queue that builds when the ascent is stopped. It proposes one action per track and level. Nothing goes out automatically: a named officer approves; RED needs two different officers; no answer in 10 minutes escalates; a senior officer can break glass with a written reason. Every step goes into a hash-chained, append-only audit log. The approved alert is CAP 1.2 — the format SACHET already uses — in English, Hindi and Urdu. A camera frame can be counted with DM-Count to feed the crowd level; the demo uses licensed festival photos, not shrine cameras.");
  }

  // ---------- Slide 4: replay ----------
  {
    const s = add("Replay: 26 August 2025");
    const y = 1.3, h = 3.75;
    const w1 = h * 2732 / 1536; // 6.94
    s.addImage({ path: IMG("replay-0500-segment.png"), x: 0.5, y, w: w1, h, altText: "Console at 26 Aug 2025 05:00 IST: old track RED with the Why panel" });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: w1, h, fill: { type: "none" }, line: { color: COL.line, width: 1 }, objectName: "frame-1" });
    const w2 = h * 794 / 1065;
    const x2 = 0.5 + w1 + 0.25;
    s.addImage({ path: IMG("alert-approved-cap.png"), x: x2, y, w: w2, h, altText: "RED alert approved by two officers, CAP 1.2 with Hindi text" });
    s.addShape(pres.shapes.RECTANGLE, { x: x2, y, w: w2, h, fill: { type: "none" }, line: { color: COL.line, width: 1 }, objectName: "frame-2" });
    text(s, "26 Aug 05:00 IST: old track at Adhkuwari RED, with the reasons in numbers", { x: 0.5, y: y + h + 0.08, w: w1, h: 0.3, fontSize: 11, color: COL.muted });
    text(s, "RED alert: 2 of 2 officers, CAP in Hindi", { x: x2, y: y + h + 0.08, w: w2, h: 0.3, fontSize: 11, color: COL.muted });
    // stat column
    const xs = x2 + w2 + 0.3, ws = 12.83 - xs;
    const stats = [
      { n: "9.5 h", l: "RED before the slide (GFS)", c: COL.red },
      { n: "1.5 h", l: "with ECMWF or ERA5", c: COL.orange },
      { n: "674 → 0", l: "on the slide segment if held at first ORANGE", c: COL.navy, sim: true },
    ];
    for (let i = 0; i < 3; i++) {
      const yy = y + i * 1.32;
      text(s, stats[i].n, { x: xs, y: yy, w: ws, h: 0.6, fontSize: 32, bold: true, color: stats[i].c });
      text(s, stats[i].l, { x: xs, y: yy + 0.6, w: ws, h: 0.5, fontSize: 13, color: COL.text });
    }
    simTag(s, xs, y + 2 * 1.32 + 1.2);
    text(s, [
      { text: "Holding the ascent fills the Katra gate to 5.4 persons/m² inside a RED segment (SIMULATED): ", options: {} },
      { text: "closing a track moves the risk to the people below it.", options: { bold: true, color: COL.navy } },
    ], { x: 0.5, y: 5.75, w: 12.33, h: 0.6, fontSize: 16 });
    text(s, "Replay of archived model rain (Open-Meteo historical forecast, CC BY 4.0; 9–25 km grid): close to what a live system would have seen, not identical. Screenshots: real API replay; approval timestamps are from the demo run.",
      { x: 0.5, y: 6.38, w: 12.33, h: 0.5, fontSize: 10, color: COL.muted });
    s.addNotes("This is the replay of 26 August 2025, run through the real API. With the GFS forecast, the old track at Adhkuwari reaches RED at 05:00 IST — about 9.5 hours before the 14:40 slide — and the Why panel shows the reasons in numbers: 24 h rain 154 mm against the 144 mm severe level. With ECMWF or ERA5 the lead is only about 1.5 hours — I say this openly: honesty is a feature.\n\nThe alert needs two different officers for RED; the CAP 1.2 message carries English, Hindi and Urdu.\n\nThe cost of waiting (SIMULATED pilgrims): if officers had approved a hold at the first ORANGE warning, 0 pilgrims would have been on the slide segment at 14:00, instead of 674 — in all three weather models. At the first GFS RED it is 93. The cost is a queue at the Katra gate. A hold at ~12:00 at the Katra gate is too late for this segment: those people had already passed the gate. The real closure was at Adhkuwari; modelled there, 236 descending pilgrims remain (measured in PR 9, not in the API).\n\nHolding the ascent fills the Katra gate to 5.4 persons per m² inside a segment that is itself RED: closing a track moves the risk to the people below it.");
  }

  // ---------- Slide 5: impact, KPIs, scale ----------
  {
    const s = add("Impact, KPIs and scale");
    const hdr = (t) => ({ text: t, options: { bold: true, color: COL.white, fill: { color: COL.navy } } });
    const rows = [
      [hdr("KPI"), hdr("Prototype result"), hdr("Pilot target")],
      ["Lead time of RED before a slide", "1.5–9.5 h (26 Aug 2025 replay, 3 models)", "≥ 3 h with radar input"],
      ["Alerts with a named approver and time", "100%", "100%"],
      ["Open alerts at peak (26 Aug, 14:00)", "6: one per track and level", "≤ 1 per track and level"],
      ["Pilgrims on slide segment at 14:00 (SIMULATED)", "674 no action → 0 if held at first ORANGE; 93 at first RED (GFS)", "Decision within 1 h of ORANGE"],
      ["Camera crowd count error", "MAE 60 people/image (ShanghaiTech A)", "Validated on SMVDSB CCTV"],
      ["Time from proposal to decision", "Logged per alert", "Median < 10 min"],
    ];
    s.addTable(rows, {
      x: 0.5, y: 1.3, w: 8.3, colW: [2.7, 3.3, 2.3], fontFace: FONT, fontSize: 13, color: COL.text,
      border: { type: "solid", pt: 0.75, color: COL.line }, valign: "middle", margin: [3, 6, 3, 6],
      rowH: [0.4, 0.55, 0.45, 0.45, 0.8, 0.55, 0.45],
    });
    const h = 3.65, w = h * 846 / 926;
    s.addImage({ path: IMG("impact-gfs.png"), x: 12.83 - w, y: 1.3, w, h, altText: "What-if panel: pilgrims on VD-OLD-01 at 14:00 by decision time" });
    text(s, "Console what-if panel, GFS (SIMULATED pilgrims)", { x: 12.83 - w, y: 1.3 + h + 0.08, w, h: 0.3, fontSize: 11, color: COL.muted });
    text(s, [
      { text: "Scale: ", options: { bold: true, color: COL.navy } },
      { text: "same engine for Amarnath, Machail, Char Dham, Sabarimala — only segments and thresholds change. ", options: {} },
      { text: "Sustainable: ", options: { bold: true, color: COL.navy } },
      { text: "open source, one small server, fits shrine-board control rooms and SDMA. Add Dogri, Kashmiri, Pahari with native speakers.", options: {} },
    ], { x: 0.5, y: 5.6, w: 12.33, h: 0.95, fontSize: 15 });
    s.addNotes("KPIs, prototype result vs pilot target. Lead time of RED before the slide: 1.5 to 9.5 hours in the 26 Aug 2025 replay, depending on the weather model; target at least 3 hours with IMD radar input. Every alert that goes out carries a named approver and a timestamp — the workflow does not allow otherwise. At the peak there are 6 open alerts, one per track and level, not a flood. Pilgrims on the slide segment at 14:00 (SIMULATED): 674 with no action, 0 if held at the first ORANGE in all three models; at the first RED, 93 with GFS and 674 with ECMWF and ERA5. Camera count error: MAE 60 people per image on ShanghaiTech Part A; to be validated on shrine-board CCTV. Time from proposal to decision is logged per alert; the pilot target is a median under 10 minutes.\n\nScale: the same engine works for Amarnath, Machail, Char Dham and Sabarimala — only segments and thresholds change. Languages are templates; Dogri, Kashmiri and Pahari need native speakers. It is open source and runs on one small server.");
  }

  // ---------- Slide 6: roadmap ----------
  {
    const s = add("Implementation roadmap and what it needs");
    const phases = [
      { h: "1  Pilot (one monsoon)", b: "Old track + Himkoti with the SMVDSB control room and SDRF. Read-only, no public alerts; compare proposals with real decisions." },
      { h: "2  Calibrate", b: "Local slide records, IMD radar feed, 3–5 rain gauges on the track, GSI susceptibility layer." },
      { h: "3  Integrate", b: "RFID gate counts, CCTV density, approved CAP to SACHET, app and PA." },
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.5 + i * 4.18, w = 3.97;
      s.addShape(i === 0 ? pres.shapes.PENTAGON : pres.shapes.CHEVRON, { x, y: 1.4, w: i === 2 ? w : w + 0.21, h: 0.8, fill: { color: COL.navy }, line: { color: COL.white, width: 1 }, objectName: `phase-${i + 1}` });
      text(s, phases[i].h, { x: x + (i === 0 ? 0.25 : 0.5), y: 1.4, w: w - 0.6, h: 0.8, fontSize: 18, bold: true, color: COL.white, valign: "middle" });
      text(s, phases[i].b, { x: x + 0.1, y: 2.4, w: w - 0.3, h: 1.5, fontSize: 16 });
    }
    const boxes = [
      { ic: fa.FaHandshake, h: "What it needs", b: "Data-sharing MoU · one server · a field-officer champion · native-speaker review", fill: COL.tint, c: COL.navy },
      { ic: fa.FaExclamationTriangle, h: "Limits, shown openly", b: "Thresholds not calibrated for these tracks · 9–25 km rain grid · crowd and delivery channels SIMULATED", fill: COL.redTint, c: COL.red },
    ];
    for (let i = 0; i < 2; i++) {
      const x = 0.5 + i * 6.27, w = 6.06;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.0, w, h: 1.85, rectRadius: 0.08, fill: { color: boxes[i].fill }, line: { color: boxes[i].fill }, objectName: `box-${i + 1}` });
      s.addImage({ data: await icon(boxes[i].ic, boxes[i].c), x: x + 0.3, y: 4.2, w: 0.45, h: 0.45, altText: boxes[i].h });
      text(s, boxes[i].h, { x: x + 0.95, y: 4.2, w: w - 1.2, h: 0.45, fontSize: 18, bold: true, color: boxes[i].c, valign: "middle" });
      text(s, boxes[i].b, { x: x + 0.3, y: 4.85, w: w - 0.6, h: 0.9, fontSize: 16 });
    }
    s.addNotes("Roadmap in three phases. One: a one-monsoon pilot on the old track and Himkoti with the SMVDSB control room and SDRF — read-only, no public alerts — comparing the system's proposals with the real decisions. Two: calibrate with local slide records, the IMD radar feed, 3 to 5 rain gauges on the track and the GSI susceptibility layer. Three: integrate RFID gate counts, CCTV density, and send approved CAP alerts to SACHET, the app and the PA system.\n\nWhat it needs: a data-sharing MoU, one server, a field-officer champion and native-speaker review of the Hindi and Urdu texts.\n\nLimits, said openly: thresholds come from NH-44 and Nepal studies and are not calibrated for these tracks; forecast rain is on a 9-25 km grid; crowd data and delivery channels are SIMULATED in the prototype.");
  }

  // ---------- Slide 7: team, AI disclosure, attributions ----------
  {
    const s = add("Team and AI-use disclosure");
    s.addShape(pres.shapes.OVAL, { x: 0.5, y: 1.4, w: 1.1, h: 1.1, fill: { color: COL.navy }, line: { color: COL.navy }, objectName: "team-avatar" });
    text(s, "RB", { x: 0.5, y: 1.4, w: 1.1, h: 1.1, fontSize: 26, bold: true, color: COL.white, align: "center", valign: "middle" });
    text(s, "Ritik Bhardwaj", { x: 1.85, y: 1.4, w: 3.6, h: 0.45, fontSize: 20, bold: true, color: COL.navy });
    text(s, "B.Tech IT, NIT Srinagar · solo entry, J&K", { x: 1.85, y: 1.85, w: 3.6, h: 0.6, fontSize: 14, color: COL.muted });
    text(s, "Problem framing, design decisions, validation, pitch.", { x: 0.5, y: 2.75, w: 4.95, h: 0.6, fontSize: 16 });
    text(s, [
      { text: "Code: ", options: { bold: true, color: COL.navy } },
      { text: "github.com/RitikBhardwaj-programmer/YatraKavach (MIT)", options: {} },
    ], { x: 0.5, y: 3.45, w: 4.95, h: 0.6, fontSize: 14 });
    // disclosure box
    const bx = 5.75, bw = 7.08;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: 1.4, w: bw, h: 3.05, rectRadius: 0.08, fill: { color: COL.tint }, line: { color: COL.navy, width: 1.5 }, objectName: "ai-disclosure" });
    s.addImage({ data: await icon(fa.FaRobot, COL.navy), x: bx + 0.3, y: 1.6, w: 0.45, h: 0.45, altText: "AI-use disclosure" });
    text(s, "AI-use disclosure", { x: bx + 0.95, y: 1.6, w: 4, h: 0.45, fontSize: 18, bold: true, color: COL.navy, valign: "middle" });
    text(s, [
      { text: "Tool: ", options: { bold: true } }, { text: "Claude Code (Anthropic), as coding and research agent.", options: { breakLine: true } },
      { text: "AI did: ", options: { bold: true } }, { text: "research report, most code, tests and docs, an independent code review.", options: { breakLine: true } },
      { text: "Team did: ", options: { bold: true } }, { text: "chose the problem, set requirements, approved every design and fix, validated results.", options: { breakLine: true } },
      { text: "Share (team estimate): ", options: { bold: true, color: COL.red } }, { text: "about 60–65% of code and documents AI-generated under the team’s direction.", options: {} },
    ], { x: bx + 0.3, y: 2.2, w: bw - 0.6, h: 2.6, fontSize: 15, paraSpaceAfter: 6 });
    // attributions
    text(s, [
      { text: "Data and credits: ", options: { bold: true, color: COL.navy } },
      { text: "Tracks © OpenStreetMap contributors (ODbL). Elevation: Copernicus DEM GLO-90 via Open-Meteo. Rain: Open-Meteo.com (CC BY 4.0), ECMWF IFS, NOAA GFS, ERA5. Thresholds: Shah et al. 2024; Dahal & Hasegawa 2008. Crowd model: DM-Count (MIT). Demo photos: Wikimedia Commons (CC BY 4.0 / CC BY 2.5 / CC BY-SA 4.0), authors in the repo. Pilgrim counts, holding queues and delivery channels are SIMULATED; all CAP messages are status=Exercise.", options: {} },
    ], { x: 0.5, y: 4.85, w: 12.33, h: 1.4, fontSize: 12, color: COL.text });
    s.addNotes("I'm Ritik Bhardwaj, B.Tech IT at NIT Srinagar, a solo entry for J&K. I framed the problem, made the design decisions, validated the results and own this pitch.\n\nAI-use disclosure, as the rules require: I built YatraKavach with Claude Code from Anthropic as a coding and research agent. It did the web research and the sourced research report, most of the code, tests and documentation, and an independent code review that found two real bugs. I chose the problem and the J&K focus, set the requirements, approved every design decision and fix, and checked the results. My estimate: about 60-65% of the code and documents were generated by AI under my direction.\n\nData: OpenStreetMap (ODbL), Copernicus DEM via Open-Meteo, Open-Meteo rain (CC BY 4.0), DM-Count (MIT), Wikimedia Commons demo photos. Everything simulated is labelled SIMULATED.");
  }

  await pres.writeFile({ fileName: OUT });
  console.log("wrote", OUT);
}

main().catch((e) => { console.error(e); process.exit(1); });
