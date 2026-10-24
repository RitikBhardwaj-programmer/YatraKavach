// Console 2 checks and screenshots (impact, camera, KPI strip, phone). Usage:
//   python -m http.server 8765   (repo root)   then   node frontend/screenshots/shoot2.js <scratch dir>
// <scratch dir>/ml/package/dist holds the npm package maplibre-gl@4.7.1 (unpkg.com may be blocked).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const SP = process.argv[2], OUT = path.join(__dirname), ML = path.join(SP, 'ml/package/dist');
const BASE = 'http://localhost:8765/frontend/index.html?fixtures=1';
const UPLOAD = path.join(__dirname, '../../docs/api-fixtures/vision/samples/example-placeholder.png');
(async () => {
  const browser = await chromium.launch();
  const errors = [];
  async function page(viewport, extra = '') {
    const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
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
  const width = (p) => p.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);

  let p = await page({ width: 1366, height: 768 }, '&segment=VD-OLD-01');
  await p.screenshot({ path: `${OUT}/8-header-kpi-1366.png` });
  console.log('KPI lead:', (await p.textContent('#kpi-lead')).replace(/\s+/g, ' ').trim());
  console.log('KPI lead title:', await p.getAttribute('#kpi-lead', 'title'));
  console.log('KPI alerts:', await p.textContent('#kpi-alerts'), '| audit:', await p.textContent('#audit-badge'));
  console.log('1366 scrollWidth/innerWidth:', await width(p));

  await p.locator('#impact-panel').scrollIntoViewIfNeeded();
  await p.locator('#impact-panel').screenshot({ path: `${OUT}/9-impact-panel-gfs.png` });
  console.log('impact GFS:', (await p.textContent('#impact-body')).replace(/\s+/g, ' ').trim());
  await p.selectOption('#impact-source', 'ecmwf_ifs025');
  await p.waitForTimeout(400);
  await p.locator('#impact-panel').screenshot({ path: `${OUT}/10-impact-panel-ecmwf.png` });
  console.log('impact ECMWF order:', await p.$$eval('#impact-body .bar-label strong', (els) => els.map((e) => e.textContent)));

  await p.locator('#camera-panel').scrollIntoViewIfNeeded();
  await p.waitForTimeout(300);
  await p.locator('#camera-panel').screenshot({ path: `${OUT}/11-camera-panel-replay.png` });
  console.log('camera (replay) apply button present:', await p.locator('#cam-apply').count());
  await p.screenshot({ path: `${OUT}/12-side-camera-1366.png` });

  // upload an image, then LIVE mode with the apply button
  await p.setInputFiles('#cam-upload', UPLOAD);
  await p.waitForTimeout(600);
  console.log('after upload sample select:', JSON.stringify(await p.inputValue('#sample-select')),
    '| caption:', await p.textContent('.cam-fig figcaption'));
  await p.click('.mode button[data-mode="live"]');
  await p.waitForTimeout(800);
  console.log('camera (live) apply button present:', await p.locator('#cam-apply').count());
  await p.click('#cam-apply');
  await p.waitForTimeout(800);
  console.log('flash:', await p.textContent('#flash'));
  await p.locator('#camera-panel').scrollIntoViewIfNeeded();
  await p.locator('#camera-panel').screenshot({ path: `${OUT}/13-camera-panel-live.png` });

  p = await page({ width: 390, height: 844 });
  await p.screenshot({ path: `${OUT}/14-phone-top.png` });
  await p.screenshot({ path: `${OUT}/15-phone-full.png`, fullPage: true });
  console.log('390 scrollWidth/innerWidth:', await width(p));
  const wide = await p.evaluate(() => [...document.querySelectorAll('body *')]
    .filter((e) => e.getBoundingClientRect().right > window.innerWidth + 1).map((e) => e.tagName + '.' + e.className).slice(0, 10));
  console.log('390 elements past the right edge:', JSON.stringify(wide));
  console.log('SIMULATED labels:', await p.locator('text=SIMULATED').count());
  console.log('footer:', (await p.textContent('.footer')).replace(/\s+/g, ' ').trim());
  console.log('errors:', JSON.stringify(errors));
  await browser.close();
})();
