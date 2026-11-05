#!/usr/bin/env python3
"""VEM-eredmények -> böngészőbarát GLB-k (csúcsszínek + deformációs morph target) + cases.json.

Futtatás: python3 tools/build_fem.py
  1) beam15  – VALÓDI CalculiX-eredmény (/home/claude/work/feas/beam_result.vtu: 'von Mises [MPa]', 'u')
  2) axle_demo – SZINTETIKUS DEMÓ (csavart kereszttengely, analitikus közelítés), egyértelmű DEMÓ jelöléssel

FEM GLB formátum (a VEM-ágens ehhez igazodjon):
  * egyetlen mesh, egyetlen primitive, háromszögek, egység: mm, +Y fel
  * POSITION = deformálatlan felület,  COLOR_0 = feszültség színe (a SKÁLA ebben a fájlban: SCALE lent)
  * _STRESS (float, egyedi attribútum) = von Mises [MPa] csúcsonként – az egérrel leolvasáshoz
  * morph target 0: POSITION-elmozdulás = valódi elmozdulás (u) mm-ben, 1.0 súly = valós deformáció
  * mesh.extras: {"case": id, "vmin": MPa, "vmax": MPa, "umax_mm": mm}
"""
import json, os, numpy as np, pygltflib

HERE = os.path.dirname(os.path.abspath(__file__)); SITE = os.path.dirname(HERE)
OUT = os.path.join(SITE, 'assets/fem'); os.makedirs(OUT, exist_ok=True)
# színskála: grafitkék -> kék -> türkiz -> homok -> narancs (#F28C28 a csúcs)
SCALE = [(0.0, '#1d2a44'), (0.25, '#2f5f9e'), (0.5, '#4fa3a5'), (0.75, '#d9c27a'), (1.0, '#F28C28')]

def cmap(t):
    t = np.clip(t, 0, 1); xs = [s[0] for s in SCALE]
    cs = np.array([[int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)] for _, c in SCALE])
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], 1)

def srgb2lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def write_glb(path, P, F, S, U, extras):
    vmin, vmax = float(S.min()), float(S.max())
    C = srgb2lin(cmap((S - vmin) / (vmax - vmin))).astype(np.float32)
    P = P.astype(np.float32); U = U.astype(np.float32); S = S.astype(np.float32); F = F.astype(np.uint32)
    blobs = []; views = []; accs = []
    def add(arr, typ, comp, target=None, mm=False):
        off = sum(len(b) for b in blobs)
        b = arr.tobytes(); pad = (-len(b)) % 4; blobs.append(b + b'\0' * pad)
        views.append(pygltflib.BufferView(buffer=0, byteOffset=off, byteLength=len(b), target=target))
        kw = {}
        if mm: kw = dict(min=arr.min(0).tolist(), max=arr.max(0).tolist())
        accs.append(pygltflib.Accessor(bufferView=len(views) - 1, componentType=comp, count=len(arr), type=typ, **kw))
        return len(accs) - 1
    ip = add(P, 'VEC3', 5126, 34962, True); ic = add(C, 'VEC3', 5126, 34962)
    is_ = add(S, 'SCALAR', 5126, 34962); iu = add(U, 'VEC3', 5126, 34962, True)
    ii = add(F.ravel(), 'SCALAR', 5125, 34963)
    prim = pygltflib.Primitive(attributes=pygltflib.Attributes(POSITION=ip, COLOR_0=ic, _STRESS=is_),
                               indices=ii, material=0, targets=[{'POSITION': iu}])
    g = pygltflib.GLTF2(
        scene=0, scenes=[pygltflib.Scene(nodes=[0])],
        nodes=[pygltflib.Node(name='fem', mesh=0)],
        meshes=[pygltflib.Mesh(name='fem', primitives=[prim], weights=[0.0], extras=extras)],
        materials=[pygltflib.Material(name='fem', doubleSided=True, pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
            baseColorFactor=[1, 1, 1, 1], metallicFactor=0.0, roughnessFactor=0.6))],
        accessors=accs, bufferViews=views, buffers=[pygltflib.Buffer(byteLength=sum(len(b) for b in blobs))])
    g.set_binary_blob(b''.join(blobs)); g.save_binary(path)
    return vmin, vmax, os.path.getsize(path)

cases = []
# ---- 1) valódi: 15L gerenda, konzol ----
import pyvista as pv
vtu = '/home/claude/work/feas/beam_result.vtu'
if os.path.exists(vtu):
    m = pv.read(vtu).extract_surface(nonlinear_subdivision=0).triangulate().clean()
    P = np.asarray(m.points); F = np.asarray(m.faces).reshape(-1, 4)[:, 1:]
    S = np.asarray(m['von Mises [MPa]']); U = np.asarray(m['u'])
    umax = float(np.linalg.norm(U, axis=1).max())
    vmin, vmax, sz = write_glb(os.path.join(OUT, 'beam15.glb'), P, F, S, U,
                               {'case': 'beam15', 'vmin': float(S.min()), 'vmax': float(S.max()), 'umax_mm': umax})
    # kézi számítás: konzol, F=10 N, tömör 7.2x7.2 négyzet felső becslés / lyukas szelvény
    print('beam15', len(P), 'pts', len(F), 'tris', '%.1f kB' % (sz / 1e3), 'vM max %.1f' % vmax, 'umax %.2f' % umax)
    cases.append({'id': 'beam15', 'file': 'assets/fem/beam15.glb', 'demo': False,
                  'title': {'hu': '15L gerenda – konzol', 'en': '15L beam – cantilever'},
                  'desc': {'hu': 'Egyik végén befogott 32278-as gerenda, a szabad végén 10 N lefelé. Anyag: ABS (E ≈ 2,3 GPa, feltevés). CalculiX, másodfokú tetraéderek.',
                           'en': 'A 32278 beam clamped at one end, 10 N downward at the free end. Material: ABS (E ≈ 2.3 GPa, assumed). CalculiX, quadratic tetrahedra.'},
                  'load': {'hu': '10 N a gerenda végén', 'en': '10 N at the tip'},
                  'vmin': round(vmin, 2), 'vmax': round(vmax, 1), 'umax_mm': round(umax, 2),
                  'hand': None, 'deviation_pct': None,
                  'note': {'hu': 'A csúcsfeszültség a befogásnál, a lyukak mellett. A kézi számítás összevetése a VEM-ágens feladata.',
                           'en': 'Peak stress at the clamp, next to the holes. Hand-calc comparison pending (FEM agent).'}})

# ---- 2) DEMÓ: csavart kereszttengely (analitikus közelítés) ----
a, b = 2.4, 0.9  # kereszt: 4.8 x 1.8 mm karok
sec = np.array([[b, b], [a, b], [a, -b], [b, -b], [b, -a], [-b, -a], [-b, -b], [-a, -b], [-a, b], [-b, b], [-b, a], [b, a]])
n = len(sec); Lx = 64.0; NS = 64
xs = np.linspace(0, Lx, NS + 1)
P = []; F = []
for i, x in enumerate(xs):
    for (y, z) in sec: P.append([x, y, z])
for i in range(NS):
    for j in range(n):
        p0 = i * n + j; p1 = i * n + (j + 1) % n; q0 = p0 + n; q1 = p1 + n
        F += [[p0, q0, p1], [p1, q0, q1]]
for end, flip in ((0, True), (NS, False)):
    c = len(P); P.append([xs[end], 0, 0])
    for j in range(n):
        t = [c, end * n + j, end * n + (j + 1) % n]; F.append(t[::-1] if flip else t)
P = np.array(P, float); F = np.array(F)
r = np.hypot(P[:, 1], P[:, 2])
Tq = 200.0  # N·mm
S = 18.0 * (r / r.max()) * (0.85 + 0.15 * np.cos(np.pi * P[:, 0] / Lx) ** 2)  # demó-eloszlás
phi = np.radians(12.0) * P[:, 0] / Lx
U = np.zeros_like(P)
U[:, 1] = P[:, 1] * np.cos(phi) - P[:, 2] * np.sin(phi) - P[:, 1]
U[:, 2] = P[:, 1] * np.sin(phi) + P[:, 2] * np.cos(phi) - P[:, 2]
vmin, vmax, sz = write_glb(os.path.join(OUT, 'axle_demo.glb'), P, F, S, U,
                           {'case': 'axle_demo', 'vmin': float(S.min()), 'vmax': float(S.max()), 'umax_mm': float(np.linalg.norm(U, axis=1).max())})
print('axle_demo', len(P), 'pts', '%.1f kB' % (sz / 1e3))
cases.append({'id': 'axle_demo', 'file': 'assets/fem/axle_demo.glb', 'demo': True,
              'title': {'hu': 'DEMÓ – tengelycsavarás', 'en': 'DEMO – axle torsion'},
              'desc': {'hu': 'Szintetikus helyőrző: 8L kereszttengely csavarása, analitikus közelítéssel színezve. A valódi VEM-eset ide kerül.',
                       'en': 'Synthetic placeholder: an 8L cross axle in torsion, coloured by an analytic approximation. The real FEM case goes here.'},
              'load': {'hu': '200 N·mm csavarónyomaték', 'en': '200 N·mm torque'},
              'vmin': round(vmin, 2), 'vmax': round(vmax, 1), 'umax_mm': None,
              'hand': None, 'deviation_pct': None, 'note': {'hu': 'DEMÓ – nem mérnöki eredmény.', 'en': 'DEMO – not an engineering result.'}})

json.dump({'scale': SCALE, 'units': 'MPa', 'cases': cases}, open(os.path.join(OUT, 'cases.json'), 'w'), ensure_ascii=False, indent=1)
