// Playwright – a Próbaút (probaut/) ellenőrzése: NODE_PATH=/opt/npm-tools/node_modules node tools/check_game.js
// előtte: python3 -m http.server 8765 a site/ mappában. Kimenet: _check/game_*.png, hibalista.
const { chromium, devices } = require('playwright');
const OUT = __dirname + '/../_check/';
const BASE = process.env.BASE || 'http://localhost:8765/';
(async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const errors = [], report = [];
  for (const run of [{ name: 'desktop', lang: 'hu', ctx: { viewport: { width: 1440, height: 900 } } },
                     { name: 'mobile', lang: 'en', ctx: { ...devices['iPhone 13'] } }]) {
    const ctx = await browser.newContext(run.ctx); const page = await ctx.newPage(); page.setDefaultTimeout(240000); const tag = `${run.name}_${run.lang}`;
    page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') (m.type() === 'error' ? errors : report).push(`[${tag}] console.${m.type()}: ${m.text()}`); });
    page.on('pageerror', e => errors.push(`[${tag}] pageerror: ${e.message}`));
    page.on('response', s => { if (s.status() >= 400) errors.push(`[${tag}] HTTP ${s.status()} ${s.url()}`); });
    // főoldal: a Próbaút link és CTA
    await page.goto(BASE + (run.lang === 'en' ? '?lang=en' : ''), { waitUntil: 'domcontentloaded' });
    await page.waitForSelector('#driveCta'); await page.waitForTimeout(800);
    const cta = await page.$eval('#driveCta', e => [e.getAttribute('href'), e.innerText.replace(/\s+/g, ' ').trim()]);
    const navd = await page.$eval('#nav .nav__drive', e => [e.getAttribute('href'), e.textContent]);
    report.push(`[${tag}] főoldal CTA: ${cta[0]} „${cta[1]}”; nav: ${navd[0]} „${navd[1]}”`);
    await page.locator('#driveCta').scrollIntoViewIfNeeded(); await page.evaluate(() => scrollBy(0, -200)); await page.waitForTimeout(900);
    await page.screenshot({ path: OUT + `game_cta_${tag}.png` });
    const ow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); if (ow > 1) errors.push(`[${tag}] főoldal vízszintes túllógás ${ow}px`);
    // játék
    await page.locator('#driveCta').click();
    await page.waitForURL(/probaut/);
    await page.waitForFunction(() => window.__game && document.getElementById('load').classList.contains('done'), null, { timeout: 240000 });
    await page.waitForTimeout(1500);
    const s0 = await page.evaluate(() => window.__game.state());
    report.push(`[${tag}] betöltve: y=${s0.y.toFixed(2)} h=${s0.h} kontakt=${s0.contact} fokozat=${s0.gear} rpm=${s0.rpm.toFixed(0)} draw call=${s0.calls} háromszög=${s0.tris}`);
    const title = await page.title(); report.push(`[${tag}] cím: ${title}`);
    await page.screenshot({ path: OUT + `game_${tag}_start.png` });
    const q = run.name === 'mobile' ? '' : '';
    // a szoftveres (swiftshader) WebGL lassú: a nyomva tartást SZIMULÁCIÓS időben mérjük (ms = szimulált ms)
    const simWait = async ms => { const t0 = await page.evaluate(() => window.__game.state().simT);
      await page.waitForFunction(([t0, d]) => window.__game.state().simT >= t0 + d, [t0, ms / 1000], { timeout: 180000, polling: 100 }); };
    const press = async (k, ms) => { if (run.name === 'mobile') { await page.evaluate(k => { window.__game.ctl[k] = 1; }, k); await simWait(ms); await page.evaluate(k => { window.__game.ctl[k] = 0; }, k); }
      else { const key = { gas: 'ArrowUp', brake: 'ArrowDown', left: 'ArrowLeft', right: 'ArrowRight' }[k]; await page.keyboard.down(key); await simWait(ms); await page.keyboard.up(key); } };
    // gáz 1. fokozatban
    if (run.name === 'mobile') { const b = page.locator('#touch [data-k=gas]'); const bb = await b.boundingBox(); report.push(`[${tag}] érintő GÁZ gomb: ${bb ? 'látható' : 'NINCS'}`);
      await page.touchscreen.tap(bb.x + bb.width / 2, bb.y + bb.height / 2); }
    await press('gas', 2500);
    const s1 = await page.evaluate(() => window.__game.state());
    const d1 = Math.hypot(s1.x - s0.x, s1.z - s0.z);
    report.push(`[${tag}] gáz 2,5 s (1.): elmozdulás ${d1.toFixed(1)} m, v=${(s1.v * 3.6).toFixed(0)} km/h, rpm=${s1.rpm.toFixed(0)}, fps=${s1.fps.toFixed(0)}`);
    if (d1 < 2) errors.push(`[${tag}] a gázra nem indult el (${d1.toFixed(2)} m)`);
    // váltás fel
    if (run.name === 'mobile') await page.locator('#touch [data-k=up]').tap(); else await page.keyboard.press('KeyE');
    await page.waitForTimeout(150);
    const g2 = (await page.evaluate(() => window.__game.state())).gear;
    report.push(`[${tag}] váltás fel: ${s1.gear} -> ${g2}`); if (g2 !== 2) errors.push(`[${tag}] a váltás nem működik (${g2})`);
    // gáz + kormány
    await press('gas', 600); if (run.name === 'mobile') await page.evaluate(() => { window.__game.ctl.gas = 1; }); else await page.keyboard.down('ArrowUp'); await press('right', 1500); await press('gas', 300);
    const s2 = await page.evaluate(() => window.__game.state());
    report.push(`[${tag}] 2. fokozat + jobbra: v=${(s2.v * 3.6).toFixed(0)} km/h, rpm=${s2.rpm.toFixed(0)}, h=${s2.h}`);
    await page.screenshot({ path: OUT + `game_${tag}_drive.png` });
    // kamera
    if (run.name === 'mobile') await page.locator('#touch [data-k=cam]').tap(); else await page.keyboard.press('KeyC');
    await press('gas', 700); await page.screenshot({ path: OUT + `game_${tag}_hood.png` });
    if (run.name === 'mobile') await page.locator('#touch [data-k=cam]').tap(); else await page.keyboard.press('KeyC');
    // le N-ig
    for (let i = 0; i < 3; i++) { if (run.name === 'mobile') await page.locator('#touch [data-k=down]').tap(); else await page.keyboard.press('KeyQ'); await page.waitForTimeout(80); }
    await press('gas', 600);
    const sN = await page.evaluate(() => window.__game.state()); report.push(`[${tag}] N + gáz: fokozat ${sN.gear}, rpm ${sN.rpm.toFixed(0)}`);
    if (sN.gear !== 'N') errors.push(`[${tag}] N-be váltás nem működik (${sN.gear})`);
    // reset
    if (run.name === 'mobile') await page.locator('#touch [data-k=reset]').tap(); else await page.keyboard.press('KeyR');
    await page.waitForTimeout(800);
    const ow2 = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); if (ow2 > 1) errors.push(`[${tag}] játék vízszintes túllógás ${ow2}px`);
    await ctx.close();
  }
  await browser.close();
  console.log(report.join('\n')); console.log(errors.length ? 'HIBÁK:\n' + errors.join('\n') : 'NINCS HIBA');
})();
