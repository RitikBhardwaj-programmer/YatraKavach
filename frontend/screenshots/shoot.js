const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const SP = process.argv[2], OUT = path.join(SP, 'shots'), ML = path.join(SP, 'ml/package/dist');
const BASE = 'http://localhost:8765/frontend/index.html?fixtures=1';
(async () => {
  const browser = await chromium.launch();
  const errors = [];
  async function page(viewport, extra = '') {
    const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    // unpkg.com is blocked in this sandbox: serve the identical npm package maplibre-gl@4.7.1 locally.
    await p.route('https://unpkg.com/maplibre-gl@4.7.1/dist/**', (r) => {
      const f = path.join(ML, path.basename(new URL(r.request().url()).pathname));
      r.fulfill({ body: fs.readFileSync(f), contentType: f.endsWith('.css') ? 'text/css' : 'application/javascript' });
    });
    await p.route('https://tile.openstreetmap.org/**', (r) => r.abort());
    p.on('console', (m) => { if (m.type() === 'error' && !/tile|ERR_FAILED|Failed to load resource|Failed to fetch/.test(m.text())) errors.push(m.text()); });
    p.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
    await p.goto(BASE + extra);
    await p.waitForTimeout(2500);
    return p;
  }
  // 1. map, 1366x768, replay at 26 Aug, segment selected
  let p = await page({ width: 1366, height: 768 }, '&segment=VD-OLD-05');
  await p.screenshot({ path: `${OUT}/1-map-replay-1366.png` });
  // 2. replay: jump to 25 Aug 12:00 by slider keyboard
  await p.focus('#slider');
  for (let i = 0; i < 26; i++) await p.keyboard.press('ArrowLeft');
  await p.waitForTimeout(1200);
  await p.screenshot({ path: `${OUT}/2-replay-slider-25aug-1366.png` });
  console.log('replay time:', await p.textContent('#replay-time'));
  console.log('alerts at 25 Aug 12:00:', await p.locator('.alert').count(), await p.textContent('#alerts-list'));
  await p.click('.event-mark-text:has-text("14:40")');
  await p.waitForTimeout(1200);
  // 3. approval: second officer approves RED A-0002
  await p.selectOption('#officer', 'off-2');
  await p.click('.alert[data-id="A-0002"] button[data-verb="approve"]');
  await p.waitForTimeout(500);
  await p.click('.alert[data-id="A-0002"] details[data-kind="audit"] summary');
  await p.waitForTimeout(500);
  await p.screenshot({ path: `${OUT}/3-alert-approved-1366.png` });
  console.log('A-0002 state:', await p.textContent('.alert[data-id="A-0002"] .state'));
  // same-officer double approval should be blocked; break-glass by senior on A-0003
  await p.selectOption('#officer', 'off-1');
  console.log('off-1 approve A-0003 enabled:', await p.isEnabled('.alert[data-id="A-0003"] button[data-verb="approve"]'));
  console.log('off-1 break-glass enabled:', await p.isEnabled('.alert[data-id="A-0003"] button[data-verb="break-glass"]'));
  await p.selectOption('#officer', 'sen-1');
  p.on('dialog', (d) => d.accept());
  await p.fill('.alert[data-id="A-0003"] .reason-input', 'Slope cracks reported near Himkoti');
  await p.click('.alert[data-id="A-0003"] button[data-verb="break-glass"]');
  await p.waitForTimeout(500);
  await p.click('.alert[data-id="A-0003"] details[data-kind="cap"] summary');
  await p.waitForTimeout(500);
  await p.locator('.alert[data-id="A-0003"]').scrollIntoViewIfNeeded();
  await p.screenshot({ path: `${OUT}/4-break-glass-cap-1366.png` });
  console.log('A-0003 state:', await p.textContent('.alert[data-id="A-0003"] .state'));
  // keyboard focus visible
  await p.focus('.mode button[data-mode="live"]');
  await p.keyboard.press('Tab');
  // 5. live mode
  await p.click('.mode button[data-mode="live"]');
  await p.waitForTimeout(1000);
  await p.focus('.mode button[data-mode="live"]');
  await p.screenshot({ path: `${OUT}/5-live-focus-1366.png` });
  // 6. phone
  p = await page({ width: 390, height: 844 }, '&segment=VD-OLD-01');
  await p.screenshot({ path: `${OUT}/6-phone-top.png` });
  await p.screenshot({ path: `${OUT}/7-phone-full.png`, fullPage: true });
  const sw = await p.evaluate(() => document.documentElement.scrollWidth);
  console.log('phone scrollWidth', sw);
  console.log('errors:', JSON.stringify(errors));
  await browser.close();
})();
