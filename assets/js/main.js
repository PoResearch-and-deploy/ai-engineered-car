// Belépési pont: nyelv, navigáció, előtűnés, adatvezérelt szekciók, lusta 3D-betöltés.
import { setLang, initialLang, t, lang, onLang } from './i18n.js';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const getJSON = u => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
const num = s => lang() === 'en' ? String(s).replace(/(\d),(\d)/g, '$1.$2') : s;   // „159,5” → „159.5”

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

const sizes = await getJSON('assets/fig/sizes.json').catch(() => ({}));
const img = (k, alt, cls = '') => { const [w, h] = sizes[k] || [1600, 1000]; return `<img src="assets/fig/${esc(k)}.webp" alt="${esc(alt)}" loading="lazy" decoding="async" width="${w}" height="${h}"${cls ? ` class="${cls}"` : ''}>`; };

// --- lightbox: minden [data-lb] figure ---
const lb = $('#lightbox');
const openLb = f => { const im = f.querySelector('img'); lb.querySelector('img').src = im.src; lb.querySelector('img').alt = im.alt; lb.querySelector('.lightbox__cap').textContent = f.querySelector('figcaption')?.textContent || im.alt; lb.hidden = false; lb.querySelector('button').focus(); };
document.addEventListener('click', e => { const f = e.target.closest('figure[data-lb]'); if (f) openLb(f); });
document.addEventListener('keydown', e => { const f = e.target.closest?.('figure[data-lb]'); if (f && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openLb(f); } });
lb.addEventListener('click', e => { if (e.target === lb || e.target.closest('button')) lb.hidden = true; });
addEventListener('keydown', e => { if (e.key === 'Escape') lb.hidden = true; });

// --- részegységek ---
(async () => {
  let d; try { d = await getJSON('content/subsystems.json'); } catch (e) { return; }
  const draw = () => {
    const L = lang();
    $('#subsGrid').innerHTML = d.items.map(it => {
      const x = it[L];
      const figs = it.figs.map((f, i) => `<figure data-lb tabindex="0" class="${i ? 'sub__f2' : 'sub__f1'}"><div class="imgbox">${img(f[0], L === 'hu' ? f[1] : f[2])}</div><figcaption>${esc(L === 'hu' ? f[1] : f[2])}</figcaption></figure>`).join('');
      const kpi = it.kpi.map((k, i) => `<div${i === 0 ? ' class="hot"' : ''}><b>${esc(num(k[0]))}${k[1] ? `<small>${esc(k[1])}</small>` : ''}</b><span>${esc(L === 'hu' ? k[2] : k[3])}</span></div>`).join('');
      return `<article class="sub reveal" id="sub-${esc(it.id)}"><div class="sub__figs${it.figs.length > 1 ? ' two' : ''}">${figs}</div>
        <div class="sub__body"><p class="sub__tag">${esc(it.tag)}</p><h3>${esc(x.t)}</h3><p>${esc(x.d)}</p><div class="minikpi">${kpi}</div><p class="sub__note">${esc(x.note)}</p></div></article>`;
    }).join('');
    watchReveal($('#subs'));
  };
  draw(); onLang(draw);
})();

// --- CAD-folyamat ---
(async () => {
  let d; try { d = await getJSON('content/cad.json'); } catch (e) { return; }
  const draw = () => {
    const L = lang();
    $('#cadSteps').innerHTML = d.steps.map(s => `<li class="reveal"><i>${esc(s.n)}</i><b>${esc(s[L][0])}</b><span>${esc(s[L][1])}</span></li>`).join('');
    $('#cadFigs').innerHTML = d.gallery.map(g => `<figure class="reveal" data-lb tabindex="0"><div class="imgbox">${img(g[0], L === 'hu' ? g[1] : g[2])}</div><figcaption>${esc(L === 'hu' ? g[1] : g[2])}</figcaption></figure>`).join('');
    watchReveal($('#cad'));
  };
  draw(); onLang(draw);
})();

// --- videók: munkaverziók + helyőrző a végleges filmnek ---
(() => {
  const box = $('#filmBox'), v = box.querySelector('video'), soon = box.querySelector('.film__soon'), badge = $('#vidBadge'), tabs = [...document.querySelectorAll('#vidTabs .tab')];
  const V = { previs: { src: () => 'assets/video/previs_v3.mp4', poster: 'assets/video/previs_v3.webp', d: 'film.d1' },
              s1: { src: () => `assets/video/S1_vem_${lang()}.mp4`, poster: 'assets/video/S1_vem.webp', d: 'film.d2' },
              s2: { src: () => `assets/video/S2_hajtaslanc_${lang()}.mp4`, poster: 'assets/video/S2_hajtaslanc.webp', d: 'film.d3' },
              final: { d: 'film.d4' } };
  let cur = 'previs';
  const show = (k, force) => {
    if (k === cur && !force) return; cur = k; const c = V[k];
    tabs.forEach(b => b.setAttribute('aria-selected', String(b.dataset.v === k)));
    v.pause();
    if (c.src) { v.hidden = false; soon.hidden = true; badge.hidden = false; v.poster = c.poster; v.src = c.src(); v.controls = true; }
    else { v.removeAttribute('src'); v.load(); v.hidden = true; soon.hidden = false; badge.hidden = true; }
    $('#vidDesc').textContent = t(c.d);
  };
  tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.v)));
  show('previs', true);
  onLang(() => { const was = !v.paused; show(cur, true); if (was) v.play().catch(() => {}); });
})();

// --- könyvtár ---
(async () => {
  let d; try { d = await getJSON('assets/lib/library.json'); } catch (e) { return; }
  let grp = '', all = false; const LIMIT = 12;
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
  const q = $('#bomQ'), chips = $('#bomChips'); let grp = '';
  const draw = () => {
    const L = lang(), gi = L === 'hu' ? 0 : 1;
    chips.innerHTML = [['', t('bom.all')], ...d.groups.map(g => [g[0], g[gi]])].map(([v, l]) => `<button type="button" class="chip" data-g="${esc(v)}" aria-pressed="${v === grp}">${esc(l)}</button>`).join('');
    const s = q.value.trim().toLowerCase();
    const rows = d.rows.filter(r => (!grp || r.groups.includes(grp)) && (!s || [r.partno, r.name, r.where_hu, r.where_en].join(' ').toLowerCase().includes(s)));
    const qty = r => grp ? Number((r.where_hu.split(' · ').find(x => x.startsWith(grp + ' ')) || '0').split(' ').pop()) : r.qty;
    $('#bomBody').innerHTML = rows.map(r => `<tr><td>${esc(r.partno)}</td><td>${esc(r.name)}</td><td class="num">${qty(r)}</td><td>${esc(L === 'hu' ? r.where_hu : r.where_en)}</td></tr>`).join('');
    $('#bomSum').textContent = t('bom.sum', { rows: rows.length, qty: rows.reduce((a, r) => a + qty(r), 0) });
  };
  chips.addEventListener('click', e => { const b = e.target.closest('[data-g]'); if (!b) return; grp = b.dataset.g; draw(); });
  q.addEventListener('input', draw); onLang(draw); draw();
})();

// --- napló ---
(async () => {
  let d; try { d = await getJSON('content/log.json'); } catch (e) { return; }
  const draw = () => {
    const L = lang(), hu = L === 'hu';
    $('#logTools').innerHTML = d.tools.map(x => `<div class="reveal"><b>${esc(x[0])}</b><span>${esc(hu ? x[1] : x[2])}</span></div>`).join('');
    $('#logPrompts').innerHTML = d.prompts.map(p => `<figure class="prompt reveal"><blockquote>„${esc(hu ? p.hu : p.en)}”</blockquote><figcaption>${esc(hu ? p.ctx_hu : p.ctx_en)}${p.edited ? ` · <span class="prompt__ed">${esc(t('log.edited'))}</span>` : ''}</figcaption></figure>`).join('');
    $('#logIssues').innerHTML = d.issues.map((x, i) => { const [ti, pr, fx] = x[L]; return `<article class="issue reveal"><span class="issue__n">${String(i + 1).padStart(2, '0')}</span><div><h4>${esc(ti)}</h4><p><em>${esc(t('log.problem'))}:</em> ${esc(pr)}</p><p><em class="ok">${esc(t('log.fix'))}:</em> ${esc(fx)}</p></div></article>`; }).join('');
    watchReveal($('#log'));
  };
  draw(); onLang(draw);
})();

// --- 3D és VEM: lusta betöltés, amikor a szekció közel ér ---
const lazy = (el, fn) => new IntersectionObserver((es, o) => { if (es[0].isIntersecting) { o.disconnect(); fn(); } }, { rootMargin: '400px' }).observe(el);
lazy($('#truckStage'), () => import('./viewer.js').then(m => m.initViewer($('#truckStage'))).catch(e => console.error(e)));
lazy($('#femStage'), () => import('./fem.js').then(m => m.initFem($('#femStage'))).catch(e => console.error(e)));
