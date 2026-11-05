// 3D-nézegető: truck.glb + parts.json – robbantott nézet, részegység-kapcsolók, alkatrész-info, animáció-lejátszó.
// Csomópont-konvenció: lásd README.md (G_<csoport>, P_<cikkszám>_<nn>, W_FL/FR/RL/RR, extras.group/partno/name).
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createStage, msg } from './stage.js';
import { t, lang, onLang } from './i18n.js';

export async function initViewer(el) {
  const S = createStage(el); const { THREE, scene } = S;
  const parts = await fetch(el.dataset.parts).then(r => r.ok ? r.json() : { groups: [], parts: {} }).catch(() => ({ groups: [], parts: {} }));
  let gltf;
  try { gltf = await new GLTFLoader().loadAsync(el.dataset.src); }
  catch (e) { console.warn('truck.glb', e); msg(el, t('model.error'), true); return; }
  const root = gltf.scene; scene.add(root);
  root.updateMatrixWorld(true);

  // talaj-árnyék helyett finom korong
  const fr = S.frame(root, { pad: S.camera.aspect < 1.3 ? 1.15 : 0.82 });
  const disc = new THREE.Mesh(new THREE.CircleGeometry(fr.radius * 1.3, 64),
    new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35 }));
  disc.rotation.x = -Math.PI / 2; disc.position.set(fr.center.x, fr.box.min.y - fr.radius * 0.002, fr.center.z); scene.add(disc);

  // --- csoportok és robbantható egységek ---
  const groups = {}; const units = [];
  root.traverse(o => {
    const name = o.name || '';
    if (/^G_/.test(name)) groups[o.userData.group || name.slice(2)] = o;
    const isWheel = /^W_/.test(name);
    const isPart = o.userData && o.userData.partno && !o.parent?.name?.startsWith('W_');
    if (isWheel || isPart) units.push(o);
  });
  const C = fr.center; const v = new THREE.Vector3();
  const gCenter = {};
  for (const [id, g] of Object.entries(groups)) gCenter[id] = new THREE.Box3().setFromObject(g).getCenter(new THREE.Vector3());
  units.forEach(u => {
    const c = new THREE.Box3().setFromObject(u).getCenter(new THREE.Vector3());
    let g = u; while (g && !/^G_/.test(g.name)) g = g.parent;
    const gc = g ? gCenter[g.userData.group || g.name.slice(2)] : C;
    const off = gc.clone().sub(C).multiplyScalar(1.1).add(c.clone().sub(gc).multiplyScalar(0.9));
    off.y = Math.max(off.y, 0) * 1.3 + (c.y - C.y) * 0.4;
    u.userData._base = u.position.clone();
    u.userData._baseW = u.getWorldPosition(new THREE.Vector3());
    u.userData._off = off;
  });
  const ex = document.getElementById('explode');
  const setExplode = k => {
    ex.style.setProperty('--p', (k * 100) + '%');
    units.forEach(u => {
      if (!k) { u.position.copy(u.userData._base); return; }
      v.copy(u.userData._baseW).addScaledVector(u.userData._off, k * 1.4);
      u.position.copy(u.parent.worldToLocal(v));
    });
  };
  ex.addEventListener('input', () => setExplode(+ex.value));

  // --- részegység-chipek ---
  const chips = document.getElementById('groupChips');
  const glist = (parts.groups && parts.groups.length ? parts.groups : Object.keys(groups).map(id => ({ id, hu: id, en: id })))
    .filter(g => groups[g.id]);
  const renderChips = () => {
    chips.innerHTML = '';
    glist.forEach(g => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'chip';
      b.style.setProperty('--c', g.color || '#888');
      b.setAttribute('aria-pressed', String(groups[g.id].visible));
      b.innerHTML = `<i></i>${g[lang()] || g.hu}`;
      b.onclick = () => { groups[g.id].visible = !groups[g.id].visible; b.setAttribute('aria-pressed', String(groups[g.id].visible)); };
      chips.appendChild(b);
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
    if (on) { hiMat.set(m, m.material); const mm = m.material.clone(); mm.emissive = new THREE.Color(0xF28C28); mm.emissiveIntensity = 0.55; m.material = mm; }
    else if (hiMat.has(m)) { m.material.dispose(); m.material = hiMat.get(m); hiMat.delete(m); }
  });
  const showInfo = o => {
    highlight(sel, false); sel = o; highlight(sel, true);
    if (!o) { info.hidden = true; return; }
    const d = o.userData; const g = glist.find(x => x.id === d.group);
    info.querySelector('[data-role=infoGroup]').textContent = g ? (g[lang()] || g.hu) : d.group;
    info.querySelector('[data-role=infoName]').textContent = d.name || d.partno;
    info.querySelector('[data-role=infoId]').textContent = d.design_id || d.partno;
    info.hidden = false;
  };
  S.canvas.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
  S.canvas.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 5) return;
    const r = S.canvas.getBoundingClientRect();
    ptr.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ptr, S.camera);
    const hit = ray.intersectObject(root, true).find(h => { let o = h.object; while (o) { if (!o.visible) return false; o = o.parent; } return true; });
    let o = hit && hit.object; while (o && !(o.userData && o.userData.partno)) o = o.parent;
    showInfo(o || null);
  });
  info.querySelector('[data-role=infoClose]').onclick = () => showInfo(null);
  el.querySelector('[data-role=reset]').onclick = () => { S.reset(); ex.value = 0; setExplode(0); showInfo(null); };

  // --- animáció ---
  const mixer = new THREE.AnimationMixer(root);
  let clips = gltf.animations.slice();
  if (!clips.length) { // demó: kerekek forgatása a W_* pivotok helyi Z tengelye körül
    const tracks = [];
    root.traverse(o => { if (/^W_/.test(o.name)) {
      const q = [], tt = [];
      for (let i = 0; i <= 24; i++) { const a = -i / 24 * Math.PI * 2; tt.push(i / 12); const qq = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), a); q.push(qq.x, qq.y, qq.z, qq.w); }
      tracks.push(new THREE.QuaternionKeyframeTrack(o.name + '.quaternion', tt, q));
    } });
    if (tracks.length) clips = [new THREE.AnimationClip('demo_wheels', -1, tracks)];
  }
  const play = document.getElementById('animPlay'), tl = document.getElementById('animTime'), sc = document.getElementById('animClip');
  sc.innerHTML = clips.map((c, i) => `<option value="${i}">${c.name || 'clip ' + (i + 1)}</option>`).join('');
  sc.hidden = clips.length < 2;
  let action = null, playing = false;
  const useClip = i => { mixer.stopAllAction(); action = clips[i] ? mixer.clipAction(clips[i]).play() : null; if (action) action.paused = !playing; };
  useClip(0);
  sc.onchange = () => useClip(+sc.value);
  const setPlaying = p => { playing = p; if (action) action.paused = !p; play.classList.toggle('on', p); play.setAttribute('aria-label', t(p ? 'model.pause' : 'model.play')); };
  play.onclick = () => setPlaying(!playing);
  tl.addEventListener('input', () => { if (!action) return; setPlaying(false); action.time = +tl.value * action.getClip().duration; mixer.update(0); });
  if (!clips.length) { play.disabled = true; tl.disabled = true; }
  S.onFrame(dt => {
    if (!action) return;
    mixer.update(playing ? dt : 0);
    if (playing) { const d = action.getClip().duration || 1; tl.value = (action.time % d) / d; tl.style.setProperty('--p', (tl.value * 100) + '%'); }
  });
  msg(el, null);
  return { root, setExplode, setPlaying };
}
