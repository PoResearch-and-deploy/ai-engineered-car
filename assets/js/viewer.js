// 3D-nézegető: truck.glb (animált, meshopt-tömörített) + parts.json – klipek, sebesség, röntgen, robbantás,
// részegység-lista kiemeléssel/elrejtéssel, alkatrész-info.
// Csomópont-konvenció: G_<csoport>, P_<cikkszám>_<nn> (extras: group, partno, name, element, sub, explode [mm]).
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { createStage, msg } from './stage.js';
import { t, lang, onLang } from './i18n.js';

const EYE_ON = '<svg viewBox="0 0 24 24" class="i-on"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>';
const EYE_OFF = '<svg viewBox="0 0 24 24" class="i-off"><path d="M3 3l18 18M10.6 5.1A10.6 10.6 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.1 3.9M6.6 6.6C3.7 8.4 2 12 2 12s3.5 7 10 7c1.8 0 3.3-.5 4.6-1.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

export async function initViewer(el) {
  const S = createStage(el); const { THREE, scene } = S;
  const parts = await fetch(el.dataset.parts).then(r => r.ok ? r.json() : {}).catch(() => ({}));
  let gltf;
  try {
    const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
    gltf = await loader.loadAsync(el.dataset.src);
  } catch (e) { console.warn('truck.glb', e); msg(el, t('model.error'), true); return; }
  const root = gltf.scene; scene.add(root);
  root.updateMatrixWorld(true);

  const fr = S.frame(root, { pad: S.camera.aspect < 1.3 ? 1.15 : 0.82 });
  const disc = new THREE.Mesh(new THREE.CircleGeometry(fr.radius * 1.3, 64),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false }));
  disc.rotation.x = -Math.PI / 2; disc.position.set(fr.center.x, fr.box.min.y - fr.radius * 0.002, fr.center.z); scene.add(disc);

  // --- csomópontok, nyugalmi póz, anyagok ---
  const groups = {}; const units = []; const mats = new Map();     // anyag -> csoport
  root.traverse(o => {
    if (/^G_/.test(o.name)) groups[o.userData.group || o.name.slice(2)] = o;
    if (o.userData && o.userData.partno) units.push(o);
    if (o.isMesh) {
      let g = o; while (g && !/^G_/.test(g.name)) g = g.parent;
      const gid = g ? (g.userData.group || g.name.slice(2)) : '';
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => mats.set(m, gid));
    }
  });
  units.forEach(u => { u.userData._p = u.position.clone(); u.userData._q = u.quaternion.clone(); u.userData._s = u.scale.clone();
    const e = u.userData.explode || [0, 0, 0]; u.userData._off = new THREE.Vector3(e[0], e[1], e[2]); });
  const restore = () => units.forEach(u => { u.position.copy(u.userData._p); u.quaternion.copy(u.userData._q); u.scale.copy(u.userData._s); });

  // --- robbantás (csúszka): ugyanazok a vektorok, mint a "robbantas" klipben ---
  const ex = document.getElementById('explode');
  let exK = 0;
  const setExplode = k => {
    exK = k; ex.value = k; ex.style.setProperty('--p', (k * 100) + '%');
    units.forEach(u => u.position.copy(u.userData._p).addScaledVector(u.userData._off, k));
  };

  // --- anyag-állapot: röntgen (átlátszó burkolat) + kiemelés (a többi részegység szellemkép) + hover-fény ---
  const xr = document.getElementById('xray');
  let xray = false, hiGroup = null, hoverGroup = null;
  const glow = new THREE.Color(0xffffff);
  const applyMats = () => {
    mats.forEach((gid, m) => {
      const ghost = (hiGroup && gid !== hiGroup) || (xray && gid === 'karosszeria' && gid !== hiGroup);
      const op = ghost ? (hiGroup && gid !== hiGroup ? 0.07 : 0.13) : 1;
      if (m.opacity !== op || m.transparent !== ghost) { m.transparent = ghost; m.opacity = op; m.depthWrite = !ghost; m.needsUpdate = true; }
      if (m.emissive) {
        if (m.userData._em === undefined) m.userData._em = m.emissive.clone();
        if (gid === hoverGroup && gid !== hiGroup) { m.emissive.copy(glow); m.emissiveIntensity = 0.18; }
        else { m.emissive.copy(m.userData._em); m.emissiveIntensity = 1; }
      }
    });
  };
  const setXray = on => { xray = on; xr.setAttribute('aria-pressed', String(on)); applyMats(); };
  xr.onclick = () => setXray(!xray);

  // --- kamera: robbantáshoz hátrébb (egyszeri, finom) ---
  let dolly = null;
  const dollyOut = () => {
    const c = S.camera.position.clone().sub(S.controls.target), d = c.length(), want = fr.radius * 3.4;
    if (d >= want * 0.95) return; dolly = { from: d, to: want, dir: c.normalize(), t: 0 };
  };
  S.onFrame(dt => { if (!dolly) return; dolly.t = Math.min(1, dolly.t + dt / 0.9); const k = dolly.t * dolly.t * (3 - 2 * dolly.t);
    S.camera.position.copy(S.controls.target).addScaledVector(dolly.dir, dolly.from + (dolly.to - dolly.from) * k); if (dolly.t >= 1) dolly = null; });

  // --- részegység-lista: név = kiemelés, szem = elrejtés ---
  const chips = document.getElementById('groupChips');
  const glist = (parts.groups && parts.groups.length ? parts.groups : Object.keys(groups).map(id => ({ id, hu: id, en: id })))
    .filter(g => groups[g.id]);
  const renderChips = () => {
    chips.innerHTML = '';
    glist.forEach(g => {
      const w = document.createElement('span'); w.className = 'gchip' + (groups[g.id].visible ? '' : ' off');
      const b = document.createElement('button'); b.type = 'button'; b.className = 'chip';
      b.style.setProperty('--c', g.color || '#888');
      b.setAttribute('aria-pressed', String(hiGroup === g.id));
      b.innerHTML = `<i></i>${g[lang()] || g.hu}`;
      b.title = t('model.highlight');
      b.onclick = () => { hiGroup = hiGroup === g.id ? null : g.id; if (hiGroup && !groups[g.id].visible) groups[g.id].visible = true; renderChips(); applyMats(); };
      b.onmouseenter = () => { hoverGroup = g.id; applyMats(); };
      b.onmouseleave = () => { hoverGroup = null; applyMats(); };
      const e = document.createElement('button'); e.type = 'button'; e.className = 'eye';
      e.innerHTML = EYE_ON + EYE_OFF; e.setAttribute('aria-label', t('model.hide') + ': ' + (g[lang()] || g.hu));
      e.setAttribute('aria-pressed', String(!groups[g.id].visible));
      e.onclick = () => { groups[g.id].visible = !groups[g.id].visible; renderChips(); };
      w.append(b, e); chips.appendChild(w);
    });
  };
  renderChips(); onLang(renderChips);

  // --- alkatrész-info (kattintás, húzás nélkül) ---
  const info = el.querySelector('[data-role=info]');
  const ray = new THREE.Raycaster(); const ptr = new THREE.Vector2();
  let down = null, sel = null;
  const hiMat = new Map();
  const highlight = (obj, on) => obj && obj.traverse(m => {
    if (!m.isMesh) return;
    if (on) { hiMat.set(m, m.material); const mm = m.material.clone(); mm.emissive = new THREE.Color(0xF28C28); mm.emissiveIntensity = 0.8; m.material = mm; }
    else if (hiMat.has(m)) { m.material.dispose(); m.material = hiMat.get(m); hiMat.delete(m); }
  });
  const showInfo = o => {
    highlight(sel, false); sel = o; highlight(sel, true);
    if (!o) { info.hidden = true; return; }
    const d = o.userData; const g = glist.find(x => x.id === d.group);
    info.querySelector('[data-role=infoGroup]').textContent = g ? (g[lang()] || g.hu) : d.group;
    info.querySelector('[data-role=infoName]').textContent = d.name || d.partno;
    info.querySelector('[data-role=infoId]').textContent = d.design_id || d.partno;
    const sub = info.querySelector('[data-role=infoSub]'); if (sub) sub.textContent = d.element ? `${d.element}` : '';
    info.hidden = false;
  };
  S.canvas.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
  S.canvas.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
    const r = S.canvas.getBoundingClientRect();
    ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ptr, S.camera);
    const hit = ray.intersectObject(root, true).find(h => {
      if (h.object.material && h.object.material.transparent && h.object.material.opacity < 0.5) return false;   // röntgenben át a burkolaton
      let o = h.object; while (o) { if (!o.visible) return false; o = o.parent; } return true; });
    let o = hit && hit.object; while (o && !(o.userData && o.userData.partno)) o = o.parent;
    showInfo(o || null);
  });
  info.querySelector('[data-role=infoClose]').onclick = () => showInfo(null);

  // --- animáció: klipek, lejátszás/szünet, idővonal, sebesség ---
  const mixer = new THREE.AnimationMixer(root);
  const meta = {}; (parts.animations || []).forEach(a => { meta[a.name] = a; });
  const order = (parts.animations || []).map(a => a.name);
  const clips = gltf.animations.slice().sort((a, b) => (order.indexOf(a.name) + 99 * (order.indexOf(a.name) < 0)) - (order.indexOf(b.name) + 99 * (order.indexOf(b.name) < 0)));
  const play = document.getElementById('animPlay'), tl = document.getElementById('animTime');
  const seg = document.getElementById('animClips'), spd = document.getElementById('animSpeed');
  const desc = document.getElementById('animDesc'), gearEl = document.getElementById('animGear');
  let cur = 0, action = null, playing = false;
  const label = c => (meta[c.name] && (meta[c.name][lang()] || meta[c.name].hu)) || c.name;
  const renderSeg = () => {
    seg.innerHTML = '';
    clips.forEach((c, i) => {
      const b = document.createElement('button'); b.type = 'button'; b.textContent = label(c);
      b.setAttribute('aria-pressed', String(i === cur));
      b.onclick = () => { useClip(i); setPlaying(true); };
      seg.appendChild(b);
    });
    const m = clips[cur] && meta[clips[cur].name];
    desc.textContent = m ? (lang() === 'en' ? m.desc_en : m.desc_hu) : '';
  };
  const marks = parts.gear_marks || [];
  const gearName = g => g === 0 ? 'N' : g + '.';
  const updGear = () => {
    if (!action || clips[cur].name !== 'valtas' || !marks.length) { gearEl.hidden = true; if (rpmEl) rpmEl.hidden = true; return; }
    const tt = action.time % action.getClip().duration; let g = marks[0].gear;
    marks.forEach(m => { if (tt >= m.t) g = m.gear; });
    gearEl.hidden = false; gearEl.textContent = gearName(g);
    updRpm(tt);
  };
  // fordulatszám-kijelzők a váltás klipben (parts.valtas_rpm: kockánkénti főtengely- és kerék-fordulat, 1/min)
  const rpmEl = document.getElementById('animRpm'), rpmC = document.getElementById('rpmCrank'), rpmW = document.getElementById('rpmWheel');
  const RPM = parts.valtas_rpm || null;
  function updRpm(tt) {
    if (!rpmEl) return;
    if (!RPM || !action || clips[cur].name !== 'valtas') { rpmEl.hidden = true; return; }
    const f = Math.min(RPM.wheel_rpm.length - 1, Math.max(0, Math.round(tt * RPM.fps)));
    rpmEl.hidden = false; rpmC.textContent = Math.round(RPM.crank_rpm[f]); rpmW.textContent = Math.round(RPM.wheel_rpm[f]);
  }
  function useClip(i) {
    mixer.stopAllAction(); restore(); exK = 0; ex.value = 0; ex.style.setProperty('--p', '0%');
    cur = i; action = clips[i] ? mixer.clipAction(clips[i]) : null;
    if (clips[i] && clips[i].name === 'robbantas') dollyOut();
    if (action) { action.reset(); action.play(); action.paused = !playing; mixer.update(0); }
    tl.value = 0; tl.style.setProperty('--p', '0%');
    renderSeg(); updGear();
  }
  function setPlaying(p) {
    if (p && !action) useClip(cur);
    playing = p; if (action) action.paused = !p;
    play.classList.toggle('on', p); play.setAttribute('aria-label', t(p ? 'model.pause' : 'model.play'));
  }
  play.onclick = () => setPlaying(!playing);
  spd.onchange = () => { mixer.timeScale = +spd.value; };
  tl.addEventListener('input', () => { if (!action) useClip(cur); setPlaying(false); action.time = +tl.value * action.getClip().duration; mixer.update(0); updGear(); });
  ex.addEventListener('input', () => {             // kézi robbantás: a klip megáll, alaphelyzet + eltolás
    if (action) { setPlaying(false); mixer.stopAllAction(); restore(); action = null; }
    if (+ex.value > 0.2) dollyOut();
    setExplode(+ex.value);
  });
  el.querySelector('[data-role=reset]').onclick = () => { dolly = null; S.reset(); setPlaying(false); useClip(cur); hiGroup = null; renderChips(); setXray(false); showInfo(null); };
  onLang(() => { renderSeg(); setPlaying(playing); });
  if (!clips.length) { play.disabled = true; tl.disabled = true; seg.hidden = true; }
  useClip(0);
  S.onFrame(dt => {
    if (!action) return;
    mixer.update(playing ? dt : 0);
    if (playing) { const d = action.getClip().duration || 1; tl.value = (action.time % d) / d; tl.style.setProperty('--p', (tl.value * 100) + '%'); updGear(); }
  });
  // automatikus lejátszás (gurulás), ha a látogató nem kért csökkentett mozgást
  let reduce = false; try { reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) {}
  if (clips.length && !reduce) setPlaying(true);
  msg(el, null);
  const api = { root, stage: S, setExplode, setPlaying, useClip, setXray, clips: clips.map(c => c.name),
    state: () => ({ clip: clips[cur] && clips[cur].name, time: action ? action.time : null, playing, gear: gearEl.hidden ? null : gearEl.textContent }) };
  el._viewer = api;                     // ellenőrző szkriptekhez (tools/check_model.js)
  return api;
}
