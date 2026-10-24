'use strict';
/* YatraKavach officer console. Static, no build step. Contract: docs/PLAN.md "HTTP API".
   ?fixtures=1 reads docs/api-fixtures/ (EXAMPLE data) instead of /api. */

const LEVELS = ['GREEN', 'YELLOW', 'ORANGE', 'RED'];
const LEVEL_WORD = ['normal', 'watch', 'warning', 'severe'];
const LEVEL_COLOR = ['#2e7d32', '#f2c200', '#ef6c00', '#c62828']; // display colours only
const LEVEL_WIDTH = [3, 4, 6, 8];                                  // px; second cue besides colour
const OPEN_STATES = ['PROPOSED', 'ESCALATED', 'APPROVED', 'SENT'];
const ACTIONABLE = ['PROPOSED', 'ESCALATED'];
const IST_OFFSET_MIN = 330;
const HISTORY_HOURS = 48;
const PLAY_STEP_MS = 800;
const LIVE_REFRESH_MS = 5 * 60 * 1000;
const ALERTS_REFRESH_MS = 30 * 1000;

const params = new URLSearchParams(location.search);
const FIXTURES = params.get('fixtures') === '1';
const FIXTURE_BASE = '../docs/api-fixtures/';

const state = {
  mode: params.get('mode') === 'live' ? 'live' : 'replay',
  times: [], events: [], idx: 0, playing: false,
  fc: null, selected: null, alerts: [], officers: [],
  map: null, mapReady: false, fitted: false,
  openDetails: new Set(), editing: null, loadToken: 0, historyToken: 0,
  liveTimer: null,
};

const $ = (sel, root = document) => root.querySelector(sel);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* ---------- time helpers (all display in IST) ---------- */
function toIst(ms) {
  return new Date(ms + IST_OFFSET_MIN * 60000).toISOString().slice(0, 19) + '+05:30';
}
function fmtTs(ts, withYear = true) {
  if (!ts) return '';
  const d = new Date(Date.parse(ts) + IST_OFFSET_MIN * 60000);
  const mon = d.toLocaleString('en-GB', { month: 'short', timeZone: 'UTC' });
  const hm = d.toISOString().slice(11, 16);
  return `${d.getUTCDate()} ${mon}${withYear ? ' ' + d.getUTCFullYear() : ''} ${hm} IST`;
}
function nowIst() { return toIst(Date.now()); }

/* ---------- API: real HTTP or fixtures ---------- */
function qs(obj) {
  return Object.entries(obj).filter(([, v]) => v != null && v !== '')
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
}

function httpApi() {
  async function req(method, path, body, asText) {
    const opts = { method, headers: {} };
    if (body) { opts.headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(body); }
    const r = await fetch('/api' + path, opts);
    if (!r.ok) {
      let msg = `${r.status} ${r.statusText}`;
      try { const j = await r.json(); if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail); } catch { /* not JSON */ }
      throw new Error(msg);
    }
    return asText ? r.text() : r.json();
  }
  return {
    segments: (mode, at) => req('GET', '/segments?' + qs({ mode, at })),
    timeline: () => req('GET', '/replay/timeline'),
    history: (id, mode, from, to) => req('GET', `/segments/${encodeURIComponent(id)}/history?` + qs({ mode, from, to })),
    alerts: () => req('GET', '/alerts'),
    action: (id, verb, body) => (verb === 'edit'
      ? req('PATCH', `/alerts/${encodeURIComponent(id)}`, body)
      : req('POST', `/alerts/${encodeURIComponent(id)}/${verb}`, body)),
    cap: (id) => req('GET', `/alerts/${encodeURIComponent(id)}/cap.xml`, null, true),
    audit: (id) => req('GET', '/audit?' + qs({ alert_id: id })),
    verify: () => req('GET', '/audit/verify'),
    officers: () => req('GET', '/officers'),
  };
}

/* Fixture API: reads the example files and mimics the alert state machine in memory (not saved). */
function fixtureApi() {
  const cache = new Map();
  const get = (file, asText) => {
    if (!cache.has(file)) {
      cache.set(file, fetch(FIXTURE_BASE + file).then((r) => {
        if (!r.ok) throw new Error(`fixture ${file}: ${r.status}`);
        return asText ? r.text() : r.json();
      }));
    }
    return cache.get(file);
  };
  const clone = (o) => JSON.parse(JSON.stringify(o));
  let alerts = null;
  const localAudit = [];
  const loadAlerts = async () => { if (!alerts) alerts = clone(await get('alerts.json')); return alerts; };

  async function replaySegments(at) {
    const base = await get('segments_replay.json');
    if (!at || base.features[0]?.properties.ts === at) return base;
    const rows = await Promise.all(base.features.map((f) => get(`history/${f.properties.id}.json`)));
    return {
      ...base,
      features: base.features.map((f, i) => {
        const row = rows[i].find((r) => r.ts === at);
        if (!row) return { ...f, properties: { ...f.properties, risk_level: null } };
        const d = row.drivers || {};
        return { ...f, properties: { ...f.properties, ts: row.ts, hazard_level: row.hazard_level,
          crowd_level: row.crowd_level, risk_level: row.risk_level, drivers: d,
          persons: d.persons, density_ppm2: d.density_ppm2 } };
      }),
    };
  }

  function transition(a, verb, body, officer) {
    const fail = (m) => { throw new Error(m); };
    const from = a.state;
    if (!officer) fail('Unknown officer');
    if (verb === 'approve') {
      if (!ACTIONABLE.includes(from)) fail(`Cannot approve in state ${from}`);
      if (a.approvals.some((x) => x.officer === officer.id)) fail('This officer has already approved; a second, different officer is needed');
      a.approvals.push({ officer: officer.id, ts: nowIst() });
      if (a.approvals.length >= a.needs_approvals) a.state = 'APPROVED';
    } else if (verb === 'reject') {
      if (!ACTIONABLE.includes(from)) fail(`Cannot reject in state ${from}`);
      a.state = 'REJECTED';
    } else if (verb === 'cancel') {
      if (!OPEN_STATES.includes(from)) fail(`Cannot cancel in state ${from}`);
      a.state = 'CANCELLED';
    } else if (verb === 'ack') {
      if (from !== 'SENT') fail('Only a SENT alert can be acknowledged');
      a.state = 'ACKED';
    } else if (verb === 'break-glass') {
      if (officer.role !== 'senior') fail('Break-glass needs a senior officer');
      if (!body.reason) fail('Break-glass needs a written reason');
      if (!ACTIONABLE.includes(from)) fail(`Cannot break-glass in state ${from}`);
      a.state = 'SENT';
    } else if (verb === 'edit') {
      if (!ACTIONABLE.includes(from) || a.approvals.length) fail('Edit is only allowed before any approval');
      a.proposed_action = body.proposed_action;
    }
    a.updated_at = nowIst();
    localAudit.push({ local: true, ts: a.updated_at, alert_id: a.id, actor: officer.id, from_state: from,
      to_state: a.state, reason: body.reason || (verb === 'edit' ? 'edited action' : verb), message: a.proposed_action });
  }

  return {
    segments: (mode, at) => (mode === 'live' ? get('segments_live.json') : replaySegments(at)),
    timeline: () => get('replay_timeline.json'),
    history: async (id, mode, from, to) => (await get(`history/${id}.json`))
      .filter((r) => (!from || Date.parse(r.ts) >= Date.parse(from)) && (!to || Date.parse(r.ts) <= Date.parse(to))),
    alerts: async () => clone(await loadAlerts()),
    action: async (id, verb, body) => {
      const a = (await loadAlerts()).find((x) => x.id === id);
      if (!a) throw new Error(`No alert ${id}`);
      const officers = await get('officers.json');
      transition(a, verb, body, officers.find((o) => o.id === body.officer_id));
      return clone(a);
    },
    cap: (id) => get(`cap/${id}.xml`, true),
    audit: async (id) => [...await get(`audit/${id}.json`), ...localAudit.filter((r) => r.alert_id === id)],
    verify: () => get('audit_verify.json'),
    officers: () => get('officers.json'),
  };
}

const api = FIXTURES ? fixtureApi() : httpApi();

/* ---------- small UI helpers ---------- */
function pill(level, extra = '') {
  if (level == null || !(level in LEVELS)) return '<span class="pill pill-na">n/a</span>';
  return `<span class="pill lvl-${level}">${LEVELS[level]}<span class="pill-word"> · ${LEVEL_WORD[level]}</span>${extra}</span>`;
}
const SIM = '<span class="tag tag-sim">SIMULATED</span>';
function officerName(id) {
  const o = state.officers.find((x) => x.id === id);
  return o ? o.name : id;
}
function flash(msg, isError) {
  const el = $('#flash') || Object.assign(document.body.appendChild(document.createElement('div')), { id: 'flash' });
  el.setAttribute('role', isError ? 'alert' : 'status');
  el.className = isError ? 'flash flash-err' : 'flash';
  el.textContent = msg;
  clearTimeout(flash.t);
  flash.t = setTimeout(() => { el.textContent = ''; el.className = 'flash'; }, 6000);
}

/* ---------- drivers in words ---------- */
const RULE_WORDS = {
  RED_R24: '24 h rain at or above the severe level',
  ORANGE_R24: '24 h rain at or above the warning level',
  ORANGE_R24_ANTECEDENT: '24 h rain over twice the watch level on wet ground (15-day rain)',
  YELLOW_R24: '24 h rain over the watch level',
  YELLOW_R15D: '15-day rain over the antecedent level',
  BELOW_WATCH: 'rain below the watch level',
};
function ruleWords(rule) {
  if (!rule) return '';
  const id = /^RED_ID_(\d+)H$/.exec(rule);
  if (id) return `mean rain intensity over ${id[1]} h above the intensity-duration curve`;
  return RULE_WORDS[rule] || rule;
}
const num = (v, d = 1) => Number(v).toLocaleString('en-IN', { maximumFractionDigits: d });

/* The API nests drivers as {rule, hazard: {...}, crowd: {...}}; fixtures may be flat. Flatten both. */
function flatDrivers(p) {
  const raw = p.drivers || {};
  const h = raw.hazard || {};
  const steps = h.step_up || raw.step_up || [];
  return { ...raw, ...h, rule: h.rule || raw.rule, fusion_rule: raw.hazard ? raw.rule : null,
    slope_raise: raw.slope_raise || steps.includes('STEEP_SLOPE'), past_slide: steps.includes('PAST_SLIDE'),
    scenario: raw.crowd?.scenario || null };
}

function driversText(p) {
  const d = flatDrivers(p);
  const parts = [];
  if (d.r24_mm != null) {
    let s = `24 h rain ${num(d.r24_mm)} mm`;
    if (d.r24_threshold) s += ` = ${num(d.ratio ?? d.r24_mm / d.r24_threshold)}x threshold (${num(d.r24_threshold, 2)} mm)`;
    parts.push(s);
  }
  if (d.r15d_mm != null) parts.push(`15-day rain ${num(d.r15d_mm)} mm${d.r15d_threshold ? ` (level ${num(d.r15d_threshold)} mm)` : ''}`);
  if (d.r3_mm != null) parts.push(`3 h rain ${num(d.r3_mm)} mm`);
  const slope = d.slope_deg ?? p.terrain_slope_deg;
  if (slope != null) {
    let s = `slope ${num(slope)} deg`;
    if (d.slope_raise) s += ` (steep${d.steep_slope_deg ? `, ≥ ${num(d.steep_slope_deg)} deg` : ''}: level raised one step)`;
    parts.push(s);
  }
  if (d.past_slide) parts.push('a landslide was recorded here earlier: level raised one step');
  const persons = p.persons ?? d.persons;
  const dens = p.density_ppm2 ?? d.density_ppm2;
  if (persons != null) parts.push(`${num(persons, 0)} people${dens != null ? ` (${num(dens, 2)} per m²)` : ''}`);
  const sc = d.scenario || p.crowd_scenario;
  if (sc && sc.held_persons) {
    parts.push(sc.releasing
      ? `held queue of ${num(sc.held_persons, 0)} people moving on after the hold ended (SIMULATED scenario)`
      : `ascent stopped here: ${num(sc.held_persons, 0)} pilgrims held in a queue (SIMULATED holding-area scenario)`);
  }
  return parts;
}

/* ---------- map ---------- */
function initMap() {
  if (typeof maplibregl === 'undefined') {
    const err = $('#map-error');
    err.hidden = false;
    err.textContent = 'Map library could not load (no access to unpkg.com). Use the segment list; alerts still work.';
    return;
  }
  const map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        osm: {
          type: 'raster', tileSize: 256, maxzoom: 19,
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL)',
        },
      },
      layers: [{ id: 'osm', type: 'raster', source: 'osm', paint: { 'raster-saturation': -0.4 } }],
    },
    center: [74.94, 33.01], zoom: 13, attributionControl: { compact: false },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
  map.on('load', () => {
    const colour = ['match', ['get', 'risk_level'], 0, LEVEL_COLOR[0], 1, LEVEL_COLOR[1], 2, LEVEL_COLOR[2], 3, LEVEL_COLOR[3], '#888'];
    const width = ['match', ['get', 'risk_level'], 0, LEVEL_WIDTH[0], 1, LEVEL_WIDTH[1], 2, LEVEL_WIDTH[2], 3, LEVEL_WIDTH[3], 2];
    map.addSource('segments', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'seg-selected', type: 'line', source: 'segments', filter: ['==', ['get', 'id'], ''],
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#111', 'line-width': ['+', width, 8] } });
    map.addLayer({ id: 'seg-casing', type: 'line', source: 'segments',
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#fff', 'line-width': ['+', width, 3] } });
    map.addLayer({ id: 'seg-line', type: 'line', source: 'segments',
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': colour, 'line-width': width } });
    map.addLayer({ id: 'seg-hit', type: 'line', source: 'segments',
      paint: { 'line-color': '#000', 'line-opacity': 0, 'line-width': 18 } });
    map.on('click', 'seg-hit', (e) => selectSegment(e.features[0].properties.id));
    map.on('mouseenter', 'seg-hit', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'seg-hit', () => { map.getCanvas().style.cursor = ''; });
    state.mapReady = true;
    renderMap();
  });
  state.map = map;
}

function renderMap() {
  if (!state.mapReady || !state.fc) return;
  state.map.getSource('segments').setData(state.fc);
  state.map.setFilter('seg-selected', ['==', ['get', 'id'], state.selected || '']);
  if (!state.fitted && state.fc.features.length) {
    state.fitted = true;
    state.map.fitBounds(bounds(state.fc.features), { padding: 40, duration: 0 });
  }
}

function bounds(features) {
  let w = 180, s = 90, e = -180, n = -90;
  for (const f of features) for (const [x, y] of f.geometry.coordinates) {
    w = Math.min(w, x); e = Math.max(e, x); s = Math.min(s, y); n = Math.max(n, y);
  }
  return [[w, s], [e, n]];
}

function renderLegend() {
  $('#legend-list').innerHTML = LEVELS.map((name, i) =>
    `<li><span class="swatch" style="background:${LEVEL_COLOR[i]};height:${LEVEL_WIDTH[i]}px"></span>${name} <span class="muted">(${LEVEL_WORD[i]})</span></li>`).join('');
}

/* ---------- segments ---------- */
function currentAt() { return state.mode === 'replay' ? state.times[state.idx] : null; }

async function loadSegments() {
  const token = ++state.loadToken;
  try {
    const fc = await api.segments(state.mode, currentAt());
    if (token !== state.loadToken) return;
    state.fc = fc;
    const ts = fc.features[0]?.properties.ts || currentAt();
    $('#data-time').textContent = `${state.mode === 'live' ? 'Live' : 'Replay'} data: ${ts ? fmtTs(ts) : 'time not given'}`;
    renderMap();
    renderSegmentSelect();
    if (state.selected) renderSegment();
    if (state.mode === 'replay' && !state.editing) renderAlerts();
  } catch (e) {
    if (token === state.loadToken) flash(`Could not load segments: ${e.message}`, true);
  }
}

function renderSegmentSelect() {
  const sel = $('#segment-select');
  const cur = state.selected || '';
  sel.innerHTML = '<option value="">—</option>' + state.fc.features.map((f) => {
    const p = f.properties;
    const lvl = p.risk_level in LEVELS ? LEVELS[p.risk_level] : 'n/a';
    return `<option value="${esc(p.id)}">${esc(p.id)} · ${lvl}${p.landmark ? ' · ' + esc(p.landmark) : ''}</option>`;
  }).join('');
  sel.value = cur;
}

function selectSegment(id) {
  state.selected = id || null;
  $('#segment-select').value = id || '';
  renderMap();
  renderSegment();
  if (window.matchMedia('(max-width: 900px)').matches && id) $('#segment-panel').scrollIntoView({ behavior: 'smooth' });
}

function renderSegment() {
  const body = $('#segment-body');
  const f = state.fc?.features.find((x) => x.properties.id === state.selected);
  if (!f) { body.innerHTML = 'Select a segment on the map or in the list.'; body.className = 'muted'; return; }
  const p = f.properties;
  body.className = '';
  const d = flatDrivers(p);
  const fused = p.risk_level != null && p.risk_level > Math.max(p.hazard_level ?? 0, p.crowd_level ?? 0);
  const simCrowd = p.simulated_crowd !== false;
  const why = driversText(p);
  body.innerHTML = `
    <div class="seg-head">${pill(p.risk_level)} <strong>${esc(p.id)}</strong></div>
    <div class="muted small">${esc(p.route_name)} · segment ${esc(p.seq)}${p.landmark ? ' · ' + esc(p.landmark) : ''}
      · ${num(p.length_m, 0)} m long, ${num(p.width_m)} m wide${p.elev_m != null ? ` · ${num(p.elev_m, 0)} m elevation` : ''}</div>
    <dl class="kv">
      <dt>Hazard</dt><dd>${pill(p.hazard_level)}</dd>
      <dt>Crowd</dt><dd>${pill(p.crowd_level)} ${simCrowd ? SIM : ''}</dd>
      <dt>Risk</dt><dd>${pill(p.risk_level)}${fused ? ' <span class="small">raised one step: hazard ≥ ORANGE with people on the segment</span>' : ''}</dd>
    </dl>
    <p class="why"><strong>Why:</strong> ${why.length ? why.map(esc).join('; ') : 'no drivers given'}
      ${p.persons != null || d.persons != null ? (simCrowd ? ' ' + SIM : '') : ''}</p>
    ${d.rule ? `<p class="small">Rule: ${esc(ruleWords(d.rule))} <code>${esc(d.rule)}</code>${d.held_by_hysteresis ? ' · level held (hysteresis)' : ''}${d.rain_point ? ` · rain point ${esc(d.rain_point)}` : ''}${d.source ? ` (${esc(d.source)})` : ''}</p>` : ''}
    <div class="chart" id="seg-chart" aria-live="polite"><span class="muted small">Loading history…</span></div>`;
  loadHistory(p);
}

async function loadHistory(p) {
  const token = ++state.historyToken;
  const end = p.ts || currentAt() || nowIst();
  const from = toIst(Date.parse(end) - HISTORY_HOURS * 3600000);
  try {
    const rows = await api.history(p.id, state.mode, from, end);
    if (token !== state.historyToken) return;
    $('#seg-chart').innerHTML = historyChart(rows);
  } catch (e) {
    if (token === state.historyToken) $('#seg-chart').innerHTML = `<span class="muted small">History unavailable: ${esc(e.message)}</span>`;
  }
}

function historyChart(rows) {
  if (!rows.length) return '<span class="muted small">No history for this window.</span>';
  const W = 320, H = 96, strip = 12, top = strip + 6, bottom = H - 14;
  const n = rows.length, bw = W / n;
  const rain = rows.map((r) => r.drivers?.r24_mm);
  const hasRain = rain.some((v) => v != null);
  const thr = rows.find((r) => r.drivers?.r24_threshold)?.drivers.r24_threshold;
  const max = Math.max(1, ...rain.filter((v) => v != null), thr || 0);
  const y = (v) => bottom - (v / max) * (bottom - top);
  const rects = rows.map((r, i) => `<rect x="${(i * bw).toFixed(2)}" y="0" width="${(bw + 0.3).toFixed(2)}" height="${strip}" fill="${LEVEL_COLOR[r.risk_level] || '#999'}"><title>${esc(fmtTs(r.ts, false))}: ${LEVELS[r.risk_level] || 'n/a'}</title></rect>`).join('');
  const pts = rain.map((v, i) => (v == null ? null : `${(i * bw + bw / 2).toFixed(1)},${y(v).toFixed(1)}`)).filter(Boolean).join(' ');
  const peak = rows.reduce((m, r) => Math.max(m, r.risk_level ?? 0), 0);
  const label = `Last ${n} hours: highest risk ${LEVELS[peak]}${hasRain ? `, 24 h rain up to ${num(Math.max(...rain.filter((v) => v != null)))} mm` : ''}.`;
  return `<div class="small chart-title">History, ${esc(fmtTs(rows[0].ts, false))} to ${esc(fmtTs(rows[n - 1].ts, false))}: risk level (strip) and 24 h rain (line)</div>
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}" preserveAspectRatio="none">
      ${rects}
      <line x1="0" x2="${W}" y1="${bottom}" y2="${bottom}" class="axis"/>
      ${thr ? `<line x1="0" x2="${W}" y1="${y(thr).toFixed(1)}" y2="${y(thr).toFixed(1)}" class="thr"/>` : ''}
      ${hasRain ? `<polyline points="${pts}" class="rain"/>` : ''}
      <text x="2" y="${H - 2}" class="lbl">0</text>
      ${hasRain ? `<text x="2" y="${top + 8}" class="lbl">${num(max, 0)} mm</text>` : ''}
      ${thr ? `<text x="${W - 2}" y="${(y(thr) - 2).toFixed(1)}" class="lbl" text-anchor="end">watch ${num(thr, 2)} mm</text>` : ''}
    </svg>
    <p class="sr-only">${esc(label)}</p>`;
}

/* ---------- replay ---------- */
async function loadTimeline() {
  const tl = await api.timeline();
  const start = Date.parse(tl.start), end = Date.parse(tl.end), step = (tl.step_minutes || 60) * 60000;
  state.times = [];
  for (let t = start; t <= end; t += step) state.times.push(toIst(t));
  state.events = tl.events || [];
  if (tl.source) $('#replay-source').textContent = tl.source.toUpperCase();
  const slider = $('#slider');
  slider.max = String(state.times.length - 1);
  const want = params.get('at') || state.events[state.events.length - 1]?.ts;
  state.idx = want ? nearestIdx(want) : 0;
  slider.value = String(state.idx);
  const span = end - start || 1;
  $('#event-marks').innerHTML = state.events.map((ev) => {
    const pct = ((Date.parse(ev.ts) - start) / span) * 100;
    return `<button type="button" class="event-mark" style="left:${pct.toFixed(2)}%" data-ts="${esc(ev.ts)}"
      title="${esc(ev.label)}" aria-label="Jump to event: ${esc(ev.label)}"></button>`;
  }).join('');
  $('#event-list').innerHTML = state.events.length ? 'Events: ' + state.events.map((ev) =>
    `<button type="button" class="link event-mark-text" data-ts="${esc(ev.ts)}">${esc(ev.label)}</button>`).join('') : '';
  renderReplayTime();
}

function nearestIdx(ts) {
  const t = Date.parse(ts);
  let best = 0;
  state.times.forEach((x, i) => { if (Date.parse(x) <= t) best = i; });
  return best;
}

function renderReplayTime() {
  const ts = state.times[state.idx];
  const t = Date.parse(ts);
  const near = state.events.filter((ev) => Math.abs(Date.parse(ev.ts) - t) < 3600000 && Date.parse(ev.ts) >= t);
  $('#replay-time').innerHTML = `<strong>${esc(fmtTs(ts))}</strong>${near.map((ev) => `<span class="event-now">${esc(ev.label)}</span>`).join('')}`;
}

let sliderDebounce;
function setIdx(i, immediate) {
  state.idx = Math.max(0, Math.min(state.times.length - 1, i));
  $('#slider').value = String(state.idx);
  renderReplayTime();
  clearTimeout(sliderDebounce);
  if (immediate) return loadSegments();
  sliderDebounce = setTimeout(loadSegments, 150);
  return null;
}

async function playLoop() {
  while (state.playing && state.idx < state.times.length - 1) {
    const started = Date.now();
    await setIdx(state.idx + 1, true);
    await new Promise((r) => setTimeout(r, Math.max(0, PLAY_STEP_MS - (Date.now() - started))));
  }
  setPlaying(false);
}

function setPlaying(on) {
  state.playing = on;
  const b = $('#play');
  b.textContent = on ? '❚❚ Pause' : '▶ Play';
  b.setAttribute('aria-label', on ? 'Pause replay' : 'Play replay');
  if (on) playLoop();
}

/* ---------- mode ---------- */
function setMode(mode) {
  state.mode = mode;
  setPlaying(false);
  document.querySelectorAll('.mode button').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.mode === mode)));
  $('#replay-bar').hidden = mode !== 'replay';
  document.body.dataset.mode = mode;
  clearInterval(state.liveTimer);
  if (mode === 'live' && !FIXTURES) state.liveTimer = setInterval(loadSegments, LIVE_REFRESH_MS);
  loadSegments();
  renderAlerts();
}

/* ---------- alerts ---------- */
async function loadAlerts() {
  try {
    state.alerts = await api.alerts();
    renderAlerts();
  } catch (e) {
    $('#alerts-list').innerHTML = `<p class="muted">Alerts unavailable: ${esc(e.message)}</p>`;
  }
}

async function loadVerify() {
  const b = $('#audit-badge');
  try {
    const v = await api.verify();
    if (v.ok) { b.className = 'tag tag-ok'; b.textContent = `✓ Audit chain verified (${v.rows} rows)`; }
    else {
      b.className = 'tag tag-bad';
      b.textContent = `✗ Audit chain BROKEN${v.row != null || v.id != null ? ' at row ' + (v.row ?? v.id) : ''}`;
    }
  } catch (e) {
    b.className = 'tag tag-bad'; b.textContent = 'Audit check unavailable';
    b.title = e.message;
  }
}

function currentOfficer() { return state.officers.find((o) => o.id === $('#officer').value); }

function renderAlerts() {
  const at = currentAt();
  const inMode = state.alerts.filter((a) => !a.mode || a.mode === state.mode);
  // In replay, an alert proposed after the replay time does not exist yet at that time.
  // Use the risk time that triggered the alert (trigger_ts); created_at is wall-clock time of the replay run.
  const alertTime = (a) => a.trigger_ts || a.created_at;
  const mine = inMode.filter((a) => !at || !alertTime(a) || Date.parse(alertTime(a)) <= Date.parse(at));
  const later = inMode.length - mine.length;
  const order = (a, b) => (b.level - a.level) || String(alertTime(b)).localeCompare(String(alertTime(a)));
  const open = mine.filter((a) => OPEN_STATES.includes(a.state)).sort(order);
  const closed = mine.filter((a) => !OPEN_STATES.includes(a.state)).sort(order);
  $('#alerts-list').innerHTML = open.length ? open.map(alertCard).join('')
    : `<p class="muted">No open alerts in ${state.mode.toUpperCase()} mode${at ? ' at this replay time' : ''}.</p>`;
  if (later) $('#alerts-list').insertAdjacentHTML('beforeend', `<p class="muted small">${later} alert${later > 1 ? 's' : ''} proposed after ${esc(fmtTs(at))} hidden; move the slider forward.</p>`);
  $('#closed-alerts').hidden = !closed.length;
  $('#closed-list').innerHTML = closed.map(alertCard).join('');
  document.querySelectorAll('.alert details').forEach((d) => {
    if (state.openDetails.has(d.dataset.key)) { d.open = true; loadDetail(d); }
  });
}

function alertCard(a) {
  const officer = currentOfficer();
  const actionable = ACTIONABLE.includes(a.state);
  const approvedByMe = officer && (a.approvals || []).some((x) => x.officer === officer.id);
  const isSenior = officer?.role === 'senior';
  const editing = state.editing === a.id;
  const segs = a.segment_ids || [];
  const need = a.needs_approvals ?? 1;
  const got = (a.approvals || []).length;
  const dots = Array.from({ length: Math.max(need, got) }, (_, i) => `<span class="dot ${i < got ? 'on' : ''}" aria-hidden="true"></span>`).join('');
  const approvals = (a.approvals || []).map((x) => `${esc(officerName(x.officer))} (${esc(fmtTs(x.ts, false))})`).join(', ') || 'none yet';
  const btn = (verb, label, enabled, title, cls = '') =>
    `<button type="button" class="btn ${cls}" data-verb="${verb}" data-id="${esc(a.id)}" ${enabled ? '' : 'disabled'} ${title ? `title="${esc(title)}"` : ''}>${label}</button>`;
  return `<article class="alert lvl-edge-${a.level}" data-id="${esc(a.id)}" aria-label="Alert ${esc(a.id)}, ${LEVELS[a.level]}, ${esc(a.state)}">
    <header class="alert-head">${pill(a.level)} <strong>${esc(a.id)}</strong>
      <span class="state state-${esc(a.state)}">${esc(a.state)}</span>
      ${a.example ? '<span class="tag tag-example">EXAMPLE</span>' : ''}</header>
    ${editing
      ? `<label class="small">Proposed action<textarea class="edit-text" rows="3">${esc(a.proposed_action)}</textarea></label>`
      : `<p class="action">${esc(a.proposed_action)}</p>`}
    <p class="small muted">Segments: ${segs.length > 3 ? `${esc(segs[0])} … ${esc(segs[segs.length - 1])} (${segs.length})` : segs.map(esc).join(', ')}
      <button type="button" class="link" data-verb="show" data-id="${esc(a.id)}">show on map</button>
      · proposed ${esc(fmtTs(a.created_at))}${a.updated_at && a.updated_at !== a.created_at ? ` · updated ${esc(fmtTs(a.updated_at, false))}` : ''}</p>
    <p class="approvals"><span class="dots">${dots}</span> <strong>${got} of ${need}</strong> approval${need > 1 ? 's' : ''}${need > 1 ? ' from different officers' : ''}: ${approvals}</p>
    ${actionable || a.state === 'SENT' || a.state === 'APPROVED' ? `<label class="reason small">Reason (needed for break-glass)
      <input type="text" class="reason-input" maxlength="500" placeholder="e.g. slope failure reported at segment"></label>` : ''}
    <div class="actions">
      ${editing
        ? btn('save', 'Save action', true, '', 'btn-primary') + btn('edit-cancel', 'Cancel edit', true)
        : (actionable ? btn('approve', 'Approve', !approvedByMe, approvedByMe ? 'You already approved; another officer must give the next approval' : '', 'btn-primary')
          + btn('edit', 'Edit', !got, got ? 'Edit is only allowed before any approval' : '')
          + btn('reject', 'Reject', true, '', 'btn-warn')
          + btn('break-glass', 'Break-glass', isSenior, isSenior ? 'Send now without the remaining approvals (logged, reason required)' : 'Only a senior officer can use break-glass', 'btn-danger') : '')
          + (a.state === 'SENT' ? btn('ack', 'Acknowledge', true) : '')
          + (OPEN_STATES.includes(a.state) ? btn('cancel', 'Cancel alert', true, '', 'btn-ghost') : '')}
    </div>
    ${['SENT', 'ACKED'].includes(a.state) ? `<p class="small">Delivered to: SMS · SACHET · cell broadcast ${SIM}</p>` : ''}
    <details data-kind="cap" data-id="${esc(a.id)}" data-key="${esc(a.id)}:cap"><summary>CAP 1.2 XML</summary><pre class="xml">Loading…</pre></details>
    <details data-kind="audit" data-id="${esc(a.id)}" data-key="${esc(a.id)}:audit"><summary>Audit trail</summary><div class="audit">Loading…</div></details>
  </article>`;
}

async function loadDetail(d) {
  const id = d.dataset.id;
  try {
    if (d.dataset.kind === 'cap') {
      $('pre', d).textContent = await api.cap(id);
    } else {
      const rows = await api.audit(id);
      $('.audit', d).innerHTML = rows.length ? `<table><thead><tr><th>Time</th><th>Actor</th><th>Change</th><th>Reason</th><th>Hash</th></tr></thead><tbody>
        ${rows.map((r) => `<tr><td>${esc(fmtTs(r.ts, false))}</td><td>${esc(officerName(r.actor))}</td>
          <td>${esc(r.from_state || '—')} → ${esc(r.to_state)}</td><td>${esc(r.reason || '')}</td>
          <td>${r.local ? '<span class="tag tag-example">LOCAL, not in chain</span>' : `<code title="prev ${esc(r.prev_hash)}">${esc(String(r.hash || '').slice(0, 10))}…</code>`}</td></tr>`).join('')}
        </tbody></table>` : '<p class="muted">No audit rows.</p>';
    }
  } catch (e) {
    (d.querySelector('pre, .audit')).textContent = `Unavailable: ${e.message}`;
  }
}

async function onAlertClick(ev) {
  const b = ev.target.closest('button[data-verb]');
  if (!b) return;
  const id = b.dataset.id, verb = b.dataset.verb;
  const card = b.closest('.alert');
  const a = state.alerts.find((x) => x.id === id);
  if (verb === 'show') {
    const ids = a.segment_ids || [];
    selectSegment(ids[0]);
    const fs = state.fc?.features.filter((f) => ids.includes(f.properties.id));
    if (state.mapReady && fs?.length) state.map.fitBounds(bounds(fs), { padding: 60 });
    return;
  }
  if (verb === 'edit') { state.editing = id; renderAlerts(); $('.edit-text', document.querySelector(`.alert[data-id="${CSS.escape(id)}"]`))?.focus(); return; }
  if (verb === 'edit-cancel') { state.editing = null; renderAlerts(); return; }
  const officer = currentOfficer();
  if (!officer) { flash('Pick the acting officer first.', true); return; }
  const reasonEl = $('.reason-input', card);
  const reason = reasonEl?.value.trim() || undefined;
  const body = { officer_id: officer.id };
  if (reason) body.reason = reason;
  let apiVerb = verb;
  if (verb === 'save') {
    apiVerb = 'edit';
    body.proposed_action = $('.edit-text', card).value.trim();
    if (!body.proposed_action) { flash('The action text cannot be empty.', true); return; }
  }
  if (verb === 'break-glass') {
    if (!reason) { flash('Break-glass needs a written reason.', true); reasonEl?.focus(); return; }
    if (!confirm(`Break-glass: send ${id} now as ${officer.name}, without the remaining approvals? This is logged.`)) return;
  }
  if (verb === 'reject' && !confirm(`Reject ${id} as ${officer.name}?`)) return;
  if (verb === 'cancel' && !confirm(`Cancel ${id} as ${officer.name}?`)) return;
  b.disabled = true;
  try {
    const updated = await api.action(id, apiVerb, body);
    state.alerts = state.alerts.map((x) => (x.id === id ? updated : x));
    if (verb === 'save') state.editing = null;
    renderAlerts();
    loadVerify();
    flash(`${id}: ${verb === 'save' ? 'action edited' : verb} by ${officer.name} → ${updated.state}${FIXTURES ? ' (fixtures: local only, not saved)' : ''}`);
  } catch (e) {
    b.disabled = false;
    flash(`${id}: ${e.message}`, true);
  }
}

/* ---------- boot ---------- */
async function boot() {
  if (FIXTURES) {
    $('#fixtures-tag').hidden = false;
    document.title += ' (example data)';
  }
  renderLegend();
  initMap();
  document.querySelectorAll('.mode button').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.mode)));
  $('.mode').addEventListener('keydown', (e) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
    const next = state.mode === 'live' ? 'replay' : 'live';
    setMode(next);
    $(`.mode button[data-mode="${next}"]`).focus();
  });
  $('#segment-select').addEventListener('change', (e) => selectSegment(e.target.value));
  $('#slider').addEventListener('input', (e) => { setPlaying(false); setIdx(Number(e.target.value)); });
  $('#play').addEventListener('click', () => {
    if (!state.playing && state.idx >= state.times.length - 1) setIdx(0);
    setPlaying(!state.playing);
  });
  $('#replay-bar').addEventListener('click', (e) => {
    const m = e.target.closest('.event-mark, .event-mark-text');
    if (m) { setPlaying(false); setIdx(nearestIdx(m.dataset.ts)); }
  });
  $('#officer').addEventListener('change', renderAlerts);
  document.querySelector('.side').addEventListener('click', onAlertClick);
  document.querySelector('.side').addEventListener('toggle', (e) => {
    const d = e.target;
    if (!d.matches?.('.alert details')) return;
    if (d.open) { state.openDetails.add(d.dataset.key); loadDetail(d); } else state.openDetails.delete(d.dataset.key);
  }, true);

  try {
    state.officers = await api.officers();
  } catch (e) { flash(`Officers unavailable: ${e.message}`, true); }
  $('#officer').innerHTML = state.officers.map((o) => `<option value="${esc(o.id)}">${esc(o.name)}${o.role === 'senior' ? ' · senior' : ''}</option>`).join('');
  try { await loadTimeline(); } catch (e) { flash(`Replay timeline unavailable: ${e.message}`, true); }
  setMode(state.mode);
  if (params.get('segment')) selectSegment(params.get('segment'));
  loadAlerts();
  loadVerify();
  if (!FIXTURES) {
    setInterval(() => {
      if (!state.editing && !document.activeElement?.closest('.alert')) loadAlerts();
    }, ALERTS_REFRESH_MS);
  }
}

document.addEventListener('DOMContentLoaded', boot);
