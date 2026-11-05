// VEM-nézegető: assets/fem/cases.json + <eset>.glb (COLOR_0 = feszültségszín, morph target 0 = elmozdulás mm-ben).
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createStage, msg } from './stage.js';
import { t, lang, onLang } from './i18n.js';

export async function initFem(el) {
  const S = createStage(el, { env: true }); const { THREE, scene } = S;
  let data;
  try { data = await fetch(el.dataset.cases).then(r => r.json()); }
  catch (e) { msg(el, t('model.error'), true); return; }
  const cases = data.cases || [];
  const tabs = document.getElementById('femTabs');
  const scale = document.getElementById('femScale'), scaleV = document.getElementById('femScaleV');
  const loader = new GLTFLoader(); const cache = {};
  let cur = null, mesh = null, idx = 0;
  const num = (x, d = 1) => x == null ? null : Number(x).toLocaleString(lang() === 'hu' ? 'hu-HU' : 'en-GB', { maximumFractionDigits: d });

  function renderSide() {
    const c = cases[idx]; if (!c) return; const L = lang();
    document.getElementById('femTitle').textContent = c.title[L] || c.title.hu;
    document.getElementById('femDesc').textContent = c.desc[L] || c.desc.hu;
    const kv = [[t('fem.load'), c.load[L] || c.load.hu], [t('fem.vmax'), num(c.vmax) + ' MPa', 'hot']];
    if (c.umax_mm != null) kv.push([t('fem.umax'), num(c.umax_mm, 2) + ' mm']);
    kv.push([t('fem.hand'), c.hand != null ? num(c.hand) + ' MPa' : t('fem.pending')]);
    kv.push([t('fem.dev'), c.deviation_pct != null ? num(c.deviation_pct) + ' %' : '–']);
    document.getElementById('femKv').innerHTML = kv.map(([k, v, cl]) => `<dt>${k}</dt><dd class="${cl || ''}">${v}</dd>`).join('');
    document.getElementById('femNote').textContent = c.note ? (c.note[L] || c.note.hu) : '';
    el.querySelector('[data-role=vmax]').textContent = num(c.vmax);
    el.querySelector('[data-role=vmin]').textContent = num(c.vmin, 2);
    el.querySelector('[data-role=demo]').hidden = !c.demo;
    tabs.innerHTML = '';
    cases.forEach((cc, i) => {
      const b = document.createElement('button'); b.className = 'tab'; b.type = 'button'; b.setAttribute('role', 'tab');
      b.setAttribute('aria-selected', String(i === idx)); b.textContent = cc.title[L] || cc.title.hu;
      b.onclick = () => select(i); tabs.appendChild(b);
    });
  }
  const applyScale = () => {
    // def_scale (cases.json, opcionális): a csúszka 1×-e ennyiszeres valós deformáció (apró VEM-elmozdulásokhoz)
    const ms = (cases[idx] && cases[idx].def_scale) || 1;
    const k = +scale.value; scaleV.textContent = (Math.round(k * ms * 10) / 10).toLocaleString(lang() === 'hu' ? 'hu-HU' : 'en-GB') + '×';
    scale.style.setProperty('--p', (k / +scale.max * 100) + '%');
    if (mesh && mesh.morphTargetInfluences) mesh.morphTargetInfluences[0] = k * ms;
  };
  async function select(i) {
    idx = i; renderSide();
    const c = cases[i];
    el.classList.remove('ready'); msg(el, t('model.loading'));
    try {
      if (!cache[c.id]) cache[c.id] = await loader.loadAsync(c.file);
    } catch (e) { console.warn(c.file, e); msg(el, t('model.error'), true); return; }
    if (cur) scene.remove(cur);
    cur = cache[c.id].scene; scene.add(cur);
    mesh = null;
    cur.traverse(o => { if (o.isMesh) {
      mesh = o;
      if (!o.userData._m) o.material = o.userData._m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.55, metalness: 0, flatShading: !o.geometry.attributes.normal, side: THREE.DoubleSide });
    } });
    // keret a deformálatlan alakhoz; kamera kissé felülről, oldalról
    if (mesh) mesh.morphTargetInfluences && (mesh.morphTargetInfluences[0] = 0);
    S.frame(cur, { dir: [0.35, 0.35, 1], pad: 1.05 });
    applyScale(); msg(el, null);
  }
  scale.addEventListener('input', applyScale);
  onLang(() => { renderSide(); applyScale(); });
  await select(0);
}
