// Próbaút – árkád vezetés a Trophy truckkal (three.js, saját egyszerű merevtest-fizika, fix lépésköz).
// Jármű: assets/truck_game.glb + truck_game.json (tools/build_game_glb.py: a build_anim_glb.py kinematikájának mintavétele).
// Lépték: a modell 1:16 – a játékvilágban 16-szorosára nagyítva (1 mm modell = 16 mm világ), az arányok változatlanok.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

// ------------------------------------------------------------------ nyelv
const TXT = {
  hu: { title: 'Próbaút', sub: 'Trophy truck · valós kinematika', back: 'Vissza', gear: 'fokozat', kmh: 'skála-km/h', real: 'valós 1:16', rpm: '1/min (főtengely)',
    keysH: 'Irányítás', kGas: 'gáz', kBrake: 'fék / tolatás', kSteer: 'kormány', kShift: 'váltás le / fel (N-1-2-3)', kHand: 'kézifék', kReset: 'visszaállítás', kCam: 'kamera',
    note: 'Fokozatonként a valós áttétel: főtengely/kerék 5,44 · 3,27 · 1,81. A rugózás, a kormányzás és a V8 dugattyúi a modell kinematikája szerint mozognak.',
    loading: 'A jármű betöltése…', tGas: 'GÁZ', tBrake: 'FÉK', camChase: 'Kamera: követő', camHood: 'Kamera: motorháztető', flip: 'Felborultál? Nyomd meg az R-t.',
    reset: 'Visszaállítva', err: 'A jármű nem töltött be. Frissítsd az oldalt.', docTitle: 'Próbaút – Trophy truck' },
  en: { title: 'Test drive', sub: 'Trophy truck · real kinematics', back: 'Back', gear: 'gear', kmh: 'scale km/h', real: 'real 1:16', rpm: 'rpm (crank)',
    keysH: 'Controls', kGas: 'throttle', kBrake: 'brake / reverse', kSteer: 'steer', kShift: 'shift down / up (N-1-2-3)', kHand: 'handbrake', kReset: 'reset', kCam: 'camera',
    note: 'Real ratios per gear: crank/wheel 5.44 · 3.27 · 1.81. Suspension, steering and the V8 pistons move by the model’s own kinematics.',
    loading: 'Loading the truck…', tGas: 'GAS', tBrake: 'BRAKE', camChase: 'Camera: chase', camHood: 'Camera: hood', flip: 'Flipped over? Press R.',
    reset: 'Reset', err: 'The truck failed to load. Please refresh.', docTitle: 'Test drive – Trophy truck' },
};
let LANG = 'hu';
{ const q = new URLSearchParams(location.search).get('lang'); let s = null; try { s = localStorage.getItem('lang'); } catch (e) {}
  LANG = q === 'en' || q === 'hu' ? q : (s === 'en' ? 'en' : 'hu'); }
const t = k => (TXT[LANG] && TXT[LANG][k]) || TXT.hu[k] || k;
function applyLang(l) {
  LANG = l; document.documentElement.lang = l; document.title = t('docTitle');
  document.querySelectorAll('[data-t]').forEach(e => { e.textContent = t(e.dataset.t); });
  document.querySelectorAll('[data-lang]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.lang === l)));
  document.getElementById('back').href = '../' + (l === 'en' ? '?lang=en' : '') + '#model';
  try { localStorage.setItem('lang', l); } catch (e) {}
  const u = new URL(location.href); if (l === 'hu') u.searchParams.delete('lang'); else u.searchParams.set('lang', l); history.replaceState(null, '', u);
}
document.querySelectorAll('[data-lang]').forEach(b => b.addEventListener('click', () => applyLang(b.dataset.lang)));
applyLang(LANG);
const fmt = (x, d = 0) => x.toLocaleString(LANG === 'hu' ? 'hu-HU' : 'en-US', { minimumFractionDigits: d, maximumFractionDigits: d });


// --- diagnosztika: hibák és WebGL-kontextusvesztés láthatóan (telefonos hibakereséshez) ---
const diagBox = (msg) => { let d = document.getElementById('diag'); if (!d) { d = document.createElement('div'); d.id = 'diag';
  d.style.cssText = 'position:fixed;left:8px;right:8px;top:56px;z-index:99;background:rgba(160,20,20,.92);color:#fff;font:12px/1.4 monospace;padding:8px 10px;border-radius:8px;white-space:pre-wrap'; document.body.appendChild(d); }
  d.textContent += (d.textContent ? '\n' : '') + msg; };
addEventListener('error', e => diagBox('Hiba: ' + (e.message || e.type) + (e.lineno ? ' @' + e.lineno : '')));
addEventListener('unhandledrejection', e => diagBox('Hiba (promise): ' + (e.reason && (e.reason.message || e.reason))));
// ------------------------------------------------------------------ renderer, jelenet
const MOBILE = matchMedia('(hover:none) and (pointer:coarse)').matches;
const QP = new URLSearchParams(location.search).get('q');
// mobilon alapból könnyített mód (nincs árnyék, 1× felbontás); ?q=high felülírja, ?q=low asztalin is kéri
const LOWQ = QP === 'low' || (QP !== 'high' && (MOBILE || (navigator.deviceMemory || 8) <= 4));
const cv = document.getElementById('cv');
const renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: !MOBILE, powerPreference: LOWQ ? 'default' : 'high-performance' });
renderer.setPixelRatio(LOWQ ? 1 : Math.min(devicePixelRatio, MOBILE ? 1.5 : 1.75));
renderer.shadowMap.enabled = !LOWQ; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
cv.addEventListener('webglcontextlost', e => { e.preventDefault(); diagBox('A grafikus kontextus elveszett (memória?). Próbáld: ?q=low'); });
const scene = new THREE.Scene();
const HORIZON = new THREE.Color(0xe9c9a0), ZENITH = new THREE.Color(0x3d7fc4);
scene.fog = new THREE.Fog(HORIZON, 140, 520);
const camera = new THREE.PerspectiveCamera(58, 1, 0.1, 1500);
function resize() { const w = innerWidth, h = innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.fov = w < h ? 72 : 58; camera.updateProjectionMatrix(); }
addEventListener('resize', resize); resize();

// ég (gradiens-gömb + nap)
const SUN_DIR = new THREE.Vector3(-0.45, 0.62, 0.35).normalize();
{
  const g = new THREE.SphereGeometry(1200, 32, 16);
  const m = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { cH: { value: HORIZON }, cZ: { value: ZENITH }, sun: { value: SUN_DIR } },
    vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
    fragmentShader: `uniform vec3 cH; uniform vec3 cZ; uniform vec3 sun; varying vec3 vD;
      void main(){ float h = clamp(vD.y, 0.0, 1.0); vec3 c = mix(cH, cZ, pow(h, 0.4));
        float s = max(dot(normalize(vD), sun), 0.0); c += vec3(1.0,0.85,0.6) * (pow(s, 900.0) * 3.0 + pow(s, 12.0) * 0.18);
        if (vD.y < 0.0) c = cH; gl_FragColor = vec4(c, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }` });
  const sky = new THREE.Mesh(g, m); sky.frustumCulled = false; sky.renderOrder = -1; scene.add(sky); scene.userData.sky = sky;
}
const hemi = new THREE.HemisphereLight(0xcfe2ff, 0xc99a63, 1.1); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6);
sun.castShadow = !LOWQ; sun.shadow.mapSize.set(MOBILE ? 1024 : 2048, MOBILE ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 120 });
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);

// ------------------------------------------------------------------ terep (analitikus magasságfüggvény = fizika és háló)
function hash(x, y) { let h = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return h - Math.floor(h); }
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
const HALF = 260;                                   // a pálya fél-mérete [m]
const RAMPS = [                                     // ugratók: középpont, irány, hossz, szélesség, magasság
  { x: 40, z: -6, a: 0.0, L: 15, W: 9, H: 2.4 },
  { x: -70, z: 55, a: 2.4, L: 18, W: 10, H: 3.2 },
  { x: 95, z: 95, a: -2.2, L: 13, W: 8, H: 1.8 },
];
for (const r of RAMPS) { r.c = Math.cos(r.a); r.s = Math.sin(r.a); }
function rampH(r, x, z) {
  const dx = x - r.x, dz = z - r.z; const u = dx * r.c + dz * r.s, v = -dx * r.s + dz * r.c;   // u: menetirány, v: oldalt
  const hw = r.W / 2; if (u < -r.L || u > 2.2 || Math.abs(v) > hw + 1.5) return 0;
  const side = Math.abs(v) <= hw ? 1 : 1 - (Math.abs(v) - hw) / 1.5;
  const f = u <= 0 ? Math.pow((u + r.L) / r.L, 1.7) : Math.max(0, 1 - u / 2.2);           // felfutó ív, a végén meredek leszálló
  return r.H * f * side * side;
}
function baseH(x, z) {
  let h = 2.4 * Math.sin(x * 0.041 + 0.8 * Math.sin(z * 0.027)) * Math.cos(z * 0.033 + 0.4)
        + 1.3 * Math.sin(z * 0.071 + x * 0.019)
        + 2.2 * (vnoise(x * 0.018, z * 0.018) - 0.5) + 0.9 * (vnoise(x * 0.05 + 7, z * 0.05) - 0.5) + 0.22 * (vnoise(x * 0.16, z * 0.16) - 0.5);
  const r0 = Math.hypot(x, z); h *= Math.min(1, Math.max(0, (r0 - 18) / 30));            // sík rajtterület
  for (const r of RAMPS) { const d = Math.hypot(x - r.x + r.c * r.L * 0.4, z - r.z + r.s * r.L * 0.4); h *= Math.min(1, Math.max(0.15, (d - r.L * 0.6) / 12)); }
  const e = Math.max(Math.abs(x), Math.abs(z)) - (HALF - 60) + 12 * (vnoise(x * 0.02 + 3, z * 0.02) - 0.5); if (e > 0) h += e * e * 0.006;   // szegély: felfutó dűnék
  return h;
}
function H(x, z) { let h = baseH(x, z); for (const r of RAMPS) h += rampH(r, x, z); return h; }
const _n = new THREE.Vector3();
function normalAt(x, z, out = _n) { const e = 0.25; return out.set(H(x - e, z) - H(x + e, z), 2 * e, H(x, z - e) - H(x, z + e)).normalize(); }

const SAND = new THREE.Color(0xd8b07a), SAND2 = new THREE.Color(0xc1925c), SAND3 = new THREE.Color(0xe8c896);
function sandTex() {
  const c = document.createElement('canvas'); c.width = c.height = 256; const x = c.getContext('2d');
  const im = x.createImageData(256, 256);
  for (let i = 0; i < 256 * 256; i++) { const px = i % 256, py = (i / 256) | 0;
    const n = 0.5 * vnoise(px * 0.09, py * 0.09) + 0.3 * vnoise(px * 0.31, py * 0.31) + 0.2 * Math.random();
    const rip = 0.5 + 0.5 * Math.sin(py * 0.28 + 2.2 * vnoise(px * 0.03, py * 0.03) * 6.0);
    const v = 205 + (n - 0.5) * 60 + (rip - 0.5) * 22; im.data[i * 4] = v; im.data[i * 4 + 1] = v * 0.97; im.data[i * 4 + 2] = v * 0.93; im.data[i * 4 + 3] = 255; }
  x.putImageData(im, 0, 0);
  const tx = new THREE.CanvasTexture(c); tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8; return tx;
}
const SANDTEX = sandTex();
{
  const N = LOWQ ? 160 : 320, S = HALF * 2;
  const g = new THREE.PlaneGeometry(S, S, N, N); g.rotateX(-Math.PI / 2);
  const p = g.attributes.position, col = new Float32Array(p.count * 3), uv = g.attributes.uv, c = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), y = baseH(x, z); p.setY(i, y);
    const n = normalAt(x, z); const k = vnoise(x * 0.03 + 50, z * 0.03);
    c.copy(SAND).lerp(SAND2, Math.min(1, (1 - n.y) * 6 + (k - 0.5) * 0.6)).lerp(SAND3, Math.max(0, (y - 1.5) * 0.12));
    col.set([c.r, c.g, c.b], i * 3); uv.setXY(i, x / 9, z / 9);
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ vertexColors: true, map: SANDTEX, roughness: 0.96, metalness: 0 });
  const ground = new THREE.Mesh(g, m); ground.receiveShadow = true; scene.add(ground);
  // ugratók: finom felbontású külön háló (a magasságfüggvényből)
  const rm = new THREE.MeshStandardMaterial({ color: 0xc89a62, map: SANDTEX, roughness: 0.95 });
  for (const r of RAMPS) {
    const nu = 48, nv = 16, gg = new THREE.PlaneGeometry(1, 1, nu, nv), pp = gg.attributes.position, uvv = gg.attributes.uv;
    for (let i = 0; i < pp.count; i++) {
      const u = -r.L - 0.5 + (uvv.getX(i)) * (r.L + 3.2), v = (uvv.getY(i) - 0.5) * (r.W + 3.4);
      const x = r.x + u * r.c - v * r.s, z = r.z + u * r.s + v * r.c;
      pp.setXYZ(i, x, H(x, z) + 0.03, z); uvv.setXY(i, x / 9, z / 9);
    }
    gg.computeVertexNormals();
    const idx = gg.index.array; for (let i = 0; i < idx.length; i += 3) { const a = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = a; }   // felfelé néző lapok
    gg.computeVertexNormals();
    const mesh = new THREE.Mesh(gg, rm); mesh.receiveShadow = true; mesh.castShadow = true; scene.add(mesh);
    // jelzőoszlopok az ugrató szélén
    for (const sv of [-1, 1]) {
      const px = r.x - r.L * r.c - sv * (r.W / 2 + 0.6) * r.s, pz = r.z - r.L * r.s + sv * (r.W / 2 + 0.6) * r.c;
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 2.4, 8), new THREE.MeshStandardMaterial({ color: 0xF28C28, roughness: 0.6 }));
      pole.position.set(px, H(px, pz) + 1.2, pz); pole.castShadow = true; scene.add(pole);
    }
  }
}

// kövek (statikus gömb-ütköző) és bóják (ellökhető)
const ROCKS = [], CONES = [];
{
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const rmat = new THREE.MeshStandardMaterial({ color: 0x8a7462, roughness: 0.95, flatShading: true });
  for (let i = 0; i < 26; i++) {
    let x, z, ok;
    do { x = (rnd() * 2 - 1) * (HALF - 60); z = (rnd() * 2 - 1) * (HALF - 60);
      ok = Math.hypot(x, z) > 35 && RAMPS.every(r => Math.hypot(x - r.x, z - r.z) > r.L + 10) && Math.abs(z) > 14; } while (!ok);
    const R = 0.8 + rnd() * 1.8;
    const g = new THREE.IcosahedronGeometry(R, 1); const p = g.attributes.position;
    for (let k = 0; k < p.count; k++) { const s = 0.75 + 0.45 * hash(p.getX(k) * 3 + i, p.getZ(k) * 3 + p.getY(k)); p.setXYZ(k, p.getX(k) * s, p.getY(k) * s * 0.7, p.getZ(k) * s); }
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, rmat); const y = H(x, z) + R * 0.25; m.position.set(x, y, z); m.rotation.y = rnd() * 6;
    m.castShadow = m.receiveShadow = true; scene.add(m); ROCKS.push({ x, y, z, R: R * 0.95 });
  }
  const cg = new THREE.ConeGeometry(0.38, 1.0, 14); cg.translate(0, 0.5, 0);
  const cm = new THREE.MeshStandardMaterial({ color: 0xff6a13, roughness: 0.55 });
  const stripe = new THREE.Mesh(new THREE.CylinderGeometry(0.205, 0.265, 0.16, 14), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5 }));
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.06, 0.8), new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.8 }));
  const place = (x, z) => {
    const o = new THREE.Group(); const c = new THREE.Mesh(cg, cm); const s = stripe.clone(); s.position.y = 0.52; const b = base.clone(); b.position.y = 0.03;
    o.add(c, s, b); o.traverse(m => { m.castShadow = true; });
    o.position.set(x, H(x, z), z); scene.add(o);
    CONES.push({ o, p: o.position, v: new THREE.Vector3(), w: new THREE.Vector3(), q: o.quaternion, hit: false, rest: true });
  };
  for (let i = 0; i < 8; i++) place(-30 - i * 14, (i % 2 ? 1 : -1) * 3.5);          // szlalom a rajttól hátra
  for (let i = 0; i < 6; i++) place(22 + i * 3, -6 + (i % 2 ? 5.6 : -5.6));         // kapu az 1. ugrató előtt
}

// ------------------------------------------------------------------ por-részecskék
const DUST_N = LOWQ ? 240 : 700;
const dust = (() => {
  const g = new THREE.BufferGeometry();
  const pos = new Float32Array(DUST_N * 3), size = new Float32Array(DUST_N), alpha = new Float32Array(DUST_N);
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('aSize', new THREE.BufferAttribute(size, 1)); g.setAttribute('aAlpha', new THREE.BufferAttribute(alpha, 1));
  const m = new THREE.ShaderMaterial({ transparent: true, depthWrite: false,
    uniforms: { uScale: { value: 400 }, uCol: { value: new THREE.Color(0xd9b88a) } },
    vertexShader: `attribute float aSize; attribute float aAlpha; uniform float uScale; varying float vA;
      void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); gl_Position = projectionMatrix * mv; gl_PointSize = aSize * uScale / max(-mv.z, 0.1); vA = aAlpha; }`,
    fragmentShader: `uniform vec3 uCol; varying float vA; void main(){ vec2 d = gl_PointCoord - 0.5; float r = dot(d,d) * 4.0; if (r > 1.0) discard;
      gl_FragColor = vec4(uCol, vA * (1.0 - r) * (1.0 - r));
      #include <colorspace_fragment>
    }` });
  const pts = new THREE.Points(g, m); pts.frustumCulled = false; scene.add(pts);
  const P = []; for (let i = 0; i < DUST_N; i++) P.push({ x: 0, y: -999, z: 0, vx: 0, vy: 0, vz: 0, age: 1, life: 1, s0: 1 });
  let head = 0;
  return {
    m, emit(x, y, z, vx, vy, vz, s) { const p = P[head]; head = (head + 1) % DUST_N; Object.assign(p, { x, y, z, vx, vy, vz, age: 0, life: 1.2 + Math.random() * 1.3, s0: s }); },
    update(dt) {
      for (let i = 0; i < DUST_N; i++) { const p = P[i];
        if (p.age >= p.life) { alpha[i] = 0; size[i] = 0; continue; }
        p.age += dt; p.vx *= 1 - 1.6 * dt; p.vz *= 1 - 1.6 * dt; p.vy = p.vy * (1 - 1.2 * dt) + 0.35 * dt;
        p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt; const k = p.age / p.life;
        pos[i * 3] = p.x; pos[i * 3 + 1] = p.y; pos[i * 3 + 2] = p.z; size[i] = p.s0 * (0.6 + 2.6 * k); alpha[i] = 0.5 * (1 - k) * Math.min(1, p.age * 8); }
      g.attributes.position.needsUpdate = g.attributes.aSize.needsUpdate = g.attributes.aAlpha.needsUpdate = true;
    },
  };
})();

// ------------------------------------------------------------------ jármű
const SC = 0.016;                                  // modell-mm -> világ-m (1:16 léptékű modell 16× nagyítva)
const loadBar = document.getElementById('loadBar');
const loader = new GLTFLoader(); loader.setMeshoptDecoder(MeshoptDecoder);
const [gltf, META] = await Promise.all([
  new Promise((res, rej) => loader.load('assets/truck_game.glb', res, e => { if (e.total) loadBar.style.width = (100 * e.loaded / e.total).toFixed(0) + '%'; }, rej)),
  fetch('assets/truck_game.json').then(r => r.json()),
]).catch(e => { console.warn(e); document.getElementById('loadErr').textContent = t('err'); document.getElementById('loadErr').hidden = false; throw e; });

const COM_MM = new THREE.Vector3(96, 38, 0);         // tömegközéppont a modell-KR-ben (mm): tengelytáv közepe, kb. kerékagy-magasság
const truck = new THREE.Group(); scene.add(truck);
const model = gltf.scene; model.scale.setScalar(SC); model.position.copy(COM_MM).multiplyScalar(-SC); truck.add(model);
model.traverse(o => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; o.frustumCulled = false; } });
// árnyék-helyettesítő: a ~430 ezer háromszöges jármű helyett egyszerű testek vetnek árnyékot (a fő menetben láthatatlanok)
const PROXY_MAT = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: false });
function proxy(geo, parent, x, y, z) { const m = new THREE.Mesh(geo, PROXY_MAT); m.position.set(x, y, z); m.castShadow = true; m.renderOrder = -2; parent.add(m); return m; }

// mintatáblák
const FAMV = {};                                     // család -> pillanatnyi állapotérték(ek)
const NODES = [];
for (const nd of META.nodes) { const o = model.getObjectByName(nd.node); if (!o) { console.warn('hiányzó csomópont', nd.node); continue; } NODES.push({ o, fam: nd.family, S: Float32Array.from(nd.samples.flat()) }); }
const WHEELS = {};
for (const [w, d] of Object.entries(META.wheels)) {
  WHEELS[w] = { o: model.getObjectByName(d.node), spin: model.getObjectByName(d.node + '_spin'), fam: d.family, S: Float32Array.from(d.samples.flat()), d };
}
const GR = META.grids;
{ const b = META.bbox; // burkolat + plató (mm, modell-KR)
  proxy(new THREE.BoxGeometry(b.max[0] - b.min[0] - 40, 50, 112), model, (b.max[0] + b.min[0]) / 2 + 6, 70, 0);
  proxy(new THREE.BoxGeometry(110, 40, 96), model, 110, 116, 0);
  for (const wh of Object.values(WHEELS)) { const c = new THREE.CylinderGeometry(34.4, 34.4, 30, 18); c.rotateX(Math.PI / 2); proxy(c, wh.spin, 0, 0, 0); } }
function locate(vals, x) {                            // -> [i, f] a rácson (széleken vágva)
  const n = vals.length; if (x <= vals[0]) return [0, 0]; if (x >= vals[n - 1]) return [n - 2, 1];
  let i = 0; while (i < n - 2 && x > vals[i + 1]) i++; return [i, (x - vals[i]) / (vals[i + 1] - vals[i])];
}
const _q = [new THREE.Quaternion(), new THREE.Quaternion(), new THREE.Quaternion(), new THREE.Quaternion()];
function blend(S, idx, wts, o) {                     // pozíció lerp + kvaternió nlerp (előjel-igazítással)
  let px = 0, py = 0, pz = 0, qx = 0, qy = 0, qz = 0, qw = 0, r = null;
  for (let k = 0; k < idx.length; k++) { const w = wts[k]; if (w === 0) continue; const b = idx[k] * 7;
    px += S[b] * w; py += S[b + 1] * w; pz += S[b + 2] * w;
    let x = S[b + 3], y = S[b + 4], z = S[b + 5], ww = S[b + 6];
    if (r === null) r = [x, y, z, ww]; else if (x * r[0] + y * r[1] + z * r[2] + ww * r[3] < 0) { x = -x; y = -y; z = -z; ww = -ww; }
    qx += x * w; qy += y * w; qz += z * w; qw += ww * w; }
  o.position.set(px, py, pz); o.quaternion.set(qx, qy, qz, qw).normalize();
}
function famWeights(fam) {
  const g = GR[fam], v = FAMV[fam];
  if (g.axes.length === 1) { const [i, f] = locate(g.values[0], v[0]); return [[i, i + 1], [1 - f, f]]; }
  const [i, f] = locate(g.values[0], v[0]), [j, e] = locate(g.values[1], v[1]), n1 = g.values[1].length;
  return [[i * n1 + j, i * n1 + j + 1, (i + 1) * n1 + j, (i + 1) * n1 + j + 1], [(1 - f) * (1 - e), (1 - f) * e, f * (1 - e), f * e]];
}
const SPIN_AX = new THREE.Vector3(0, 0, -1);        // + szög = előre gördülés
function poseTruck(st) {
  FAMV.FL = [st.hmm[0], st.s]; FAMV.FR = [st.hmm[1], st.s]; FAMV.STEER = [st.s];
  const hr = Math.max(-9, Math.min(9, (st.hmm[2] + st.hmm[3]) / 2));
  const roll = Math.max(-11, Math.min(11, Math.atan((st.hmm[2] - st.hmm[3]) / 159.6) * 180 / Math.PI));
  FAMV.REAR = [hr, roll];
  const C = ((st.crank % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI); FAMV.CRANK = [C];
  const W = {}; for (const f of Object.keys(GR)) W[f] = famWeights(f);
  for (const n of NODES) blend(n.S, W[n.fam][0], W[n.fam][1], n.o);
  for (const [w, wh] of Object.entries(WHEELS)) { blend(wh.S, W[wh.fam][0], W[wh.fam][1], wh.o); wh.spin.quaternion.setFromAxisAngle(SPIN_AX, st.spin[w]); }
}

// ------------------------------------------------------------------ fizika (merev test + 4 sugárvetés)
const G = 9.81, MASS = 2400, DT = 1 / 120;
const RATIO = { 1: 5.44, 2: 3.27, 3: 1.81 };
const GEARS = ['N', 1, 2, 3];
const IDLE = 160, REDLINE = 1200;                    // főtengely 1/min (a modell léptékében: a kerékfordulat × áttétel)
const F_DRIVE1 = MASS * 6.4;                         // 1. fokozat hajtóereje [N]; a többi az áttétellel arányos
const MU = 0.95, MU_HB = 0.38;
const com = COM_MM.clone().multiplyScalar(SC);
const RW = META.wheels.FL.radius * SC;              // kerék-sugár [m]
const TRAVEL = { FL: 16, FR: 16, RL: 16, RR: 16 };  // kerekenkénti rugóút ± [modell-mm]; a hátsó merev híd a megjelenítésben ±9 mm / ±11°-ra vágva
const W0 = MASS * G / 4;
const wheelsP = ['FL', 'FR', 'RL', 'RR'].map(w => {
  const c = META.wheels[w].center; const k = W0 / (w[0] === 'F' ? 0.30 : 0.24);
  return { w, front: w[0] === 'F', a: new THREE.Vector3(c[0], c[1], c[2]).multiplyScalar(SC).sub(com), hmax: TRAVEL[w] * SC, hmin: -TRAVEL[w] * SC,
    k, c: 2 * 0.42 * Math.sqrt(k * MASS / 4), h: 0, hprev: 0, contact: false, N: 0, omega: 0, spin: 0, slip: 0, cp: new THREE.Vector3(), yaw: 0 };
});
const I_BODY = new THREE.Vector3(2900, 9200, 7900);  // tehetetlenség [kg m²] (doboz-közelítés ×1,25), test-KR: x hossz, y függőleges, z kereszt
// ütköző pontok (test-KR, m, a tömegközépponthoz): alváz-sarkok, tető, orr/far
const HULL = []; { const b = META.bbox, mm = (x, y, z) => new THREE.Vector3(x, y, z).multiplyScalar(SC).sub(com);
  for (const x of [b.min[0] + 8, b.max[0] - 8]) for (const z of [-70, 70]) HULL.push(mm(x, 22, z));
  for (const x of [-20, 175]) for (const z of [-55, 55]) HULL.push(mm(x, b.max[1] - 4, z));
  HULL.push(mm(b.max[0], 50, 0), mm(b.min[0], 50, 0), mm(96, 130, 0)); }
const SPHERES = [-1.8, 0, 1.8].map(x => new THREE.Vector3(x, 0.25, 0));

const body = { p: new THREE.Vector3(0, 0, 0), q: new THREE.Quaternion(), v: new THREE.Vector3(), w: new THREE.Vector3() };
const ctl = { gas: 0, brake: 0, left: 0, right: 0, hand: 0 };
const st = { gear: 1, steer: 0, s: 0, rpm: IDLE, crank: 0, shiftT: 0, hmm: [0, 0, 0, 0], spin: { FL: 0, FR: 0, RL: 0, RR: 0 }, airT: 0, upsideT: 0, cam: 0, dist: 0 };
function resetCar(atStart) {
  const yaw = atStart ? 0 : Math.atan2(-fwdW.z, fwdW.x);
  const x = atStart ? 0 : body.p.x, z = atStart ? 0 : body.p.z;
  body.q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw); body.p.set(x, H(x, z) + com.y + 0.45, z);
  body.v.set(0, 0, 0); body.w.set(0, 0, 0); for (const wp of wheelsP) { wp.h = wp.hprev = 0; wp.omega = 0; }
  st.upsideT = 0;
}
const fwdW = new THREE.Vector3(1, 0, 0), upW = new THREE.Vector3(0, 1, 0), rightW = new THREE.Vector3(0, 0, 1);
const _v = new THREE.Vector3(), _v2 = new THREE.Vector3(), _r = new THREE.Vector3(), _f = new THREE.Vector3(), _s = new THREE.Vector3(), _o = new THREE.Vector3(), _dir = new THREE.Vector3();
const _qi = new THREE.Quaternion(), _wq = new THREE.Quaternion();
let Facc = new THREE.Vector3(), Tacc = new THREE.Vector3();
function addForce(F, at) { Facc.add(F); _r.subVectors(at, body.p); Tacc.add(_v2.crossVectors(_r, F)); }
function pointVel(at, out) { _r.subVectors(at, body.p); return out.crossVectors(body.w, _r).add(body.v); }
function rayGround(o, d, maxT) {                     // o + d·t és a terep metszése (menetelés + felezés)
  let tPrev = 0, fPrev = o.y - H(o.x, o.z); if (fPrev <= 0) return 0;
  const step = 0.18; for (let tt = step; tt <= maxT + 1e-6; tt += step) {
    const x = o.x + d.x * tt, y = o.y + d.y * tt, z = o.z + d.z * tt, f = y - H(x, z);
    if (f <= 0) { let a = tPrev, b = tt; for (let k = 0; k < 7; k++) { const m = (a + b) / 2; if (o.y + d.y * m - H(o.x + d.x * m, o.z + d.z * m) > 0) a = m; else b = m; } return (a + b) / 2; }
    tPrev = tt; fPrev = f; }
  return -1;
}
function yawFor(w, s) { const y = META.wheels[w].yaw_vs_s; if (!y) return 0; const [i, f] = locate(GR.STEER.values[0].length === y.length ? GR.STEER.values[0] : GR.FL.values[1], s); return (y[i] + (y[i + 1] - y[i]) * f) * Math.PI / 180; }

function step(dt) {
  fwdW.set(1, 0, 0).applyQuaternion(body.q); upW.set(0, 1, 0).applyQuaternion(body.q); rightW.set(0, 0, 1).applyQuaternion(body.q);
  Facc.set(0, -MASS * G, 0); Tacc.set(0, 0, 0);
  const vF = body.v.dot(fwdW), speed = body.v.length();
  // kormány: sebességfüggő végállás
  const target = ctl.right - ctl.left; const rate = target === 0 || Math.sign(target) !== Math.sign(st.steer) ? 4.0 : 2.4;
  st.steer += Math.max(-rate * dt, Math.min(rate * dt, target - st.steer));
  const lim = 1 - 0.62 * Math.min(1, Math.max(0, (Math.abs(vF) - 8) / 28));
  st.s = st.steer * lim * META.S_MAX;
  // hajtás
  st.shiftT = Math.max(0, st.shiftT - dt);
  const g = st.gear, ratio = RATIO[g] || 0;
  let wheelAvg = 0; for (const wp of wheelsP) wheelAvg += wp.omega; wheelAvg /= 4;
  if (g === 'N') st.rpm += ((IDLE + ctl.gas * (REDLINE - IDLE)) - st.rpm) * Math.min(1, dt * (ctl.gas ? 3 : 1.6));
  else st.rpm = Math.max(IDLE, Math.abs(wheelAvg) * ratio * 60 / (2 * Math.PI));
  const tq = st.rpm < 0.86 * REDLINE ? 1 : Math.max(0, 1 - (st.rpm - 0.86 * REDLINE) / (0.14 * REDLINE));
  let Fdrive = 0;
  if (g !== 'N' && st.shiftT === 0) Fdrive = ctl.gas * F_DRIVE1 * (ratio / RATIO[1]) * tq;
  let reverse = false;
  if (ctl.brake && !ctl.gas && vF < 0.8 && g !== 'N') { reverse = true; Fdrive = vF > -4.5 ? -0.33 * F_DRIVE1 * ctl.brake : 0; }
  let nContact = 0;
  for (const wp of wheelsP) {
    // sugárvetés a felfüggesztés tengelye mentén (test lefelé)
    _o.copy(wp.a).addScaledVector(new THREE.Vector3(0, 1, 0), wp.hmax).applyQuaternion(body.q).add(body.p);
    _dir.copy(upW).negate();
    const range = wp.hmax - wp.hmin + RW; const th = rayGround(_o, _dir, range);
    wp.hprev = wp.h;
    if (th < 0 || th > range) { wp.contact = false; wp.h = Math.max(wp.hmin, wp.h - 1.2 * dt); wp.N = 0; }
    else {
      wp.contact = true; nContact++;
      let h = wp.hmax - (th - RW); let bump = 0; if (h > wp.hmax) { bump = h - wp.hmax; h = wp.hmax; }
      wp.h = h; const hd = (wp.h - wp.hprev) / dt;
      let N = W0 + wp.k * h + wp.c * hd + 9 * wp.k * bump + (bump > 0 ? 3 * wp.c * Math.max(0, hd) : 0);
      N = Math.max(0, N); wp.N = N;
      wp.cp.copy(_o).addScaledVector(_dir, th);
      const n = normalAt(wp.cp.x, wp.cp.z);
      addForce(_v.copy(upW).multiplyScalar(N), wp.cp);
      // gumi-erők a talaj síkjában
      wp.yaw = wp.front ? yawFor(wp.w, st.s) : 0;
      _f.copy(fwdW).multiplyScalar(Math.cos(wp.yaw)).addScaledVector(rightW, -Math.sin(wp.yaw));
      _f.addScaledVector(n, -_f.dot(n)).normalize(); _s.crossVectors(_f, n).normalize();
      const vp = pointVel(wp.cp, _v); const vl = vp.dot(_f), vs = vp.dot(_s);
      const mu = (ctl.hand && !wp.front) ? MU_HB : MU; const Fmax = mu * N;
      let Fx = Fdrive / 4 - Math.sign(vl) * Math.min(Math.abs(vl) * 400, 0.025 * N);
      if (ctl.brake && !reverse) Fx -= Math.max(-1, Math.min(1, vl * 1.5)) * 0.9 * Fmax;
      if (ctl.hand && !wp.front) Fx -= Math.max(-1, Math.min(1, vl * 2)) * Fmax * 0.8;
      const ref = Math.max(Math.abs(vl), 4.0);
      let Fy = -Fmax * Math.max(-1, Math.min(1, (vs / ref) / 0.14));
      const tot = Math.hypot(Fx, Fy); let slip = 0;
      if (tot > Fmax) { slip = Fmax > 1e-3 ? Math.min(5, tot / Fmax - 1) : 5; const f = Fmax > 0 ? Fmax / tot : 0; Fx *= f; Fy *= f; }
      wp.slip = slip + Math.min(1, Math.abs(vs) / 6);
      const hApp = com.y * 0.55;                       // árkád: a gumi-erő a talaj fölött hat (kisebb borulási nyomaték)
      _o.copy(wp.cp).addScaledVector(upW, hApp);
      addForce(_v2.copy(_f).multiplyScalar(Fx).addScaledVector(_s, Fy), _o);
      // kerék szögsebesség (megjelenítés + fordulatszám)
      const spinUp = (Fdrive !== 0 && slip > 0.05) ? Math.sign(Fdrive) * Math.min(25, slip * 30) : 0;
      wp.omega = (ctl.hand && !wp.front && Math.abs(vl) > 1) || (ctl.brake && !reverse && Math.abs(vl) > 2 && slip > 0.3) ? wp.omega * 0.8 : vl / RW + spinUp;
    }
    if (!wp.contact) {
      const drive = g !== 'N' && ctl.gas ? (REDLINE * tq * 0.95) / ratio * 2 * Math.PI / 60 : 0;
      wp.omega += ((drive || wp.omega * 0.97) - wp.omega) * Math.min(1, dt * (drive ? 2.5 : 0.6));
    }
    wp.spin = (wp.spin + wp.omega * dt) % (Math.PI * 2 * 1000);
  }
  // test ütközése: alváz/tető pontok a tereppel, gömbök a kövekkel
  for (const hp of HULL) {
    _o.copy(hp).applyQuaternion(body.q).add(body.p); const pen = H(_o.x, _o.z) - _o.y;
    if (pen > 0) { const n = normalAt(_o.x, _o.z, new THREE.Vector3()); const vp = pointVel(_o, _v); const vn = vp.dot(n);
      const Fn = Math.max(0, 260000 * pen - 26000 * vn); const vt = vp.addScaledVector(n, -vn); const vtl = vt.length();
      const F = n.multiplyScalar(Fn); if (vtl > 1e-3) F.addScaledVector(vt, -Math.min(0.6 * Fn, vtl * 4000) / vtl);
      addForce(F, _o); }
  }
  for (const sp of SPHERES) {
    _o.copy(sp).applyQuaternion(body.q).add(body.p);
    for (const r of ROCKS) { const dx = _o.x - r.x, dy = _o.y - r.y, dz = _o.z - r.z, d = Math.hypot(dx, dy, dz), pen = r.R + 1.35 - d;
      if (pen > 0 && d > 1e-3) { const n = new THREE.Vector3(dx / d, dy / d, dz / d); const vn = pointVel(_o, _v).dot(n);
        addForce(n.multiplyScalar(Math.max(0, 300000 * pen - 30000 * vn)), _o); } }
    for (const c of CONES) { const dx = c.p.x - _o.x, dz = c.p.z - _o.z, d = Math.hypot(dx, dz);
      if (d < 1.75 && c.p.y < _o.y + 1.2) { const vp = pointVel(_o, _v); c.v.set(vp.x * 1.15 + dx / d * 2.5, 2.5 + 0.12 * vp.length(), vp.z * 1.15 + dz / d * 2.5);
        c.w.set((Math.random() - 0.5) * 12, (Math.random() - 0.5) * 6, (Math.random() - 0.5) * 12); c.rest = false; c.p.x += dx / d * 0.05; c.p.z += dz / d * 0.05; c.p.y += 0.05; } }
  }
  // légellenállás + szöglengés-csillapítás
  Facc.addScaledVector(body.v, -0.9 * speed);
  body.v.addScaledVector(Facc, dt / MASS);
  _qi.copy(body.q).invert(); const tb = _v.copy(Tacc).applyQuaternion(_qi);
  const wb = _v2.copy(body.w).applyQuaternion(_qi);
  wb.x += tb.x / I_BODY.x * dt; wb.y += tb.y / I_BODY.y * dt; wb.z += tb.z / I_BODY.z * dt;
  wb.multiplyScalar(1 - (nContact ? 0.6 : 0.15) * dt);
  body.w.copy(wb).applyQuaternion(body.q);
  body.p.addScaledVector(body.v, dt);
  _wq.set(body.w.x, body.w.y, body.w.z, 0).multiply(body.q);
  body.q.x += 0.5 * dt * _wq.x; body.q.y += 0.5 * dt * _wq.y; body.q.z += 0.5 * dt * _wq.z; body.q.w += 0.5 * dt * _wq.w; body.q.normalize();
  // pálya széle
  const lim2 = HALF - 4; if (Math.abs(body.p.x) > lim2) { body.p.x = Math.sign(body.p.x) * lim2; body.v.x *= -0.3; } if (Math.abs(body.p.z) > lim2) { body.p.z = Math.sign(body.p.z) * lim2; body.v.z *= -0.3; }
  st.airT = nContact ? 0 : st.airT + dt;
  st.upsideT = upW.y < 0.15 && speed < 2.5 ? st.upsideT + dt : 0;
  // főtengely (a megjelenítésben max. 7 fordulat/s, hogy ne stroboszkópozzon)
  const wc = Math.min(st.rpm / 60, 7) * 2 * Math.PI; st.crank -= wc * dt;
  st.dist += Math.abs(vF) * dt;
  // bóják
  for (const c of CONES) { if (c.rest) continue;
    c.v.y -= G * dt; c.p.addScaledVector(c.v, dt); _wq.set(c.w.x * dt * 0.5, c.w.y * dt * 0.5, c.w.z * dt * 0.5, 1); c.q.premultiply(_wq).normalize();
    const gh = H(c.p.x, c.p.z); if (c.p.y < gh) { c.p.y = gh; c.v.y *= -0.25; c.v.x *= 0.7; c.v.z *= 0.7; c.w.multiplyScalar(0.7); if (c.v.lengthSq() < 0.05) c.rest = true; } }
}

// ------------------------------------------------------------------ bemenet
const keymap = { ArrowUp: 'gas', KeyW: 'gas', ArrowDown: 'brake', KeyS: 'brake', ArrowLeft: 'left', KeyA: 'left', ArrowRight: 'right', KeyD: 'right', Space: 'hand' };
const toast = (() => { const el = document.getElementById('toast'); let tm; return msg => { el.textContent = msg; el.hidden = false; clearTimeout(tm); tm = setTimeout(() => { el.hidden = true; }, 1600); }; })();
function shift(d) { const i = GEARS.indexOf(st.gear), j = Math.max(0, Math.min(GEARS.length - 1, i + d)); if (j !== i) { st.gear = GEARS[j]; st.shiftT = 0.22; } }
function action(a) {
  if (a === 'up') shift(1); else if (a === 'down') shift(-1);
  else if (a === 'reset') { resetCar(false); toast(t('reset')); }
  else if (a === 'cam') { st.cam = 1 - st.cam; toast(t(st.cam ? 'camHood' : 'camChase')); }
}
addEventListener('keydown', e => {
  if (e.target && e.target.tagName === 'INPUT') return;
  if (keymap[e.code]) { ctl[keymap[e.code]] = 1; e.preventDefault(); return; }
  if (e.repeat) return;
  if (e.code === 'KeyE' || e.code === 'PageUp') action('up'); else if (e.code === 'KeyQ' || e.code === 'PageDown') action('down');
  else if (e.code === 'KeyR') action('reset'); else if (e.code === 'KeyC') action('cam');
});
addEventListener('keyup', e => { if (keymap[e.code]) ctl[keymap[e.code]] = 0; });
addEventListener('blur', () => { for (const k in ctl) ctl[k] = 0; });
document.querySelectorAll('#touch [data-k]').forEach(b => {
  const k = b.dataset.k, hold = ['gas', 'brake', 'left', 'right'].includes(k);
  b.addEventListener('pointerdown', e => { e.preventDefault(); try { b.setPointerCapture?.(e.pointerId); } catch (_) {} b.classList.add('on'); if (hold) ctl[k] = 1; else action(k); });
  const up = e => { b.classList.remove('on'); if (hold) ctl[k] = 0; };
  b.addEventListener('pointerup', up); b.addEventListener('pointercancel', up); b.addEventListener('lostpointercapture', up);
});
const keysEl = document.getElementById('keys');
document.getElementById('keysX').addEventListener('click', () => keysEl.classList.toggle('min'));

// ------------------------------------------------------------------ kamera, HUD, fő ciklus
const camPos = new THREE.Vector3(-12, 6, 0), camLook = new THREE.Vector3();
const HOOD = new THREE.Vector3(128, 162, 0).multiplyScalar(SC).sub(com);   // a fülketető fölött, előre-lefelé nézve (a motorháztető látszik)
const elG = document.getElementById('gear'), elS = document.getElementById('spd'), elSR = document.getElementById('spdReal'), elR = document.getElementById('rpm'), elRB = document.getElementById('rpmBar');
let hudT = 0, flipShown = false;
function updateCamera(dt, snap) {
  if (st.cam === 1) {
    camera.position.copy(HOOD).applyQuaternion(body.q).add(body.p);
    _v.copy(fwdW).multiplyScalar(20).add(camera.position).addScaledVector(upW, -2.6); camera.up.copy(upW); camera.lookAt(_v); return;
  }
  camera.up.set(0, 1, 0);
  const fl = _v.set(fwdW.x, 0, fwdW.z); if (fl.lengthSq() < 1e-4) fl.set(1, 0, 0); fl.normalize();
  const vfl = _v2.set(body.v.x, 0, body.v.z); const back = vfl.length() > 3 && vfl.dot(fl) < -2 ? vfl.normalize().negate() : fl;   // tolatáskor is mögötte
  const want = _o.copy(body.p).addScaledVector(back, -10.5); want.y = body.p.y + 3.6 + Math.min(4, body.v.length() * 0.03);
  const k = snap ? 1 : 1 - Math.exp(-dt * 3.2); camPos.lerp(want, k);
  const gh = H(camPos.x, camPos.z) + 1.0; if (camPos.y < gh) camPos.y = gh;
  camLook.lerp(_s.copy(body.p).addScaledVector(fl, 2.5).add(new THREE.Vector3(0, 0.9, 0)), snap ? 1 : 1 - Math.exp(-dt * 8));
  camera.position.copy(camPos); camera.lookAt(camLook);
}
function hud(dt) {
  hudT -= dt; if (hudT > 0) return; hudT = 0.08;
  const kmh = body.v.length() * 3.6;
  elG.textContent = st.gear === 'N' ? 'N' : String(st.gear);
  elS.textContent = fmt(kmh); elSR.textContent = fmt(kmh / 16, 1); elR.textContent = fmt(st.rpm);
  elRB.style.width = (100 * Math.min(1, st.rpm / REDLINE)).toFixed(1) + '%';
  if (st.upsideT > 1.5 && !flipShown) { toast(t('flip')); flipShown = true; } if (st.upsideT === 0) flipShown = false;
}
const dustCol = new THREE.Vector3();
function emitDust(dt) {
  for (const wp of wheelsP) { if (!wp.contact) continue;
    const v = Math.abs(wp.omega * RW); const rate = Math.min(1, v / 18) * 40 + wp.slip * 50; let n = rate * dt; if (MOBILE) n *= 0.6; if (!(n > 0)) continue; n = Math.min(n, 4);   // felső korlát: földetéréskor a csúszás nagy lehet
    while (n > 0) { if (Math.random() < n) { const vp = pointVel(wp.cp, _v);
        dust.emit(wp.cp.x + (Math.random() - 0.5) * 0.8, wp.cp.y + 0.15, wp.cp.z + (Math.random() - 0.5) * 0.8, -vp.x * 0.25 + (Math.random() - 0.5) * 2, 0.6 + Math.random() * 1.2, -vp.z * 0.25 + (Math.random() - 0.5) * 2, 0.9 + Math.random() * 0.8); }
      n -= 1; } }
}
const visState = { hmm: [0, 0, 0, 0], s: 0, crank: 0, spin: st.spin };
function syncVisual() {
  truck.position.copy(body.p); truck.quaternion.copy(body.q);
  wheelsP.forEach((wp, i) => { visState.hmm[i] = Math.max(-16, Math.min(16, wp.h / SC)); st.spin[wp.w] = wp.spin; });
  visState.s = st.s; visState.crank = st.crank; poseTruck(visState);
  sun.position.copy(body.p).addScaledVector(SUN_DIR, 60); sun.target.position.copy(body.p);
  scene.userData.sky.position.copy(camera.position);
}

resetCar(true); for (let i = 0; i < 240; i++) step(DT);   // leülepedés
updateCamera(0, true); syncVisual();
renderer.compile(scene, camera);
document.getElementById('load').classList.add('done');
let last = performance.now(), acc = 0, frames = 0, fpsT = 0, fps = 0, simT = 0;
renderer.setAnimationLoop(() => {
  const now = performance.now(); let dt = Math.min(0.1, (now - last) / 1000); last = now;
  acc += dt; let n = 0; while (acc >= DT && n < 10) { step(DT); acc -= DT; n++; simT += DT; } if (n === 10) acc = 0;
  if (!Number.isFinite(body.p.x + body.p.y + body.p.z + body.v.x + body.v.y + body.v.z + body.q.w)) { resetCar(true); for (const wp of wheelsP) wp.slip = 0; }   // NaN-védelem
  syncVisual(); emitDust(dt); dust.update(dt); updateCamera(dt, false); hud(dt);
  dust.m.uniforms.uScale.value = innerHeight * renderer.getPixelRatio() * 0.5;
  renderer.render(scene, camera);
  frames++; fpsT += dt; if (fpsT > 1) { fps = frames / fpsT; frames = 0; fpsT = 0; }
});
// teszt-/hibakereső felület (Playwright)
window.__game = { state: () => ({ x: body.p.x, y: body.p.y, z: body.p.z, v: body.v.length(), gear: st.gear, rpm: st.rpm, s: st.s, h: wheelsP.map(w => +(w.h / SC).toFixed(2)),
  contact: wheelsP.map(w => w.contact), fps, simT, crank: st.crank, calls: renderer.info.render.calls, tris: renderer.info.render.triangles }), ctl, action };
