// Közös three.js "színpad": renderer, kamera, OrbitControls, fények, láthatóság szerinti renderelés.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function createStage(el, { env = true } = {}) {
  const canvas = el.querySelector('canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  const scene = new THREE.Scene();
  if (env) {
    const pm = new THREE.PMREMGenerator(renderer);
    scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.4;
  }
  scene.add(new THREE.HemisphereLight(0xffffff, 0x202024, 0.6));
  const key = new THREE.DirectionalLight(0xffffff, 1.6); key.position.set(3, 5, 4); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffd9b0, 0.6); rim.position.set(-4, 2, -3); scene.add(rim);
  const camera = new THREE.PerspectiveCamera(32, 1, 0.001, 100);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.autoRotate = false; controls.autoRotateSpeed = 0.6;

  let visible = false, raf = 0, home = null;
  const hooks = [];
  const clock = new THREE.Clock();
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(canvas);
  function loop() {
    raf = visible ? requestAnimationFrame(loop) : 0;
    const dt = Math.min(clock.getDelta(), 0.1);
    hooks.forEach(f => f(dt));
    controls.update();
    renderer.render(scene, camera);
  }
  new IntersectionObserver(es => {
    visible = es[0].isIntersecting;
    if (visible && !raf) { clock.getDelta(); loop(); }
  }, { rootMargin: '100px' }).observe(el);

  function frame(obj, { dir = [1, 0.55, 1.25], pad = 1.15 } = {}) {
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
    const r = size.length() / 2;
    const fov = camera.fov * Math.PI / 180;
    const fit = Math.max(r / Math.sin(fov / 2), r / Math.sin(Math.atan(Math.tan(fov / 2) * camera.aspect)));
    const d = new THREE.Vector3(...dir).normalize().multiplyScalar(fit * pad);
    camera.position.copy(c).add(d); camera.near = r / 100; camera.far = r * 100; camera.updateProjectionMatrix();
    controls.target.copy(c); controls.minDistance = r * 0.4; controls.maxDistance = r * 6;
    home = { p: camera.position.clone(), t: c.clone() };
    controls.update();
    return { box, size, center: c, radius: r };
  }
  function reset() { if (home) { camera.position.copy(home.p); controls.target.copy(home.t); controls.update(); } }
  resize();
  return { THREE, renderer, scene, camera, controls, frame, reset, onFrame: f => hooks.push(f), el, canvas };
}

export function msg(el, text, err = false) {
  const m = el.querySelector('[data-role=msg]');
  if (!m) return;
  if (text == null) { el.classList.add('ready'); return; }
  m.classList.toggle('err', err); m.textContent = text;
}
