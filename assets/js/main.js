// Belépési pont: nyelv, navigáció, előtűnés, adatvezérelt szekciók, lusta 3D-betöltés.
import { setLang, initialLang, t, lang, onLang } from './i18n.js';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const getJSON = u => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
const fmt = (x, d = 0) => x == null ? '' : Number(x).toLocaleString(lang() === 'hu' ? 'hu-HU' : 'en-GB', { maximumFractionDigits: d });

// --- nyelv ---
document.querySelectorAll('[data-lang]').forEach(b => b.addEventListener('click', () => setLang(b.dataset.lang)));
await setLang(initialLang(), { push: false });

// --- navigáció ---
const burger = $('#burger'), nav = $('#nav');
burger.addEventListener('click', () => { const o = !nav.classList.contains('open'); nav.classList.toggle('open', o); burger.setAttribute('aria-expanded', String(o)); });
nav.addEventListener('click', e => { if (e.target.closest('a')) { nav.classList.remove('open'); burger.setAttribute('aria-expanded', 'false'); } });
const navLinks = [...nav.querySelectorAll('a')];
const navObs = new IntersectionObserver(es => es.forEach(e => {
  if (e.isIntersecting) navLinks.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id));
}), { rootMargin: '-45% 0px -50% 0px' });
document.querySelectorAll('main section[id]').forEach(s => navObs.observe(s));

// --- előtűnés görgetésre ---
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const rev = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); rev.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px' });
const watchReveal = root => root.querySelectorAll('.reveal:not(.in)').forEach(el => reduce ? el.classList.add('in') : rev.observe(el));
watchReveal(document);

// --- média-jegyzék: assets/video/media.json ({"hero": bool, "film": bool}) – így nincs 404 a hiányzó fájlokra ---
const media = await getJSON('assets/video/media.json').catch(() => ({}));

// --- hero-videó, ha létezik ---
(async () => {
  const hm = $('#heroMedia'); const src = hm.dataset.video;
  if (reduce || !src || !media.hero) return;
  try {
    const v = Object.assign(document.createElement('video'), { src, muted: true, loop: true, autoplay: true, playsInline: true });
    v.setAttribute('aria-hidden', 'true'); v.poster = hm.querySelector('img').src;
    hm.querySelector('img').replaceWith(v);
  } catch (e) {}
})();

// --- film: helyőrző, ha nincs film.mp4 ---
(async () => {
  const box = $('#filmBox'); const v = box.querySelector('video');
  if (media.film) { v.src = box.dataset.src; } else { box.querySelector('.film__soon').hidden = false; v.removeAttribute('controls'); v.querySelectorAll('track').forEach(tr => tr.remove()); }
})();

// --- számítás ---
(async () => {
  let d; try { d = await getJSON('content/calc.json'); } catch (e) { return; }
  const draw = () => {
    const L = lang();
    $('#kpis').innerHTML = d.cards.map((c, i) => `<div class="kpi reveal${i === 0 ? ' kpi--hot' : ''}"><p>${esc(c[L])}</p><b class="${c.v.length > 9 ? 'long' : ''}">${esc(L === 'en' ? c.v.replace(/,/g, '.') : c.v)}<small>${esc(c.u)}</small></b><span>${esc(L === 'hu' ? c.shu : c.sen)}</span></div>`).join('');
    $('#figs').innerHTML = d.figs.map(f => `<figure class="reveal" tabindex="0" data-src="${esc(f.src)}"><div class="imgbox"><img src="${esc(f.src)}" alt="${esc(f[L])}" loading="lazy" decoding="async" width="${f.w}" height="${f.h}"></div><figcaption>${esc(f[L])}</figcaption></figure>`).join('');
    watchReveal($('#calc'));
  };
  draw(); onLang(draw);
})();

// --- lightbox ---
const lb = $('#lightbox');
const openLb = f => { lb.querySelector('img').src = f.dataset.src; lb.querySelector('img').alt = f.querySelector('img').alt; lb.querySelector('.lightbox__cap').textContent = f.querySelector('figcaption').textContent; lb.hidden = false; lb.querySelector('button').focus(); };
$('#figs').addEventListener('click', e => { const f = e.target.closest('figure'); if (f) openLb(f); });
$('#figs').addEventListener('keydown', e => { const f = e.target.closest('figure'); if (f && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openLb(f); } });
lb.addEventListener('click', e => { if (e.target === lb || e.target.closest('button')) lb.hidden = true; });
addEventListener('keydown', e => { if (e.key === 'Escape') lb.hidden = true; });

// --- könyvtár ---
(async () => {
  let d; try { d = await getJSON('assets/lib/library.json'); } catch (e) { return; }
  $('#nLib').textContent = d.items.length;
  let grp = '', all = false; const LIMIT = 24;
  const more = Object.assign(document.createElement('button'), { type: 'button', className: 'btn btn--more' });
  $('#libGrid').after(more); more.onclick = () => { all = !all; draw(); };
  const q = $('#libQ'), chips = $('#libChips');
  const draw = () => {
    const L = lang(), key = L === 'hu' ? 'group' : 'group_en';
    const gs = [...new Set(d.items.map(i => i[key]))];
    chips.innerHTML = [['', t('lib.all')], ...gs.map(g => [g, g])].map(([v, l]) => `<button type="button" class="chip" data-g="${esc(v)}" aria-pressed="${v === grp}">${esc(l)}</button>`).join('');
    const s = q.value.trim().toLowerCase();
    const list = d.items.filter(i => (!grp || i[key] === grp) && (!s || (i.partno + ' ' + i.name).toLowerCase().includes(s)));
    const shown = all || s || grp ? list : list.slice(0, LIMIT);
    more.hidden = shown.length === list.length && !all; more.textContent = all ? t('lib.less') : t('lib.more', { n: list.length });
    $('#libGrid').innerHTML = shown.map(i => `<article class="part"><div class="thumb">${i.thumb ? `<img src="${esc(i.thumb)}" alt="" loading="lazy" decoding="async" width="300" height="300">` : ''}</div><div><b>${esc(i.partno)}</b><p>${esc(i.name)}</p></div></article>`).join('');
    $('#libCount').textContent = t('lib.count', { n: list.length });
  };
  chips.addEventListener('click', e => { const b = e.target.closest('[data-g]'); if (!b) return; grp = b.dataset.g; draw(); });
  q.addEventListener('input', draw);
  onLang(() => { grp = ''; draw(); }); draw();
})();

// --- BOM ---
(async () => {
  let d; try { d = await getJSON('content/bom.json'); } catch (e) { return; }
  const q = $('#bomQ');
  const draw = () => {
    const s = q.value.trim().toLowerCase();
    const rows = d.rows.filter(r => !s || [r.group, r.name, r.partno, r.color, r.note].join(' ').toLowerCase().includes(s));
    $('#bomBody').innerHTML = rows.map(r => `<tr><td>${esc(r.pos)}</td><td>${esc(r.group)}</td><td>${esc(r.name)}</td><td>${esc(r.partno)}</td><td class="num">${esc(r.qty)}</td><td class="num">${fmt(r.mass_g, 1)}</td><td>${esc(r.color)}</td></tr>`).join('');
    $('#bomSum').textContent = t('bom.sum', { rows: rows.length, qty: rows.reduce((a, r) => a + (r.qty || 0), 0), mass: fmt(rows.reduce((a, r) => a + (r.mass_g || 0), 0)) });
  };
  q.addEventListener('input', draw); onLang(draw); draw();
})();

// --- napló ---
(async () => {
  let d; try { d = await getJSON('content/naplo.hu.json'); } catch (e) { return; }
  $('#logTools').innerHTML = d.tools.map(x => `<div><b>${x.tool}</b><span>${x.use}</span></div>`).join('');
  $('#logTimeline').innerHTML = d.days.map(day => `<div class="day"><div class="day__d reveal"><b>${esc(day.date.slice(5).replace('-', '. '))}.</b><span>${esc(day.weekday)} · ${day.title}</span></div><div>${
    day.entries.map(en => `<div class="entry entry--${en.who.split('+')[0]} reveal"><h3>${en.title}</h3><ul>${en.items.map(i => `<li class="k-${i.kind}">${i.html}</li>`).join('')}</ul></div>`).join('')}</div></div>`).join('');
  watchReveal($('#log'));
  const en = () => { const p = $('#logEn'); p.hidden = lang() !== 'en'; p.textContent = d.en_summary + ' ' + t('log.hu_only'); };
  en(); onLang(en);
})();

// --- 3D és VEM: lusta betöltés, amikor a szekció közel ér ---
const lazy = (el, fn) => new IntersectionObserver((es, o) => { if (es[0].isIntersecting) { o.disconnect(); fn(); } }, { rootMargin: '400px' }).observe(el);
lazy($('#truckStage'), () => import('./viewer.js').then(m => m.initViewer($('#truckStage'))).catch(e => console.error(e)));
lazy($('#femStage'), () => import('./fem.js').then(m => m.initFem($('#femStage'))).catch(e => console.error(e)));
