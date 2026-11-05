// HU/EN: content/i18n/<lang>.json; választás: ?lang=en vagy #en, localStorage('lang').
const dicts = {}; let cur = 'hu'; const subs = [];
export const lang = () => cur;
export const t = (k, vars) => {
  let s = (dicts[cur] && dicts[cur][k]) ?? (dicts.hu && dicts.hu[k]) ?? k;
  if (vars) for (const [a, b] of Object.entries(vars)) s = s.replace('{' + a + '}', b);
  return s;
};
export const onLang = f => subs.push(f);
export function initialLang() {
  const q = new URLSearchParams(location.search).get('lang');
  if (q === 'en' || q === 'hu') return q;
  let s = null; try { s = localStorage.getItem('lang'); } catch (e) {}
  return s === 'en' ? 'en' : 'hu';
}
async function load(l) {
  if (!dicts[l]) dicts[l] = await fetch(`content/i18n/${l}.json`).then(r => r.json());
}
export async function setLang(l, { push = true } = {}) {
  await load('hu'); await load(l); cur = l;
  document.documentElement.lang = l;
  document.querySelectorAll('[data-i18n]').forEach(e => { e.textContent = t(e.dataset.i18n); });
  document.querySelectorAll('[data-i18n-html]').forEach(e => { e.innerHTML = t(e.dataset.i18nHtml); });
  document.querySelectorAll('[data-i18n-ph]').forEach(e => { e.placeholder = t(e.dataset.i18nPh); });
  document.querySelectorAll('[data-i18n-title]').forEach(e => { e.title = t(e.dataset.i18nTitle); e.setAttribute('aria-label', t(e.dataset.i18nTitle)); });
  document.title = t('meta.title');
  const md = document.querySelector('meta[name=description]'); if (md) md.content = t('meta.desc');
  document.querySelectorAll('[data-lang]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === l)));
  try { localStorage.setItem('lang', l); } catch (e) {}
  if (push) {
    const u = new URL(location.href);
    if (l === 'hu') u.searchParams.delete('lang'); else u.searchParams.set('lang', l);
    history.replaceState(null, '', u);
  }
  subs.forEach(f => { try { f(l); } catch (e) { console.error(e); } });
}
