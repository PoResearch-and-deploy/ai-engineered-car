// Playwright – a mozgó 3D-modell ellenőrzése: NODE_PATH=/opt/npm-tools/node_modules node tools/check_model.js
// (előtte: python3 -m http.server 8765 a site/ mappában). Kimenet: _check/model_*.png + hibalista.
const { chromium, devices } = require('playwright');
const OUT = __dirname + '/../_check/';
const BASE = process.env.BASE || 'http://localhost:8765/';
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const errors = []; const report = [];
  for (const run of [{ name: 'desktop', lang: 'hu', ctx: { viewport: { width: 1440, height: 900 } } },
                     { name: 'mobile', lang: 'en', ctx: { ...devices['iPhone 13'], deviceScaleFactor: 2 } }]) {
    const ctx = await browser.newContext(run.ctx); const page = await ctx.newPage(); page.setDefaultTimeout(240000); const tag = `${run.name}_${run.lang}`;
    page.on('console', m => { if (m.type() === 'error') errors.push(`[${tag}] console: ${m.text()}`); });
    page.on('pageerror', e => errors.push(`[${tag}] pageerror: ${e.message}`));
    page.on('requestfailed', q => errors.push(`[${tag}] requestfailed: ${q.url()} ${q.failure()?.errorText}`));
    page.on('response', s => { if (s.status() >= 400) errors.push(`[${tag}] HTTP ${s.status()} ${s.url()}`); });
    const t0 = Date.now();
    await page.goto(BASE + (run.lang === 'en' ? '?lang=en' : ''), { waitUntil: 'networkidle' });
    await page.locator('#model').scrollIntoViewIfNeeded();
    await page.waitForSelector('#truckStage.ready', { timeout: 90000 });
    report.push(`[${tag}] betöltve ${((Date.now() - t0) / 1000).toFixed(1)} s`);
    const clips = await page.$$eval('#animClips button', bs => bs.map(b => b.textContent));
    report.push(`[${tag}] klipek: ${clips.join(' | ')}`);
    const shotStage = async f => { await page.locator('#truckStage').scrollIntoViewIfNeeded(); await page.waitForTimeout(300); const bb = await page.locator(run.name === 'desktop' ? '#truckStage' : '#model').boundingBox();
      const vp = page.viewportSize(); const y = Math.max(0, bb.y); await page.screenshot({ path: OUT + f, clip: { x: bb.x, y, width: bb.width, height: Math.min(bb.height, vp.height - y) } }); };
    for (let i = 0; i < clips.length; i++) {
      await page.locator('#animClips button').nth(i).click();
      const st0 = await page.$eval('#truckStage', e => e._viewer.state()); let st1 = st0;
      for (let k = 0; k < 40 && st1.time === st0.time; k++) { await page.waitForTimeout(500); st1 = await page.$eval('#truckStage', e => e._viewer.state()); }
      const a = st0.time, b = st1.time;
      report.push(`[${tag}] ${clips[i]} (${st1.clip}): idő ${a.toFixed(3)} -> ${b.toFixed(3)} s ${b !== a ? 'MEGY' : 'ÁLL!'}`);
      if (st1.clip === 'valtas') {
        const g = [];
        for (const v of [0.05, 0.3, 0.55, 0.8, 0.97]) { await page.$eval('#animTime', (e, v) => { e.value = v; e.dispatchEvent(new Event('input')); }, v); g.push(v + ':' + await page.$eval('#animGear', e => e.textContent)); }
        report.push(`[${tag}] váltás-kijelző (idővonal:fokozat) ${g.join(' ')}`); await page.click('#animPlay');
      }
      if (b === a) errors.push(`[${tag}] a(z) ${clips[i]} klip nem halad`);
      if (run.name === 'desktop' && i === 0) await shotStage('model_1_gurulas.png');
      if (run.name === 'desktop' && i === 3) {
        await page.click('#xray'); await page.$eval('#animTime', e => { e.value = 0.3; e.dispatchEvent(new Event('input')); }); await page.waitForTimeout(800);
        await shotStage('model_2_valtas_rontgen.png'); await page.click('#xray');
      }
      if (run.name === 'desktop' && i === 4) {
        await page.locator('#groupChips .gchip .chip').nth(4).click();       // hajtáslánc kiemelése
        await page.waitForTimeout(3000); await page.click('#animPlay'); await page.waitForTimeout(200);
        await page.$eval('#animTime', e => { e.value = 0.42; e.dispatchEvent(new Event('input')); });
        await page.waitForTimeout(400);
        await shotStage('model_3_robbantas_kiemeles.png');
      }
    }
    // elrejtés + sebesség + kattintás info
    await page.locator('#groupChips .gchip .eye').last().click();
    await page.selectOption('#animSpeed', '0.25');
    if (run.name === 'desktop') await page.locator('#groupChips .gchip .chip').nth(4).click();   // kiemelés ki
    await page.locator('#animClips button').nth(0).click(); await page.click('#animPlay'); await page.waitForTimeout(1500);   // összerakott állapot, szünet
    await page.locator('#truckStage').scrollIntoViewIfNeeded(); await page.waitForTimeout(800);
    const st = await page.locator('#truckStage canvas').boundingBox();
    for (const [fx, fy] of [[0.5, 0.55], [0.45, 0.5], [0.55, 0.62], [0.4, 0.6], [0.6, 0.45]]) {
      await page.mouse.click(st.x + st.width * fx, st.y + st.height * fy); for (let k = 0; k < 12 && await page.$eval('[data-role=info]', e => e.hidden); k++) await page.waitForTimeout(500);
      if (!(await page.$eval('[data-role=info]', e => e.hidden))) break; }
    report.push(`[${tag}] info-kártya: ${await page.$eval('[data-role=info]', e => e.hidden ? '(nincs találat)' : e.querySelector('h3').textContent)}`);
    if (run.name === 'mobile') await shotStage('model_mobile_en.png');
    await ctx.close();
  }
  await browser.close();
  console.log(report.join('\n'));
  console.log(errors.length ? 'HIBÁK:\n' + errors.join('\n') : 'NINCS KONZOLHIBA');
})();
