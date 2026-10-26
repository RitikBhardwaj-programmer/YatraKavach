#!/usr/bin/env node
/* Record the draft demo video (docs/pitch/video-script.md) from the running console.

   Drives the officer console with Playwright (headless Chromium, 1280x720 CSS px at 1.5x = 1920x1080),
   records it with the DevTools screencast (device-pixel frames; Playwright's recordVideo would capture
   only 1280x720), renders title/problem/roadmap/closing cards, burns in captions with ffmpeg, and writes
   docs/pitch/JK_kavach_Video.mp4 plus a matching .srt.

   Needs: the stack from README.md on a FRESH database, replayed with
   until=2025-08-26T14:00:00+05:30 (approving alerts changes the DB, so reset before each take);
   Node with `playwright` (npm i playwright), ffmpeg/ffprobe with libx264 and libass.

   Usage:  node scripts/record_demo.js
   Env:    YK_URL        console URL (default http://localhost:8000/)
           YK_OUT        output MP4 (default docs/pitch/JK_kavach_Video.mp4)
           YK_WORK       scratch dir (default <tmp>/yk-demo)
           MAPLIBRE_DIR  optional local copy of maplibre-gl@4.7.1/dist, served for the unpkg URLs
                         (only for machines that cannot reach unpkg.com)
           YK_NO_TILES   set to 1 to fail OSM basemap tile requests at once (machines that cannot reach
                         tile.openstreetmap.org; otherwise the map's load event can stall). No basemap then.
*/
'use strict';
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const URL_ = process.env.YK_URL || 'http://localhost:8000/';
const OUT = path.resolve(process.env.YK_OUT || path.join(ROOT, 'docs/pitch/JK_kavach_Video.mp4'));
const WORK = path.resolve(process.env.YK_WORK || path.join(os.tmpdir(), 'yk-demo'));
const MAPLIBRE_DIR = process.env.MAPLIBRE_DIR || '';
const NO_TILES = process.env.YK_NO_TILES === '1';

const VIEW = { width: 1280, height: 720 };   // CSS px; x1.5 = 1920x1080 frames
const SCALE = 1.5;
const W = 1920, H = 1080, FPS = 30;
// Console frames are shrunk to 90 % so the caption band below does not hide the replay bar.
const INNER_W = 1728, INNER_H = 972, BAND_H = H - INNER_H;
const BG = '#0b1f3a';
const KEY_STEP_MS = 380;   // one replay hour per key press, slow enough that each hour renders

/* ---------- cards (full-frame, no caption band) ---------- */
const CARD_CSS = `
  * { box-sizing: border-box; margin: 0; }
  body { width: 1280px; height: 720px; background: ${BG}; color: #fff; font-family: 'Noto Sans', 'DejaVu Sans', sans-serif;
         padding: 56px 72px; display: flex; flex-direction: column; justify-content: center; gap: 22px; }
  h1 { font-size: 64px; letter-spacing: .5px; } h2 { font-size: 40px; } p, li { font-size: 24px; line-height: 1.45; }
  .sub { font-size: 28px; opacity: .85; } .muted { opacity: .7; font-size: 18px; }
  .gap { border: 4px dashed #f2c200; color: #f2c200; padding: 18px 24px; border-radius: 10px; font-size: 26px; }
  .gap b { font-size: 30px; } ul { padding-left: 26px; } .ev { display: grid; grid-template-columns: 250px 1fr; gap: 16px 22px; }
  .ev .d { color: #ffb4a8; font-weight: 700; font-size: 24px; } .ev .t { font-size: 24px; line-height: 1.4; }
  .key { background: #fff1; border-left: 6px solid #ef6c00; padding: 14px 20px; font-size: 25px; }
  .flow { display: flex; align-items: stretch; gap: 18px; } .box { flex: 1; background: #fff1; border-radius: 10px; padding: 16px 18px; }
  .box h3 { font-size: 22px; color: #f2c200; margin-bottom: 8px; } .box p { font-size: 20px; line-height: 1.4; }
  .core { background: #c62828; } .core h3 { color: #fff; } .arrow { align-self: center; font-size: 40px; }
  .attr { font-size: 16px; line-height: 1.5; opacity: .85; }`;

const CARDS = {
  intro: { seconds: 25, html: `
    <h1>YatraKavach</h1>
    <p class="sub">Team kavach · Jammu &amp; Kashmir · Hack for Social Cause 2027 (Theme 11: Disaster Mitigation &amp; Resilience)</p>
    <p class="sub">Which 500 m stretch of a pilgrim track is dangerous, how many people are on it,
      and who decided, in time and on record.</p>
    <div class="gap"><b>INTRO GAP · 0:00–0:25</b><br>Replace with your face and voice: team intro
      (video-script.md, 0:00–0:20).</div>` },
  problem: { seconds: 30, html: `
    <h2>The warning existed. The decision did not.</h2>
    <div class="ev">
      <div class="d">26 Aug 2025, 14:40</div><div class="t">Adhkuwari, Vaishno Devi: landslide on the old track; at least 34 pilgrims dead.</div>
      <div class="d">14 Aug 2025</div><div class="t">Chasoti, Machail yatra: IMD alerts existed for the region; the yatra went on; about 61–64 dead.</div>
      <div class="d">8 Jul 2022</div><div class="t">Amarnath cave: flash flood; no rain data from the upper reaches.</div>
    </div>
    <div class="key">Missing each time: the step from a district alert to
      “close this 500 m stretch, move these people, now”, with a record of who decided.</div>
    <p class="muted">Sources: docs/research.md in the repository.</p>` },
  roadmap: { seconds: 15, html: `
    <h2>Integrate, not replace</h2>
    <div class="flow">
      <div class="box"><h3>Reads</h3><p>IMD forecasts and radar · GSI bulletins · SMVDSB RFID gate counts · CCTV density</p></div>
      <div class="arrow">→</div>
      <div class="box core"><h3>YatraKavach</h3><p>500 m segments · hazard + people · proposal · named-officer approval · audit log</p></div>
      <div class="arrow">→</div>
      <div class="box"><h3>Hands over</h3><p>Approved CAP alert to NDMA SACHET · shrine-board app · camp PA</p></div>
    </div>
    <ul><li><b>Next: a one-monsoon pilot</b> with the shrine board (SMVDSB) control room and SDRF: read-only,
      no public alerts, compare proposals with real decisions.</li>
      <li>Then calibrate (local slide records, IMD radar, rain gauges on the track) and integrate.</li></ul>` },
  closing: { seconds: 15, html: `
    <h1>YatraKavach</h1>
    <p class="sub">Open source (MIT): github.com/RitikBhardwaj-programmer/YatraKavach</p>
    <p>Built with AI assistance (Claude Code); see the AI-use disclosure in the README. Thank you.</p>
    <p class="attr"><b>Data and credits.</b> Trails © OpenStreetMap contributors (ODbL) ·
      Weather data by Open-Meteo.com (CC BY 4.0): ECMWF IFS 0.25, NOAA GFS historical forecasts, ERA5 ·
      Elevation: Copernicus DEM GLO-90 via Open-Meteo · Crowd-count model: DM-Count (Wang et al., NeurIPS 2020, MIT) ·
      Demo photo: “2019 Feb 04 - Kumbh Mela - Mauni Amavasya Crowd 10” by Michael T Balonek, CC BY-SA 4.0,
      Wikimedia Commons · Map library: MapLibre GL JS (BSD-3-Clause).</p>
    <p class="attr">Crowd numbers, holding queues and alert delivery are SIMULATED. CAP messages are status=Exercise.
      Thresholds are published Himalayan values, not calibrated for these tracks.</p>` },
};
const ORDER_BEFORE = ['intro', 'problem'];
const ORDER_AFTER = ['roadmap', 'closing'];

/* ---------- console steps (captions follow video-script.md) ---------- */
// Each step runs, then waits until `seconds` have passed. Caption `at` is seconds from the step start.
const STEPS = [
  { id: 'overview', seconds: 25, captions: [
    [0, 'Officer console · the tracks are cut into 35 segments of about 500 m: Katra–Adhkuwari trunk, old track, Himkoti track'],
    [9, 'Every hour each segment gets a hazard level from rain over 3 h, 24 h and 15 days (published Himalayan thresholds), plus slope'],
    [18, 'Everything shown is open data; crowd numbers are SIMULATED and labelled so'],
  ], run: async (p) => {
    await hover(p, '.mode button[data-mode="replay"]');
    await p.waitForTimeout(3000);
    await hover(p, '#legend');
    await p.waitForTimeout(5000);
    await hover(p, '#situation');
    await p.waitForTimeout(5000);
    await hover(p, '#kpi-lead');
  } },
  { id: 'replay', seconds: 45, captions: [
    [0, 'Replay of the archived GFS forecasts · moving the slider back to 25 Aug 2025, 15:00 IST'],
    [9, '25 Aug, 15:00 IST: Adhkuwari segment VD-OLD-01 (old track) turns ORANGE'],
    [19, '26 Aug, 05:00 IST: VD-OLD-01 turns RED, about 9.5 hours before the 14:40 slide'],
    [28, '“Why”: 24 h rain against the threshold, slope; the history strip shows how the level rose'],
    [37, 'With the ECMWF forecast the first RED comes only ~1.5 h before (top bar): coarse models miss single storms, so a human decides'],
  ], run: async (p, ctx) => {
    await clickThumb(p);
    await stepSlider(p, '2025-08-25T15:00:00+05:30');
    await p.waitForTimeout(1500);
    await zoomAt(p, 'VD-OLD-01', -1);
    ctx.oldTrackClick = await clickSegment(p, 'VD-OLD-01');
    await p.waitForTimeout(5000);
    await clickThumb(p);
    await stepSlider(p, '2025-08-26T05:00:00+05:30');
    await p.waitForTimeout(3500);
    await hover(p, '#segment-body .why');
    await p.waitForTimeout(8000);
    await hover(p, '#kpi-lead');
  } },
  { id: 'queue', seconds: 25, captions: [
    [0, '26 Aug, 07:00 IST · VD-TRUNK-01 at the Katra gate: the ascent is stopped and pilgrims queue below (SIMULATED holding-area scenario)'],
    [11, 'About 5.4 people per m² (crowd ORANGE) inside a segment that is itself RED: the system weighs hazard and people together'],
  ], run: async (p, ctx) => {
    await clickThumb(p);
    await stepSlider(p, '2025-08-26T07:00:00+05:30');
    await p.waitForTimeout(1200);
    await zoomAt(p, 'VD-OLD-01', 1);
    ctx.trunkClick = await clickSegment(p, 'VD-TRUNK-01');
    await p.waitForTimeout(3000);
    await hover(p, '#segment-body .kv');
    await p.waitForTimeout(6000);
    await hover(p, '#segment-body .why');
  } },
  { id: 'alerts', seconds: 50, captions: [
    [0, 'Alerts tab · the system only proposes, one alert per track; RED needs two different officers'],
    [8, 'Demo Officer A approves the RED “clear the old track” alert: 1 of 2'],
    [15, 'The same officer cannot approve twice: Approve is now blocked for Officer A'],
    [22, 'Demo Officer B approves → SENT as a CAP 1.2 alert, the format NDMA SACHET uses (delivery SIMULATED)'],
    [31, 'CAP XML in English, Hindi and Urdu, status = Exercise'],
    [41, 'Every step is written to a hash-chained audit log nobody can edit · “Audit chain verified” in the top bar'],
  ], run: async (p, ctx) => {
    await clickEl(p, '#tab-alerts');
    const card = p.locator('#alerts-list article.alert.lvl-edge-3', { hasText: 'VD-OLD-01' }).first();
    await card.scrollIntoViewIfNeeded();
    ctx.alertId = await card.getAttribute('data-id');
    await p.waitForTimeout(2500);
    await pickOption(p, '#officer', 'off-1');
    await p.waitForTimeout(2500);
    await clickEl(p, `article.alert[data-id="${ctx.alertId}"] button[data-verb="approve"]`);
    await p.waitForTimeout(4500);
    await hover(p, `article.alert[data-id="${ctx.alertId}"] button[data-verb="approve"]`);
    ctx.blocked = await p.isDisabled(`article.alert[data-id="${ctx.alertId}"] button[data-verb="approve"]`);
    await waitUntil(p, ctx, 22);
    await pickOption(p, '#officer', 'off-2');
    await p.waitForTimeout(1500);
    await clickEl(p, `article.alert[data-id="${ctx.alertId}"] button[data-verb="approve"]`);
    await p.waitForTimeout(3000);
    ctx.alertState = (await p.textContent(`article.alert[data-id="${ctx.alertId}"] .state`)).trim();
    await waitUntil(p, ctx, 30);
    await clickEl(p, `article.alert[data-id="${ctx.alertId}"] details[data-kind="cap"] summary`);
    await p.waitForTimeout(1500);
    await scrollToText(p, `article.alert[data-id="${ctx.alertId}"] pre.xml`, 'hi-IN');
    await p.waitForTimeout(4500);
    await scrollToText(p, `article.alert[data-id="${ctx.alertId}"] pre.xml`, 'ur-IN');
    await waitUntil(p, ctx, 41);
    await clickEl(p, `article.alert[data-id="${ctx.alertId}"] details[data-kind="audit"] summary`);
    await p.waitForTimeout(1000);
    await p.locator(`article.alert[data-id="${ctx.alertId}"] .audit`).scrollIntoViewIfNeeded();
    await p.waitForTimeout(3500);
    await hover(p, '#audit-badge');
  } },
  { id: 'whatif', seconds: 30, captions: [
    [0, 'What-if (SIMULATED crowd): pilgrims on the slide segment at 14:00 · no action 674 · hold at first ORANGE 0 · at first RED 93 (GFS)'],
    [12, 'ECMWF: hold at first ORANGE is still 0 (in every model); its RED came at 13:00, so a hold then leaves 674'],
    [21, 'A hold at about 12:00 at the Katra gate comes too late for this segment: those pilgrims had already passed it'],
  ], run: async (p) => {
    await clickEl(p, '#tab-impact');
    await p.waitForSelector('#impact-body .bars');
    await p.waitForTimeout(3000);
    await hover(p, '#impact-body .bars');
    await p.waitForTimeout(8000);
    await pickOption(p, '#impact-source', 'ecmwf_ifs025');
    await p.waitForSelector('#impact-body .bars');
    await p.waitForTimeout(8000);
    await hover(p, '#impact-body .bars li:last-child');
  } },
  { id: 'camera', seconds: 24, captions: [
    [0, 'Camera tab · crowd numbers can also come from cameras: a published AI crowd-counting model (DM-Count) on a CPU'],
    [11, (c) => `Festival photo, not a Vaishno Devi camera: ${c.camCount ?? 'about 340'} people counted → density → level · average error about 60 people per image`],
  ], run: async (p, ctx) => {
    await clickEl(p, '#tab-camera');
    await p.waitForTimeout(1500);
    await pickOption(p, '#sample-select', 'kumbh_2019_mauni_amavasya.jpg');
    await p.waitForSelector('#cam-result .kv-cam', { timeout: 30000 });
    ctx.camCount = (await p.textContent('#cam-result .kv-cam .big')).trim();
    await p.waitForTimeout(1500);
    await hover(p, '#cam-result .kv-cam');
  } },
];

/* ---------- browser helpers ---------- */
const CURSOR_JS = `
  addEventListener('DOMContentLoaded', () => {
    const c = document.createElement('div');
    c.id = 'demo-cursor';
    c.style.cssText = 'position:fixed;z-index:99999;width:22px;height:22px;margin:-11px 0 0 -11px;border-radius:50%;'
      + 'border:3px solid #ef6c00;background:#ef6c0033;pointer-events:none;left:-50px;top:-50px;transition:transform .12s';
    document.body.appendChild(c);
    addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => { c.style.transform = 'scale(.6)'; }, true);
    addEventListener('mouseup', () => { c.style.transform = ''; }, true);
  });`;

async function center(p, sel) {
  const el = p.locator(sel).first();
  await el.scrollIntoViewIfNeeded();
  const b = await el.boundingBox();
  if (!b) throw new Error(`not visible: ${sel}`);
  return { x: b.x + b.width / 2, y: b.y + Math.min(b.height / 2, 30) };
}
async function hover(p, sel) {
  const { x, y } = await center(p, sel);
  await p.mouse.move(x, y, { steps: 20 });
}
async function clickEl(p, sel) {
  const { x, y } = await center(p, sel);
  await p.mouse.move(x, y, { steps: 20 });
  await p.waitForTimeout(250);
  await p.mouse.click(x, y);
}
async function pickOption(p, sel, value) {
  await hover(p, sel);
  await p.waitForTimeout(400);
  await p.selectOption(sel, value);
}
// Click on the slider thumb (not the track, which would jump the replay time) to focus it.
async function clickThumb(p) {
  const pt = await p.evaluate(() => {
    const el = document.querySelector('#slider');
    const r = el.getBoundingClientRect();
    const thumb = 16; // px, approximate thumb width
    return { x: r.left + thumb / 2 + (state.idx / Number(el.max)) * (r.width - thumb), y: r.top + r.height / 2 };
  });
  await p.mouse.move(pt.x, pt.y, { steps: 20 });
  await p.waitForTimeout(250);
  await p.mouse.click(pt.x, pt.y);
}
// Move the replay slider one hour per arrow key until it reaches `ts` (the slider is focused).
async function stepSlider(p, ts) {
  const target = await p.evaluate((t) => state.times.findIndex((x) => Date.parse(x) === Date.parse(t)), ts);
  if (target < 0) throw new Error(`replay time not on the timeline: ${ts}`);
  for (;;) {
    const idx = await p.evaluate(() => state.idx);
    if (idx === target) break;
    await p.keyboard.press(idx > target ? 'ArrowLeft' : 'ArrowRight');
    await p.waitForTimeout(KEY_STEP_MS);
  }
  await p.waitForFunction((t) => state.fc?.features[0]?.properties.ts
    && Date.parse(state.fc.features[0].properties.ts) === Date.parse(t), ts, { polling: 100 });
}
// Click the middle of a segment on the map, like a user would; fall back to the segment picker.
async function clickSegment(p, id) {
  const pt = await segmentPoint(p, id);
  await p.mouse.move(pt.x, pt.y, { steps: 25 });
  await p.waitForTimeout(300);
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(500);
  if (await p.evaluate(() => state.selected) === id) return 'map';
  await clickEl(p, '#tab-segment');
  await pickOption(p, '#segment-select', id);
  return 'picker';
}
// Scroll-zoom the map in (dir -1) or out (dir 1) around a segment, like a user with a mouse wheel.
async function zoomAt(p, id, dir) {
  const pt = await segmentPoint(p, id);
  await p.mouse.move(pt.x, pt.y, { steps: 20 });
  for (let i = 0; i < 4; i++) {
    await p.mouse.wheel(0, dir * 250);
    await p.waitForTimeout(350);
  }
  await p.waitForFunction(() => !state.map.isMoving(), null, { polling: 100 });
  await p.waitForTimeout(600);
}
async function segmentPoint(p, id) {
  return p.evaluate((sid) => {
    // The vertex of this segment that lies farthest (on screen) from all other segments, so the click hits it.
    const proj = (c) => state.map.project(c);
    const others = state.fc.features.filter((x) => x.properties.id !== sid).flatMap((x) => x.geometry.coordinates.map(proj));
    const own = state.fc.features.find((x) => x.properties.id === sid).geometry.coordinates.map(proj);
    let best = own[0], bestD = -1;
    for (const q of own) {
      const d = Math.min(...others.map((o) => Math.hypot(o.x - q.x, o.y - q.y)));
      if (d > bestD) { bestD = d; best = q; }
    }
    const r = state.map.getCanvas().getBoundingClientRect();
    return { x: r.left + best.x, y: r.top + best.y };
  }, id);
}
// Scroll a <pre> (and the side column) so the line holding `text` is in view.
async function scrollToText(p, sel, text) {
  await p.evaluate(([s, t]) => {
    const pre = document.querySelector(s);
    const node = pre.firstChild;
    const i = node.textContent.indexOf(t);
    if (i < 0) return;
    const r = document.createRange();
    r.setStart(node, i); r.setEnd(node, i + t.length);
    const top = r.getBoundingClientRect().top - pre.getBoundingClientRect().top;
    pre.scrollBy({ top: top - 8, behavior: 'smooth' });
    pre.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [sel, text]);
}
async function waitUntil(p, ctx, sec) {
  const left = ctx.stepStart + sec * 1000 - Date.now();
  if (left > 0) await p.waitForTimeout(left);
}

/* ---------- recording ---------- */
async function record() {
  const browser = await chromium.launch();
  const ctx0 = await browser.newContext({ viewport: VIEW, deviceScaleFactor: SCALE });
  if (MAPLIBRE_DIR) {
    await ctx0.route(/unpkg\.com\/maplibre-gl@4\.7\.1\/dist\//, (r) => r.fulfill({
      path: path.join(MAPLIBRE_DIR, path.basename(new URL(r.request().url()).pathname)) }));
  }
  if (NO_TILES) await ctx0.route(/tile\.openstreetmap\.org/, (r) => r.abort());
  await ctx0.addInitScript(CURSOR_JS);
  const page = await ctx0.newPage();
  page.on('pageerror', (e) => console.warn('page error:', e.message));
  await page.goto(URL_ + '?guide=1');
  await page.waitForFunction(() => typeof state !== 'undefined' && state.mapReady && state.fc
    && document.querySelector('#alerts-list article') && !/loading/i.test(document.querySelector('#kpi-lead-value').textContent)
    && /verified/.test(document.querySelector('#audit-badge').textContent), null, { timeout: 120000, polling: 500 });
  // Count a different photo first (panel hidden), so picking the Kumbh photo later is a real change.
  // Done before the first step, so it is cut from the video.
  await page.waitForSelector('#cam-result .kv-cam', { state: 'attached', timeout: 60000 });
  await page.click('#tab-camera');
  await page.selectOption('#sample-select', 'rath_yatra_puri_2007.jpg');
  await page.waitForSelector('#cam-result .kv-cam', { timeout: 60000 });
  await page.click('#tab-alerts');
  await page.mouse.move(640, 360);
  await page.waitForTimeout(1500);

  const frames = [], frameDir = path.join(WORK, 'frames');
  fs.mkdirSync(frameDir, { recursive: true });
  const cdp = await ctx0.newCDPSession(page);
  cdp.on('Page.screencastFrame', ({ data, metadata, sessionId }) => {
    const f = path.join(frameDir, `f${String(frames.length).padStart(6, '0')}.jpg`);
    fs.writeFileSync(f, Buffer.from(data, 'base64'));
    frames.push({ t: metadata.timestamp, f });   // seconds since epoch
    cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {});
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: W, maxHeight: H });
  await page.waitForTimeout(1000);

  const ctx = {}, log = [];
  for (const s of STEPS) {
    ctx.stepStart = Date.now();
    await s.run(page, ctx);
    const used = (Date.now() - ctx.stepStart) / 1000;
    if (used > s.seconds) console.warn(`step ${s.id} overran: ${used.toFixed(1)} s > ${s.seconds} s`);
    await waitUntil(page, ctx, s.seconds);
    log.push({ id: s.id, start: ctx.stepStart / 1000, end: Date.now() / 1000 });
    console.log(`step ${s.id}: ${(log.at(-1).end - log.at(-1).start).toFixed(1)} s (ran ${used.toFixed(1)} s)`);
  }
  await cdp.send('Page.stopScreencast');
  await browser.close();
  console.log(`frames: ${frames.length}, first ${frames[0] && (frames[0].t - log[0].start).toFixed(2)} s from step 1`);
  console.log('checks:', JSON.stringify({ oldTrackClick: ctx.oldTrackClick, trunkClick: ctx.trunkClick,
    alertId: ctx.alertId, blockedAfterFirstApproval: ctx.blocked, alertState: ctx.alertState, camCount: ctx.camCount }));
  return { frames, log, ctx };
}

async function renderCards() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: VIEW, deviceScaleFactor: SCALE });
  const out = {};
  for (const [id, c] of Object.entries(CARDS)) {
    await page.setContent(`<!doctype html><meta charset="utf-8"><style>${CARD_CSS}</style><body>${c.html}</body>`);
    out[id] = path.join(WORK, `card_${id}.png`);
    await page.screenshot({ path: out[id] });
  }
  await browser.close();
  return out;
}

/* ---------- captions and assembly ---------- */
const pad2 = (n) => String(n).padStart(2, '0');
function assTime(s) { const cs = Math.round(s * 100); return `${Math.floor(cs / 360000)}:${pad2(Math.floor(cs / 6000) % 60)}:${pad2(Math.floor(cs / 100) % 60)}.${pad2(cs % 100)}`; }
function srtTime(s) { const ms = Math.round(s * 1000); return `${pad2(Math.floor(ms / 3600000))}:${pad2(Math.floor(ms / 60000) % 60)}:${pad2(Math.floor(ms / 1000) % 60)},${String(ms % 1000).padStart(3, '0')}`; }

// Captions for the console part, times relative to the start of the first step.
function consoleCues(log, ctx) {
  const base = log[0].start, cues = [];
  STEPS.forEach((s, i) => {
    const start = log[i].start - base, end = log[i].end - base;
    s.captions.forEach(([at, text], j) => {
      const next = j + 1 < s.captions.length ? start + s.captions[j + 1][0] : end;
      cues.push({ start: start + at, end: next, text: typeof text === 'function' ? text(ctx) : text });
    });
  });
  return cues;
}

function writeAss(file, cues) {
  const head = `[Script Info]\nScriptType: v4.00+\nPlayResX: ${W}\nPlayResY: ${H}\nWrapStyle: 0\n\n[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Noto Sans,33,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,90,90,14,1\n
[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n`;
  fs.writeFileSync(file, head + cues.map((c) => `Dialogue: 0,${assTime(c.start)},${assTime(c.end)},Cap,,0,0,0,,${c.text}`).join('\n') + '\n');
}

function ffmpeg(args) { execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: 'inherit' }); }
const ENC = ['-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', String(FPS),
  '-c:a', 'aac', '-b:a', '64k', '-ar', '48000', '-ac', '2', '-shortest', '-movflags', '+faststart'];
const SILENCE = ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000'];

// Screencast frames arrive only when the page changes: hold each one until the next (variable frame rate).
function writeFrameList(file, frames, start, end) {
  let i = frames.findLastIndex((f) => f.t <= start);
  if (i < 0) i = 0;
  const lines = ['ffconcat version 1.0'];
  for (; i < frames.length && frames[i].t < end; i++) {
    const from = Math.max(frames[i].t, start), to = Math.min(frames[i + 1]?.t ?? end, end);
    lines.push(`file '${frames[i].f}'`, `duration ${Math.max(to - from, 0.001).toFixed(4)}`);
  }
  lines.push(`file '${frames[i - 1].f}'`);
  fs.writeFileSync(file, lines.join('\n') + '\n');
}

function build({ frames, log, ctx }, cards) {
  const parts = [];
  const cardClip = (id) => {
    const f = path.join(WORK, `part_${id}.mp4`);
    ffmpeg(['-loop', '1', '-framerate', String(FPS), '-t', String(CARDS[id].seconds), '-i', cards[id], ...SILENCE,
      '-vf', `scale=${W}:${H},format=yuv420p`, '-t', String(CARDS[id].seconds), ...ENC, f]);
    return f;
  };
  ORDER_BEFORE.forEach((id) => parts.push(cardClip(id)));

  const cues = consoleCues(log, ctx);
  const ass = path.join(WORK, 'console.ass');
  writeAss(ass, cues);
  const start = log[0].start, dur = log.at(-1).end - start;
  const consoleMp4 = path.join(WORK, 'part_console.mp4');
  const frameList = path.join(WORK, 'frames.txt');
  writeFrameList(frameList, frames, start, log.at(-1).end);
  ffmpeg(['-f', 'concat', '-safe', '0', '-i', frameList, ...SILENCE,
    '-vf', `fps=${FPS},scale=${INNER_W}:${INNER_H}:flags=lanczos,pad=${W}:${H}:${(W - INNER_W) / 2}:0:color=${BG},`
      + `subtitles=${ass.replace(/[:\\']/g, '\\$&')}`, '-t', dur.toFixed(2), ...ENC, consoleMp4]);
  parts.push(consoleMp4);
  ORDER_AFTER.forEach((id) => parts.push(cardClip(id)));

  const list = path.join(WORK, 'parts.txt');
  fs.writeFileSync(list, parts.map((f) => `file '${f}'`).join('\n') + '\n');
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  ffmpeg(['-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', OUT]);

  // Whole-video .srt: card titles plus the console captions, shifted by the opening cards.
  const off = ORDER_BEFORE.reduce((t, id) => t + CARDS[id].seconds, 0);
  const all = [
    { start: 0, end: CARDS.intro.seconds, text: '[INTRO GAP 0:00-0:25: team intro, your face and voice]' },
    { start: CARDS.intro.seconds, end: off, text: '[Problem: three dated events, 2022-2025]' },
    ...cues.map((c) => ({ ...c, start: c.start + off, end: c.end + off })),
  ];
  let t = off + dur;
  all.push({ start: t, end: t + CARDS.roadmap.seconds, text: '[Integrate, not replace · next: one-monsoon pilot with SMVDSB and SDRF]' });
  t += CARDS.roadmap.seconds;
  all.push({ start: t, end: t + CARDS.closing.seconds, text: '[Open source · built with AI assistance · data credits]' });
  fs.writeFileSync(OUT.replace(/\.mp4$/, '.srt'), all.map((c, i) =>
    `${i + 1}\n${srtTime(c.start)} --> ${srtTime(c.end)}\n${c.text}\n`).join('\n'));
  return { cues: all, consoleStart: off, consoleDur: dur };
}

async function main() {
  fs.rmSync(WORK, { recursive: true, force: true });
  fs.mkdirSync(WORK, { recursive: true });
  const rec = await record();
  const cards = await renderCards();
  const info = build(rec, cards);
  const probe = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration,size:stream=codec_type,width,height',
    '-of', 'json', OUT]).toString();
  console.log(JSON.stringify({ out: OUT, consoleStart: info.consoleStart, consoleDur: info.consoleDur,
    probe: JSON.parse(probe) }, null, 1));
}

main().catch((e) => { console.error(e); process.exit(1); });
