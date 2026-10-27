// Builds docs/pitch/JK_kavach_Deck.pptx on the HSC submission template (Template_HSC_Presentation_v7.0):
// 7 slides with the template's titles and pointers, its logo, "Team Name" oval and footer.
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
  navy: "1F4E8C", footer: "1F3864", red: "C62828", orange: "E65100", text: "1F2937", muted: "5B6472",
  tint: "F1F4F8", line: "D5DBE3", purple: "6A1B9A", white: "FFFFFF", redTint: "FDECEC",
  oval: "F8CBAD", ovalLine: "F4B183",
};
const FONT = "Aptos";
const REPO = "https://github.com/RitikBhardwaj-programmer/YatraKavach";

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
    x, y, w: 1.05, h: 0.24, fontFace: FONT, fontSize: 9, bold: true, color: COL.white, align: "center",
    valign: "middle", margin: 0, isTextBox: true,
    shape: "roundRect", rectRadius: 0.05, fill: { color: COL.purple },
  });
}

// Bold navy label: the template's pointer, kept word for word.
function pointer(slide, t, x, y, w) {
  text(slide, t, { x, y, w, h: 0.32, fontSize: 15, bold: true, color: COL.navy });
}

// Bulleted list; each item is a string or [boldLead, rest].
function bullets(slide, items, o) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    const para = { bullet: { indent: 12 }, breakLine: !last, paraSpaceAfter: 3 };
    if (Array.isArray(it)) {
      runs.push({ text: it[0], options: { bold: true, bullet: para.bullet, paraSpaceAfter: 3 } });
      runs.push({ text: it[1], options: { breakLine: !last } });
    } else {
      runs.push({ text: it, options: para });
    }
  });
  text(slide, runs, { fontSize: 13, ...o });
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in, same 16:9 as the template (960 x 540 pt)
  pres.author = "Team kavach (Ritik Bhardwaj)";
  pres.title = "YatraKavach: HSC 2027 submission";
  pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

  const common = [
    { image: { path: IMG("hsc-logo.jpg"), x: 10.85, y: 0.15, w: 2.0, h: 0.99 } },
    { text: { text: "@HSC submission- Template", options: { x: 4.67, y: 7.05, w: 4.0, h: 0.3, fontFace: FONT,
      fontSize: 12, color: COL.footer, align: "center", margin: 0, valign: "middle" } } },
  ];
  const title = { placeholder: { options: { name: "title", type: "title", x: 2.2, y: 0.5, w: 8.5, h: 0.75, fontFace: FONT,
    fontSize: 30, bold: true, color: COL.navy, align: "center", valign: "middle", margin: 0 }, text: "" } };
  const slideNumber = { x: 12.5, y: 7.05, w: 0.4, h: 0.3, fontFace: FONT, fontSize: 9, color: COL.muted, align: "right" };

  pres.defineSlideMaster({ title: "COVER", background: { color: COL.white }, objects: [...common, title], slideNumber });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: COL.white },
    objects: [...common, title],
    slideNumber,
  });
  const add = (t, master = "CONTENT") => {
    const s = pres.addSlide({ masterName: master });
    s.addText(t, { placeholder: "title" });
    if (master === "CONTENT") {
      // the template's "Team Name" oval (masters cannot hold an ellipse in pptxgenjs)
      s.addText("kavach", {
        shape: pres.shapes.OVAL, x: 0.2, y: 0.15, w: 1.73, h: 0.95, fill: { color: COL.oval },
        line: { color: COL.ovalLine, width: 1 }, shadow: { type: "outer", blur: 3, offset: 2, angle: 90, color: "808080", opacity: 0.4 },
        fontFace: FONT, fontSize: 18, color: "000000", align: "center", valign: "middle", margin: 0,
      });
    }
    return s;
  };

  // ---------- Slide 1: Cover Page ----------
  {
    const s = add("Cover Page", "COVER");
    const rows = [
      ["Problem Statement/Concept Title", "YatraKavach: landslide and crowd risk early warning for the Vaishno Devi pilgrim route"],
      ["Theme", "Theme 11: Disaster Mitigation & Resilience"],
      ["Team Name (Registered on portal)", "kavach"],
      ["Team ID(Registered on portal)", "HSC|JK|00032"],
      ["State/UT", "Jammu & Kashmir"],
    ];
    rows.forEach(([k, v], i) => {
      const y = 1.6 + i * 0.95;
      s.addShape(pres.shapes.OVAL, { x: 0.75, y: y + 0.12, w: 0.14, h: 0.14, fill: { color: COL.navy }, line: { color: COL.navy }, objectName: `cover-dot-${i + 1}` });
      text(s, k, { x: 1.1, y, w: 11.5, h: 0.38, fontSize: 18, bold: true, color: COL.navy });
      text(s, v, { x: 1.1, y: y + 0.4, w: 11.5, h: 0.42, fontSize: 18, color: COL.text });
    });
    text(s, "The warning existed. The decision did not.", { x: 1.1, y: 6.4, w: 11.5, h: 0.45, fontSize: 16, italic: true, color: COL.red });
    s.addNotes("YatraKavach, team kavach, HSC|JK|00032, Jammu & Kashmir, Theme 11 Disaster Mitigation & Resilience. One line: the warning existed, the decision did not.");
  }

  // ---------- Slide 2: Problem – Proposed Solution ----------
  {
    const s = add("Problem – Proposed Solution");
    pointer(s, "Core problem", 0.5, 1.3, 6);
    const events = [
      { date: "8 Jul 2022", place: "Amarnath cave", line: "Flash flood. No rain data from the upper reaches." },
      { date: "14 Aug 2025", place: "Chasoti, Machail yatra", line: "IMD alerts for the region; the yatra went on. About 61–64 dead." },
      { date: "26 Aug 2025", place: "Adhkuwari, Vaishno Devi", line: "Landslide at 14:40; at least 34 dead. Old track closed by ~12:00." },
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.5 + i * 4.18, w = 3.97;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.65, w, h: 1.2, rectRadius: 0.06, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: `event-${i + 1}` });
      text(s, [
        { text: events[i].date + "  ", options: { bold: true, color: COL.red } },
        { text: events[i].place, options: { bold: true, color: COL.navy, breakLine: true } },
        { text: events[i].line, options: { fontSize: 12 } },
      ], { x: x + 0.15, y: 1.75, w: w - 0.3, h: 1.0, fontSize: 13 });
    }
    text(s, [
      { text: "Each time, a warning reached some official. ", options: { bold: true, color: COL.navy } },
      { text: "Nobody turned it into “close this 500 m stretch, move these people, now”, and nobody can show who decided. Forecasts are district-scale; crowd systems (RFID, CCTV) have no hazard input." },
    ], { x: 0.5, y: 2.95, w: 12.33, h: 0.6, fontSize: 13 });

    pointer(s, "Proposed solution: YatraKavach", 0.5, 3.6, 6);
    const steps = ["Rain + slope", "Segment hazard", "+ people on segment", "Proposed action", "Officer approves", "CAP alert (en/hi/ur)"];
    const sw = 1.92, sg = 0.164;
    for (let i = 0; i < steps.length; i++) {
      const x = 0.5 + i * (sw + sg), last = i >= 4;
      s.addShape(i === 0 ? pres.shapes.PENTAGON : pres.shapes.CHEVRON, {
        x, y: 3.95, w: sw + 0.12, h: 0.6, fill: { color: last ? COL.red : COL.navy }, line: { color: COL.white, width: 1 }, objectName: `flow-${i + 1}`,
      });
      text(s, steps[i], { x: x + (i === 0 ? 0.1 : 0.4), y: 3.95, w: i === 0 ? sw - 0.3 : sw - 0.5, h: 0.6, fontSize: 12, bold: true, color: COL.white, align: "center", valign: "middle" });
    }
    const cols = [
      { h: "Detailed explanation of the proposed solution", b: [
        "35 segments (~500 m) on the three Vaishno Devi tracks.",
        "Hourly landslide hazard from 3 h, 24 h and 15-day rain against published Himalayan thresholds, stepped up on steep slopes.",
        "People per segment (SIMULATED RFID) and an AI crowd count from a camera frame (DM-Count).",
      ] },
      { h: "How does it address the problem", b: [
        "Turns a district warning into one proposal per track and level: hold, clear or reopen.",
        "A named officer approves; RED needs two officers; escalation after 10 min.",
        "Approved alert goes out as CAP 1.2 (the SACHET format) in English, Hindi and Urdu.",
      ] },
      { h: "Innovation and uniqueness of the solution", b: [
        "Segment hazard × people exposed now, not a district bulletin.",
        "Models the queue a hold creates: closing a track moves risk to the people below.",
        "Hash-chained audit log of who decided what, and when.",
      ] },
    ];
    for (let i = 0; i < 3; i++) {
      const x = 0.5 + i * 4.18, w = 3.97;
      text(s, cols[i].h, { x, y: 4.75, w, h: 0.5, fontSize: 13, bold: true, color: COL.navy });
      bullets(s, cols[i].b, { x, y: 5.25, w, h: 1.55, fontSize: 12 });
    }
    text(s, "Sources: Onmanorama, MoES (2022); ETV Bharat (2025); The Tribune (2025). Full list on the References slide.",
      { x: 0.5, y: 6.8, w: 9, h: 0.22, fontSize: 9, color: COL.muted });
    s.addNotes("In all three disasters a warning reached some official, but nobody turned it into 'close this stretch, move these people, now', and nobody can show who decided. YatraKavach splits the tracks into 35 segments, scores landslide hazard every hour from rain against published Himalayan thresholds, adds the people on each segment, and proposes one action per track and level. Nothing goes out automatically: a named officer approves, RED needs two officers, and every step is in a hash-chained audit log. The approved alert is CAP 1.2 in English, Hindi and Urdu.");
  }

  // ---------- Slide 3: Technical Approach ----------
  {
    const s = add("Technical Approach");
    pointer(s, "Technologies used", 0.5, 1.3, 7.4);
    bullets(s, [
      ["Backend: ", "Python 3.12, FastAPI, PostgreSQL 16 + PostGIS 3, pytest (258 tests pass)"],
      ["Console: ", "MapLibre GL web map, served by the API; Docker Compose to run it all"],
      ["Data: ", "OpenStreetMap tracks, Copernicus DEM slope, Open-Meteo rain (ECMWF, GFS, ERA5)"],
      ["AI crowd count: ", "DM-Count (MIT) on ONNX Runtime · Alerts: CAP 1.2 XML"],
    ], { x: 0.5, y: 1.65, w: 7.4, h: 1.25, fontSize: 12 });

    pointer(s, "Methodology and process for implementation", 0.5, 2.95, 7.4);
    const ih = 2.4, iw = ih * 2732 / 1536;
    s.addImage({ path: IMG("replay-0500-segment.png"), x: 0.5, y: 3.3, w: iw, h: ih, altText: "Console at 26 Aug 2025 05:00 IST: old track RED with the Why panel" });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.3, w: iw, h: ih, fill: { type: "none" }, line: { color: COL.line, width: 1 }, objectName: "frame-1" });
    text(s, "Working prototype: replay at 26 Aug 2025 05:00 IST, old track RED with the reasons in numbers",
      { x: 0.5, y: 3.3 + ih + 0.05, w: iw, h: 0.4, fontSize: 9, color: COL.muted });
    const mx = 0.5 + iw + 0.2, mw = 7.9 - mx;
    text(s, [
      { text: "1  Split tracks into segments (OSM + DEM)", options: { breakLine: true } },
      { text: "2  Score hazard every hour per segment", options: { breakLine: true } },
      { text: "3  Add people on the segment", options: { breakLine: true } },
      { text: "4  Propose → approve → CAP alert", options: { breakLine: true } },
      { text: "5  Validate: replay of 26 Aug 2025", options: {} },
    ], { x: mx, y: 3.3, w: mw, h: ih, fontSize: 12, paraSpaceAfter: 8, color: COL.navy, bold: true });

    // right column: links + AI use
    const rx = 8.2, rw = 4.63;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx, y: 1.3, w: rw, h: 1.95, rectRadius: 0.06, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: "links" });
    s.addImage({ data: await icon(fa.FaGithub, COL.navy), x: rx + 0.2, y: 1.45, w: 0.35, h: 0.35, altText: "GitHub" });
    text(s, "Github/Gitlab link", { x: rx + 0.65, y: 1.45, w: rw - 0.8, h: 0.35, fontSize: 14, bold: true, color: COL.navy, valign: "middle" });
    text(s, [{ text: "github.com/RitikBhardwaj-programmer/YatraKavach", options: { hyperlink: { url: REPO }, color: COL.navy, underline: true } }],
      { x: rx + 0.2, y: 1.85, w: rw - 0.3, h: 0.3, fontSize: 11 });
    s.addImage({ data: await icon(fa.FaPlayCircle, COL.navy), x: rx + 0.2, y: 2.25, w: 0.35, h: 0.35, altText: "Demo video" });
    text(s, "Demo Video", { x: rx + 0.65, y: 2.25, w: rw - 0.8, h: 0.35, fontSize: 14, bold: true, color: COL.navy, valign: "middle" });
    text(s, [
      { text: "JK_kavach_Video.mp4 (4:44), uploaded with this entry; also in the repo: ", options: {} },
      { text: "docs/pitch/JK_kavach_Video.mp4", options: { hyperlink: { url: REPO + "/blob/main/docs/pitch/JK_kavach_Video.mp4" }, color: COL.navy, underline: true } },
    ], { x: rx + 0.2, y: 2.62, w: rw - 0.3, h: 0.55, fontSize: 11 });

    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx, y: 3.4, w: rw, h: 3.3, rectRadius: 0.06, fill: { color: COL.white }, line: { color: COL.navy, width: 1.5 }, objectName: "ai-disclosure" });
    s.addImage({ data: await icon(fa.FaRobot, COL.navy), x: rx + 0.2, y: 3.55, w: 0.35, h: 0.35, altText: "AI-use disclosure" });
    text(s, "Extent of usage of AI tools", { x: rx + 0.65, y: 3.55, w: rw - 0.8, h: 0.35, fontSize: 14, bold: true, color: COL.navy, valign: "middle" });
    text(s, [
      { text: "Tool: ", options: { bold: true } }, { text: "Claude Code (Anthropic), as coding and research agent.", options: { breakLine: true } },
      { text: "AI did: ", options: { bold: true } }, { text: "research report, most code, tests and docs, an independent code review.", options: { breakLine: true } },
      { text: "Team did: ", options: { bold: true } }, { text: "chose the problem, set requirements, approved every design and fix, validated results.", options: { breakLine: true } },
      { text: "Share (team estimate): ", options: { bold: true, color: COL.red } }, { text: "about 60–65% of code and documents AI-generated under the team’s direction.", options: {} },
    ], { x: rx + 0.2, y: 4.0, w: rw - 0.4, h: 2.6, fontSize: 12, paraSpaceAfter: 5 });
    s.addNotes("Stack: Python 3.12 and FastAPI, PostgreSQL with PostGIS, a MapLibre web console, Docker Compose; 258 automated tests pass. Data: OpenStreetMap tracks, Copernicus DEM slope, Open-Meteo archived forecasts from ECMWF, GFS and ERA5. Crowd counts from a camera frame use DM-Count on ONNX Runtime. Method: segment, score hourly, add exposure, propose, approve, send CAP; validated by replaying 26 August 2025.\n\nAI-use disclosure, as the rules require: built with Claude Code from Anthropic as a coding and research agent. The team chose the problem, set the requirements, approved every design decision and fix, and checked the results. Team estimate: about 60-65% of code and documents AI-generated under the team's direction.");
  }

  // ---------- Slide 4: Impact Potential ----------
  {
    const s = add("Impact Potential");
    const lw = 6.2;
    pointer(s, "Potential impact on the target audience", 0.5, 1.3, lw);
    bullets(s, [
      "Pilgrims on mountain tracks: Vaishno Devi alone allows up to 50,000 a day.",
      ["Replay of 26 Aug 2025: ", "old track RED 1.5–9.5 h before the slide, depending on the weather model."],
      ["If held at the first ORANGE: ", "0 pilgrims on the slide segment at 14:00 instead of 674 (SIMULATED)."],
    ], { x: 0.5, y: 1.65, w: lw, h: 1.45, fontSize: 12 });
    pointer(s, "Benefits of the solution (social, economic, etc.)", 0.5, 3.15, lw);
    bullets(s, [
      ["Social: ", "earlier, segment-level action to cut disaster deaths (SDG 11.5, SDG 3)."],
      ["Economic: ", "hold only the segments at risk instead of the whole route (aim, to test in a pilot)."],
      ["Governance: ", "every alert carries a named approver and time; the log is tamper-evident."],
    ], { x: 0.5, y: 3.5, w: lw, h: 1.4, fontSize: 12 });
    pointer(s, "Stakeholders", 0.5, 4.95, lw);
    bullets(s, [
      "Shrine board (SMVDSB) control room, J&K SDMA and district administration",
      "SDRF and police on duty; IMD and GSI as data sources; NDMA SACHET for delivery",
      "Pony and palki operators, shopkeepers on the track, pilgrims and families",
    ], { x: 0.5, y: 5.3, w: lw, h: 1.45, fontSize: 12 });

    const hdr = (t) => ({ text: t, options: { bold: true, color: COL.white, fill: { color: COL.navy } } });
    const rows = [
      [hdr("KPI"), hdr("Prototype result"), hdr("Pilot target")],
      ["Lead time of RED before a slide", "1.5–9.5 h (3 models)", "≥ 3 h with radar"],
      ["Alerts with named approver and time", "100%", "100%"],
      ["Open alerts at peak (26 Aug, 14:00)", "6: one per track and level", "≤ 1 per track and level"],
      ["Pilgrims on slide segment at 14:00 (SIMULATED)", "674 → 0 if held at first ORANGE", "Decision within 1 h of ORANGE"],
      ["Camera crowd count error", "MAE 60 / image (ShanghaiTech A)", "Validated on SMVDSB CCTV"],
    ];
    s.addTable(rows, {
      x: 6.95, y: 1.3, w: 5.88, colW: [2.2, 2.03, 1.65], fontFace: FONT, fontSize: 11, color: COL.text,
      border: { type: "solid", pt: 0.75, color: COL.line }, valign: "middle", margin: [3, 5, 3, 5],
      rowH: [0.35, 0.5, 0.45, 0.5, 0.6, 0.55],
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.95, y: 4.65, w: 5.88, h: 1.6, rectRadius: 0.06, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: "scale" });
    text(s, [
      { text: "Scale: ", options: { bold: true, color: COL.navy } },
      { text: "the same engine works for Amarnath, Machail, Char Dham and Sabarimala; only segments and thresholds change.", options: { breakLine: true } },
      { text: "Sustainable: ", options: { bold: true, color: COL.navy } },
      { text: "open source (MIT), one small server, fits shrine-board control rooms and SDMA. Languages are templates; add Dogri, Kashmiri, Pahari with native speakers.", options: {} },
    ], { x: 7.15, y: 4.8, w: 5.5, h: 1.8, fontSize: 12, paraSpaceAfter: 6 });
    s.addNotes("Who benefits: pilgrims (Vaishno Devi cap 50,000 a day), pony and palki operators, shopkeepers, SDRF and police. In the 26 Aug 2025 replay, the old track reaches RED 1.5 to 9.5 hours before the 14:40 slide, depending on the model. With SIMULATED pilgrims, a hold at the first ORANGE leaves 0 people on the slide segment at 14:00 instead of 674. Benefits: earlier segment-level action, holding only segments at risk, and a named approver for every alert. Stakeholders: shrine board, SDMA, district administration, SDRF, police, IMD, GSI, NDMA SACHET.");
  }

  // ---------- Slide 5: Feasibility and Risk Analysis ----------
  {
    const s = add("Feasibility and Risk Analysis");
    pointer(s, "Analysis of the feasibility of the solution", 0.5, 1.3, 12);
    const tiles = [
      { ic: fa.FaCheckCircle, h: "Working prototype", b: "End to end: hazard, crowd, approval, CAP, audit; 258 tests pass" },
      { ic: fa.FaDatabase, h: "Open data only", b: "OSM, Copernicus DEM and Open-Meteo; no paid feeds" },
      { ic: fa.FaServer, h: "One small server", b: "Docker Compose; open source (MIT)" },
      { ic: fa.FaBroadcastTower, h: "Fits existing channels", b: "CAP 1.2 is the format SACHET already uses" },
    ];
    for (let i = 0; i < 4; i++) {
      const x = 0.5 + i * 3.13, w = 2.95;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.65, w, h: 1.1, rectRadius: 0.06, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: `tile-${i + 1}` });
      s.addImage({ data: await icon(tiles[i].ic, COL.navy), x: x + 0.15, y: 1.75, w: 0.3, h: 0.3, altText: tiles[i].h });
      text(s, tiles[i].h, { x: x + 0.55, y: 1.75, w: w - 0.65, h: 0.3, fontSize: 13, bold: true, color: COL.navy, valign: "middle" });
      text(s, tiles[i].b, { x: x + 0.15, y: 2.1, w: w - 0.3, h: 0.6, fontSize: 11 });
    }
    text(s, [
      { text: "Roadmap: ", options: { bold: true, color: COL.navy } },
      { text: "1 Pilot for one monsoon, read-only, with the SMVDSB control room and SDRF → 2 Calibrate with local slide records, IMD radar, 3–5 rain gauges, GSI layer → 3 Integrate RFID, CCTV and approved CAP to SACHET, app and PA." },
    ], { x: 0.5, y: 2.85, w: 12.33, h: 0.55, fontSize: 12 });

    const hdr = (t) => ({ text: t, options: { bold: true, color: COL.white, fill: { color: COL.navy } } });
    const rows = [
      [hdr("Potential challenges and risks"), hdr("Strategies for overcoming these challenges")],
      ["Rain thresholds come from NH-44 and Nepal studies, not calibrated for these tracks", "Read-only pilot for one monsoon; calibrate with local slide records and rain gauges"],
      ["Forecast rain is on a 9–25 km grid; lead time varies by model (1.5–9.5 h)", "Add the IMD radar feed; show the model spread to officers, not one number"],
      ["Alert fatigue: rules on monsoon rain can fire all season", "One alert per track and level: 27 → 6 open alerts in the replay (measured)"],
      ["A hold moves the risk: 5.4 persons/m² at the Katra gate (SIMULATED)", "The simulator shows the queue before approval; staggered holds"],
      ["Crowd data (RFID, CCTV) is SIMULATED today", "Data-sharing MoU with the shrine board; label stays until real data flows"],
      ["Late or wrong decisions", "Two officers for RED, escalation after 10 min, break-glass with a reason, audit log"],
    ];
    s.addTable(rows, {
      x: 0.5, y: 3.5, w: 12.33, colW: [6.0, 6.33], fontFace: FONT, fontSize: 11, color: COL.text,
      border: { type: "solid", pt: 0.75, color: COL.line }, valign: "middle", margin: [2, 6, 2, 6],
      rowH: [0.34, 0.47, 0.47, 0.47, 0.47, 0.47, 0.47],
    });
    s.addNotes("Feasibility: the prototype works end to end and 258 tests pass; it uses only open data and runs on one small server; CAP 1.2 fits SACHET. Roadmap: one read-only monsoon pilot, then calibration, then integration. Risks said openly: thresholds are not calibrated for these tracks; the rain grid is coarse and lead time depends on the model; rules on monsoon rain can flood officers, so alerts are grouped per track and level (27 to 6 in the replay); a hold moves the risk to the gate below; crowd data is simulated until a data-sharing MoU.");
  }

  // ---------- Slide 6: Team ----------
  {
    const s = add("Team");
    pointer(s, "Team Composition", 0.5, 1.3, 5);
    s.addShape(pres.shapes.OVAL, { x: 0.5, y: 1.7, w: 1.0, h: 1.0, fill: { color: COL.navy }, line: { color: COL.navy }, objectName: "team-avatar" });
    text(s, "RB", { x: 0.5, y: 1.7, w: 1.0, h: 1.0, fontSize: 24, bold: true, color: COL.white, align: "center", valign: "middle" });
    text(s, "Ritik Bhardwaj (Team Lead)", { x: 1.7, y: 1.75, w: 4.2, h: 0.4, fontSize: 17, bold: true, color: COL.navy });
    text(s, "B.Tech Information Technology Engineering, 3rd year, NIT Srinagar · solo entry for J&K", { x: 1.7, y: 2.15, w: 4.2, h: 0.6, fontSize: 12, color: COL.muted });

    pointer(s, "Roles", 0.5, 3.0, 5.4);
    bullets(s, [
      "Problem framing and the J&K focus",
      "Requirements, architecture and every design decision",
      "Directing the AI agent (code, research, review) and checking its work",
      "Validation of the replay results; pitch and demo",
    ], { x: 0.5, y: 3.35, w: 5.4, h: 1.6, fontSize: 13 });

    pointer(s, "Challenges", 6.4, 1.3, 6.4);
    bullets(s, [
      ["Time: ", "one person, about four days from idea to submission."],
      ["Data gap: ", "the Machail trek is incomplete in OpenStreetMap, so scope was cut to Vaishno Devi (35 segments)."],
      ["Honest replay: ", "the first version used the slide it predicted; fixed by dating every past-slide factor."],
      ["Alert flood: ", "27 open alerts in the first replay; grouping per track and level cut it to 6."],
    ], { x: 6.4, y: 1.65, w: 6.43, h: 2.3, fontSize: 13 });

    pointer(s, "Any other that the team would like to share about their journey", 6.4, 3.75, 6.43);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.4, y: 4.15, w: 6.43, h: 1.55, rectRadius: 0.06, fill: { color: COL.tint }, line: { color: COL.tint }, objectName: "journey" });
    text(s, [
      { text: "“The warning existed. The decision did not.” ", options: { bold: true, color: COL.red, breakLine: true } },
      { text: "Reading the reports on the 2025 disasters showed the gap was not a better forecast but the step from a warning to an owned, recorded decision. So I built that step, and I show the weak case too: with two of three weather models the lead time is only about 1.5 h.", options: {} },
    ], { x: 6.6, y: 4.3, w: 6.03, h: 1.35, fontSize: 13, paraSpaceAfter: 6 });
    s.addNotes("I'm Ritik Bhardwaj, B.Tech IT at NIT Srinagar, a solo entry for J&K. I framed the problem, made the design decisions, directed the AI agent and checked its work, validated the results and own this pitch. Challenges: time, the missing Machail trek in OSM, an early replay that used the event it predicted, and an alert flood that grouping fixed. Journey: the gap is the decision, not the forecast, and I show the weak case openly.");
  }

  // ---------- Slide 7: References ----------
  {
    const s = add("References");
    pointer(s, "Details / Links of the reference and research work", 0.5, 1.3, 12);
    const ref = (label, url) => [
      { text: label + ": ", options: { bold: true } },
      { text: url.replace(/^https?:\/\//, ""), options: { hyperlink: { url }, color: COL.navy } },
    ];
    const col = (items, x, w) => {
      const runs = [];
      items.forEach((it, i) => {
        const last = i === items.length - 1;
        if (typeof it === "string") {
          runs.push({ text: it, options: { bold: true, color: COL.navy, fontSize: 12, breakLine: true } });
        } else {
          const [a, b] = ref(it[0], it[1]);
          runs.push(a);
          runs.push({ ...b, options: { ...b.options, breakLine: !last } });
        }
      });
      text(s, runs, { x, y: 1.7, w, h: 5.1, fontSize: 9, paraSpaceAfter: 3 });
    };
    col([
      "Disasters",
      ["Amarnath 2022, Onmanorama", "https://onmanorama.com/news/india/2022/07/09/amarnath-flash-floods-not-caused-by-cloudburst-imd.html"],
      ["Amarnath 2022, MoES", "https://www.moes.gov.in/sites/default/files/RS-in-English-1300-28-07-2022.pdf"],
      ["Chasoti 2025, ETV Bharat", "https://www.etvbharat.com/en/!bharat/kishtwar-cloudburst-exposes-laxity-in-response-to-weather-warnings-in-jammu-kashmir-enn25082003499"],
      ["Vaishno Devi 2025, Tribune", "https://www.tribuneindia.com/news/j-k/no-lapses-vaishno-devi-board-calls-landslip-tragedy-unforeseeable"],
      ["Vaishno Devi probe, Tribune", "https://www.tribuneindia.com/news/j-k/deadline-over-vaishno-devi-landslip-probe-report-not-out-yet"],
      "Existing systems",
      ["SMVDSB 700+ cameras, Tribune", "https://www.tribuneindia.com/news/j-k/vaishno-devi-shrine-sets-up-dedicated-network-of-over-700-cameras-for-e-surveillance-474077"],
      ["GSI landslide bulletins, Business Standard", "https://www.business-standard.com/india-news/gsi-plans-to-use-ai-to-develop-robust-landslide-forecasting-model-dg-125072000196_1.html"],
      ["NDMA cell broadcast, ETV Bharat", "https://www.etvbharat.com/en/bharat/ndma-tests-cell-broadcast-message-to-alert-citizens-on-severe-disaster-enn26050201915"],
      ["CAP 1.2, ITU-T X.1303bis", "https://www.itu.int/wftp3/Public/t/fl/itu-t/x/x1303bis/2014/CAP-1-2.html"],
      ["Early Warnings for All, WMO", "https://wmo.int/resources/wmo-bulletin/wmo-bulletin-vol-72-1-2023/overview-of-early-warnings-all-executive-action-plan-2023-2027"],
    ], 0.5, 6.0);
    col([
      "Science and models",
      ["J&K rain thresholds, Shah et al. 2024", "https://ideas.repec.org/a/spr/nathaz/v120y2024i2d10.1007_s11069-023-06254-w.html"],
      ["Nepal I–D threshold, Dahal & Hasegawa 2008", "https://dpnet.org.np/uploads/files/rainfall%20threshold2008%202021-09-17%2006-39-49.pdf"],
      ["Crowd density limits, G. Keith Still", "https://gkstill.com/Support/crowd-flow/fruin/Fruin1.html"],
      ["Crowd turbulence, Helbing et al.", "https://arxiv.org/abs/physics/0701203"],
      ["DM-Count crowd model (MIT)", "https://github.com/cvlab-stonybrook/DM-Count"],
      "Data used (attribution)",
      ["Tracks © OpenStreetMap contributors (ODbL)", "https://www.openstreetmap.org/copyright"],
      ["Rain + Copernicus DEM, Open-Meteo (CC BY 4.0)", "https://open-meteo.com/en/docs/historical-forecast-api"],
      "Project",
      ["Code, research notes, replay data", REPO],
    ], 6.83, 6.0);
    text(s, "Full sourced research: docs/research.md and research_notes/ in the repo. Pilgrim counts, holding queues and delivery channels are SIMULATED; all CAP messages are status=Exercise. Demo photos: Wikimedia Commons, authors in the repo.",
      { x: 0.5, y: 6.6, w: 12.33, h: 0.4, fontSize: 9, color: COL.muted });
    s.addNotes("All claims trace to these sources; the full sourced research is in docs/research.md in the public repo.");
  }

  await pres.writeFile({ fileName: OUT });
  console.log("wrote", OUT);
}

main().catch((e) => { console.error(e); process.exit(1); });
