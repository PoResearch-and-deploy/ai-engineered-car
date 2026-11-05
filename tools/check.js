// Playwright-ellenőrzés: node tools/check.js  (előtte: python3 -m http.server 8765 a site/ mappában)
const { chromium, devices } = require('playwright');
const OUT = __dirname + '/../_check/';
const BASE = process.env.BASE || 'http://localhost:8765/';
async function shot(f, tag) { for (let i = 0; i < 3; i++) { try { return await f(); } catch (e) { await new Promise(r => setTimeout(r, 1000)); } } console.log('screenshot hiba', tag); }
(async () => {
  const browser = await chromium.launch();
  const errors = [];
  const runs = [
    { name: 'desktop', ctx: { viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', ctx: { ...devices['iPhone 13'], deviceScaleFactor: 2 } },
  ];
  for (const r of runs) for (const lang of ['hu', 'en']) {
    const ctx = await browser.newContext(r.ctx);
    const page = await ctx.newPage();
    const tag = `${r.name}_${lang}`;
    page.on('console', m => { if (m.type() === 'error') errors.push(`[${tag}] console: ${m.text()}`); });
    page.on('pageerror', e => errors.push(`[${tag}] pageerror: ${e.message}`));
    page.on('requestfailed', q => errors.push(`[${tag}] requestfailed: ${q.url()} ${q.failure()?.errorText}`));
    page.on('response', s => { if (s.status() >= 400) errors.push(`[${tag}] HTTP ${s.status()} ${s.url()}`); });
    await page.goto(BASE + (lang === 'en' ? '?lang=en' : ''), { waitUntil: 'networkidle' });
    await page.screenshot({ path: OUT + `${tag}_hero.png` });
    // végiggörgetés (előtűnés + lusta betöltés)
    const H = await page.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < H; y += 600) { await page.evaluate(y => scrollTo(0, y), y); await page.waitForTimeout(120); }
    for (const [sel, id] of [['#truckStage', 'model'], ['#femStage', 'fem']]) {
      await page.locator(sel).scrollIntoViewIfNeeded();
      try { await page.waitForSelector(sel + '.ready', { timeout: 60000 }); }
      catch (e) { errors.push(`[${tag}] ${sel} nem lett kész`); }
      await page.waitForTimeout(800);
      await page.locator('#' + id).screenshot({ path: OUT + `${tag}_${id}.png` });
    }
    for (const id of ['ai', 'calc', 'lib', 'log']) { await page.locator('#' + id).scrollIntoViewIfNeeded(); await page.waitForTimeout(900); await shot(() => page.locator('#' + id).screenshot({ path: OUT + `${tag}_${id}.png` }), tag); }
    if (r.name === 'desktop' && lang === 'hu') {
      // robbantott nézet + alkatrész-kattintás
      await page.locator('#truckStage').scrollIntoViewIfNeeded();
      await page.$eval('#explode', e => { e.value = 0.7; e.dispatchEvent(new Event('input')); });
      await page.waitForTimeout(500);
      const b = await page.locator('#truckStage canvas').boundingBox();
      await page.mouse.click(b.x + b.width * 0.5, b.y + b.height * 0.55);
      await page.waitForTimeout(600);
      await page.locator('#model').screenshot({ path: OUT + `${tag}_model_exploded.png` });
      await page.$eval('#femScale', e => { e.value = 4; e.dispatchEvent(new Event('input')); });
      await page.waitForTimeout(500);
      await page.locator('#fem').screenshot({ path: OUT + `${tag}_fem_x4.png` });
    }
    await page.evaluate(() => scrollTo(0, 0)); await page.waitForTimeout(300);
    if (r.name === 'desktop') await shot(() => page.screenshot({ path: OUT + `${tag}_full.png`, fullPage: true }), tag);
    await ctx.close();
  }
  await browser.close();
  console.log(errors.length ? errors.join('\n') : 'NINCS HIBA');
})();
