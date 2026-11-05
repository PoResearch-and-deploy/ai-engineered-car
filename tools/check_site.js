// Playwright – a teljes oldal ellenőrzése (2026-11-05): NODE_PATH=/opt/npm-tools/node_modules node tools/check_site.js
// előtte: python3 -m http.server 8765 a site/ mappában. Kimenet: _check/site_*.png (+ QA-képek QA_DIR-be), hibalista.
const { chromium, devices } = require('playwright');
const OUT = __dirname + '/../_check/', QA = process.env.QA_DIR || null;
const BASE = process.env.BASE || 'http://localhost:8765/';
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'] });
  const errors = [], report = [];
  for (const run of [{ name: 'desktop', lang: 'hu', ctx: { viewport: { width: 1440, height: 900 } } },
                     { name: 'mobile', lang: 'en', ctx: { ...devices['iPhone 13'] } }]) {
    const ctx = await browser.newContext(run.ctx); const page = await ctx.newPage(); page.setDefaultTimeout(240000); const tag = `${run.name}_${run.lang}`;
    page.on('console', m => { if (m.type() === 'error') errors.push(`[${tag}] console: ${m.text()}`); });
    page.on('pageerror', e => errors.push(`[${tag}] pageerror: ${e.message}`));
    page.on('requestfailed', q => { const f = q.failure()?.errorText || ''; if (!/ERR_ABORTED/.test(f)) errors.push(`[${tag}] requestfailed: ${q.url()} ${f}`); });
    page.on('response', s => { if (s.status() >= 400) errors.push(`[${tag}] HTTP ${s.status()} ${s.url()}`); });
    await page.goto(BASE + (run.lang === 'en' ? '?lang=en' : ''), { waitUntil: 'networkidle' });
    const shot = async (sel, f, qa) => { const el = page.locator(sel); await el.scrollIntoViewIfNeeded(); await page.waitForTimeout(900);
      const dir = qa ? QA : OUT; if (!dir) return; await page.screenshot({ path: dir + '/' + f }); };
    // végiggörgetés: minden lusta kép és előtűnés
    const H = await page.evaluate(() => document.body.scrollHeight);
    for (let y = 0; y < H; y += 500) { await page.evaluate(y => scrollTo(0, y), y); await page.waitForTimeout(120); }
    await page.waitForTimeout(1500);
    const imgs = await page.$$eval('img[src]', is => is.map(i => [i.currentSrc || i.src, i.complete, i.naturalWidth]));
    const bad = imgs.filter(i => !i[1] || !i[2]); report.push(`[${tag}] képek: ${imgs.length}, hibás: ${bad.length}`);
    bad.forEach(b => errors.push(`[${tag}] kép nem tölt: ${b[0]}`));
    // szekciók tartalma
    for (const [sel, min] of [['#subsGrid .sub', 8], ['#cadFigs figure', 9], ['#cadSteps li', 4], ['#bomBody tr', 70], ['#logIssues .issue', 10], ['#logPrompts .prompt', 6], ['#libGrid .part', 6]]) {
      const n = await page.$$eval(sel, e => e.length); report.push(`[${tag}] ${sel}: ${n}`); if (n < min) errors.push(`[${tag}] ${sel}: csak ${n} (min ${min})`); }
    // BOM szűrés
    await page.fill('#bomQ', '6589'); const b1 = await page.$$eval('#bomBody tr', e => e.length); await page.fill('#bomQ', '');
    await page.locator('#bomChips .chip').nth(1).click(); const b2 = await page.textContent('#bomSum'); await page.locator('#bomChips .chip').nth(0).click();
    report.push(`[${tag}] BOM keresés 6589: ${b1} sor; szűrő (1. csoport): ${b2}; összes: ${await page.textContent('#bomSum')}`);
    // videók: mindegyik fül betölti a metaadatot
    for (const v of ['previs', 's1', 's2', 'final']) {
      await page.locator(`#vidTabs [data-v=${v}]`).click(); await page.waitForTimeout(200);
      if (v === 'final') { report.push(`[${tag}] videó final: helyőrző ${await page.isVisible('#filmBox .film__soon')}`); continue; }
      const ok = await page.$eval('#filmBox video', vd => new Promise(r => { vd.preload = 'metadata'; if (vd.readyState >= 1) return r([vd.duration, vd.videoWidth, vd.currentSrc]); vd.addEventListener('loadedmetadata', () => r([vd.duration, vd.videoWidth, vd.currentSrc]), { once: true }); vd.addEventListener('error', () => r(['ERR', 0, vd.currentSrc]), { once: true }); vd.load(); setTimeout(() => r(['TIMEOUT', 0, vd.currentSrc]), 20000); }));
      report.push(`[${tag}] videó ${v}: ${ok[2].split('/').pop()} ${ok[0]} s, ${ok[1]} px`); if (typeof ok[0] !== 'number') errors.push(`[${tag}] videó ${v}: ${ok[0]}`);
    }
    await page.locator('#vidTabs [data-v=previs]').click();
    // letöltések elérhetők
    for (const href of await page.$$eval('a[download]', as => [...new Set(as.map(a => a.href))])) {
      const r = await page.request.head(href); report.push(`[${tag}] letöltés ${href.split('/').pop()}: ${r.status()} ${r.headers()['content-length']} B`); if (r.status() !== 200) errors.push(`[${tag}] letöltés ${href}: ${r.status()}`); }
    // 3D + VEM
    await page.locator('#model').scrollIntoViewIfNeeded(); await page.waitForSelector('#truckStage.ready', { timeout: 200000 });
    report.push(`[${tag}] 3D: ${JSON.stringify(await page.$eval('#truckStage', e => e._viewer.state()))}`);
    await page.locator('#fem').scrollIntoViewIfNeeded(); await page.waitForSelector('#femStage.ready', { timeout: 200000 }).catch(() => errors.push(`[${tag}] VEM nem lett kész`));
    report.push(`[${tag}] VEM-fülek: ${(await page.$$eval('#femTabs button', b => b.map(x => x.textContent))).join(' | ')}`);
    // nyelvváltás
    const other = run.lang === 'hu' ? 'en' : 'hu'; await page.click(`[data-lang=${other}]`); await page.waitForTimeout(600);
    report.push(`[${tag}] nyelvváltás → ${other}: <html lang=${await page.getAttribute('html', 'lang')}>, h1 = ${(await page.textContent('h1')).trim()}, 1. kártya = ${await page.textContent('#subsGrid h3')}`);
    await page.click(`[data-lang=${run.lang}]`); await page.waitForTimeout(600);
    // vízszintes görgetés mobilon
    const ox = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); report.push(`[${tag}] vízszintes túllógás: ${ox}px`); if (ox > 1) errors.push(`[${tag}] vízszintes túllógás ${ox}px`);
    // képernyőképek
    if (run.name === 'desktop') { await page.evaluate(() => scrollTo(0, 0)); await page.waitForTimeout(800); await page.screenshot({ path: OUT + 'site_1_desktop_hu_hero.png' });
      await shot('#sub-valto', 'site_2_desktop_hu_reszegyseg.png');
      for (const s of ['#story', '#method', '#model', '#subs', '#cad', '#lib', '#film', '#fem', '#bom', '#dl', '#log', '#logIssues', '#end']) await shot(s, `qa_${tag}_${s.slice(1)}.png`, true);
    } else {
      await shot('#cad', 'site_3_mobile_en_cad.png'); await shot('#logIssues', 'site_4_mobile_en_naplo.png');
      for (const s of ['#hero', '#story', '#model', '#subs', '#film', '#bom', '#dl', '#end']) await shot(s, `qa_${tag}_${s.slice(1)}.png`, true);
    }
    await ctx.close();
  }
  await browser.close();
  console.log(report.join('\n')); console.log(errors.length ? 'HIBÁK:\n' + errors.join('\n') : 'NINCS HIBA');
})();
