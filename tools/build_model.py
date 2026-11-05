#!/usr/bin/env python3
"""HELYŐRZŐ truck.glb építése a digitális makettből (layout_v2.json) és a könyvtár STL-jeiből.

Futtatás:  python3 tools/build_model.py [--layout PATH] [--stl-dir PATH]
Kimenet:   assets/model/truck.glb  +  assets/model/parts.json

A VÉGLEGES modell (SolidWorks-összeállítás -> Blender -> GLB) ugyanezt a konvenciót kövesse
(lásd README.md és 12_weboldal.md):
  * glTF: +X előre, +Y fel, +Z jobbra; a gyökér "truck" csomópont scale = 0.001 (mm -> m)
  * csoport-csomópontok:  G_<reszegyseg>      (pl. G_vaz, G_kerekek, G_hatso_hid ...)
  * alkatrész-csomópontok: P_<cikkszam>_<nn>   extras: {group, partno, name, design_id}
  * forgó kerék-pivotok:   W_FL, W_FR, W_RL, W_RR (a kerék közepén; forgástengely: helyi +Z)
  * animációk: "wheels_spin" (kerékforgás) – a nézegető minden beépített klipet listáz
"""
import argparse, json, glob, os, re, math
import numpy as np, trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual import TextureVisuals

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
ap.add_argument('--layout', default='/home/claude/work/layout/layout_v2.json')
ap.add_argument('--stl-dir', default='/mnt/user-data/uploads/AI challange/cad/lib')
ap.add_argument('--manifests', default='/home/claude/work/cadlib')
a = ap.parse_args()

L = json.load(open(a.layout))
names = {}
for f in glob.glob(os.path.join(a.manifests, 'manifest_*.json')):
    for p in json.load(open(f)).get('parts', []):
        if 'partno' in p: names.setdefault(p['partno'], p.get('name', ''))

GROUPS = [  # id, hu, en, szín
    ('vaz', 'Váz', 'Frame', '#5b6470'),
    ('elso_futomu', 'Első futómű', 'Front suspension', '#8a8f98'),
    ('hatso_hid', 'Hátsó híd', 'Rear axle', '#8a8f98'),
    ('hajtaslanc', 'Hajtás / váltó', 'Driveline / gearbox', '#b8bcc4'),
    ('V8', 'V8', 'V8', '#c9ccd2'),
    ('karosszeria', 'Karosszéria', 'Body', '#2a2d33'),
    ('kerekek', 'Kerekek', 'Wheels', '#1b1c1f'),
]
GMAP = {'elso_futomu_bal': 'elso_futomu', 'elso_futomu_jobb': 'elso_futomu', 'elso_diff': 'elso_futomu',
        'kormany': 'elso_futomu', 'valto': 'hajtaslanc'}
COL = {'44771': '#16171a', '15038': '#c7cad0', '2909': '#F28C28', '62821': '#9aa0a8'}

# STL-ek (a SolidWorks STL-exportja pozitív térbe tolt; a helyi origót a manifest-konvencióból állítjuk vissza)
stl = {}
for f in glob.glob(os.path.join(a.stl_dir, '*', '*.STL')):
    pn = os.path.basename(f).split('_')[0]
    m = trimesh.load(f, force='mesh')
    lo, hi = m.bounds
    if pn in ('44771', '15038', '62821'):
        off = -(lo + hi) / 2                      # forgásszimmetrikus: origó a középen
    else:
        off = -lo - np.array([3.6, 3.6, 3.6])      # gerendák/keretek: origó az első lyuk közepén
        if pn == '2909': off = -np.array([4, 4, 0]) - [0, 0, 0]
    m.apply_translation(off)
    stl[pn] = m

def beam_proxy(n):  # n lyukú egyenes gerenda helyettesítő: lekerekített hasáb, első lyuk az origóban
    Lm = 8 * n - 0.8
    b = trimesh.creation.box(extents=[Lm, 7.2, 7.2]); b.apply_translation([Lm / 2 - 3.6, 0, 0])
    return b

def mat(hexc, rough=0.55, metal=0.0):
    lin = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4  # glTF: lineáris szín
    c = [round(lin(int(hexc[i:i + 2], 16) / 255) * 255) for i in (1, 3, 5)] + [255]
    return PBRMaterial(baseColorFactor=c, metallicFactor=metal, roughnessFactor=rough)

R = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)  # layout (z fel) -> glTF (y fel)
sc = trimesh.Scene()
G = sc.graph
G.update(frame_from=G.base_frame, frame_to='truck', matrix=np.diag([0.001, 0.001, 0.001, 1]))
for gid, *_ in GROUPS:
    G.update(frame_from='truck', frame_to='G_' + gid, matrix=np.eye(4))

geoms = {}
extras = {}
cnt = {}
wheels = {}
skipped = 0
for p in L['alkatreszek']:
    pn = p['cikkszam'].split()[0].split('/')[0]
    grp = GMAP.get(p['reszegyseg'], p['reszegyseg'])
    if grp not in [g[0] for g in GROUPS]: grp = 'karosszeria'
    if p['reszegyseg'] == 'karosszeria' and pn in ('44771', '15038'):
        continue  # pótkerék: kihagyva a helyőrzőben
    mesh = stl.get(pn)
    m = re.search(r'gerenda_(\d+)L', p['fajl'])
    if mesh is None and m: mesh = ('beam', int(m.group(1)))
    if mesh is None: skipped += 1; continue
    key = pn if not isinstance(mesh, tuple) else 'beam%d' % mesh[1]
    if key not in geoms:
        g = (beam_proxy(mesh[1]) if isinstance(mesh, tuple) else mesh.copy())
        colr = COL.get(pn, dict((x[0], x[3]) for x in GROUPS)[grp])
        g.visual = TextureVisuals(material=mat(colr, 0.85 if pn == '44771' else 0.5, 0.3 if pn == '15038' else 0.0))
        geoms[key] = g
    T = np.array(p['T'], float)
    if p.get('tukrozott'): T = T @ np.diag([1, 1, -1, 1])
    Tg = R @ T
    cnt[pn] = cnt.get(pn, 0) + 1
    node = 'P_%s_%02d' % (pn, cnt[pn])
    parent = 'G_' + grp
    if grp == 'kerekek':
        c = Tg[:3, 3]
        wid = ('F' if c[0] > 96 else 'R') + ('L' if c[2] < 0 else 'R')
        if wid not in wheels:
            wheels[wid] = c
            P = np.eye(4); P[:3, 3] = c
            G.update(frame_from=parent, frame_to='W_' + wid, matrix=P)
        parent = 'W_' + wid
        Pinv = np.eye(4); Pinv[:3, 3] = -wheels[wid]
        Tg = Pinv @ Tg
    sc.add_geometry(geoms[key], geom_name=key, node_name=node, parent_node_name=parent, transform=Tg)
    extras[node] = {'group': grp, 'partno': pn, 'design_id': pn,
                    'name': names.get(pn, ('Gerenda %dL (helyettesítő)' % mesh[1]) if isinstance(mesh, tuple) else pn)}

out = os.path.join(SITE, 'assets/model/truck.glb')
os.makedirs(os.path.dirname(out), exist_ok=True)
sc.export(out)

# --- utófeldolgozás: extras + kerékforgás-animáció (pygltflib) ---
import pygltflib, struct
g = pygltflib.GLTF2().load(out)
idx = {n.name: i for i, n in enumerate(g.nodes)}
for n in g.nodes:
    if n.name in extras: n.extras = extras[n.name]
    elif n.name and n.name.startswith('G_'): n.extras = {'group': n.name[2:]}
# A kerékpivot helyi tengelye: glTF Z (= layout -y). Előremenetnél a kerék -Z körül forog.
N = 25; dur = 2.0
times = np.linspace(0, dur, N).astype(np.float32)
quats = np.array([[0, 0, math.sin(-t / dur * math.pi), math.cos(-t / dur * math.pi)] for t in times], np.float32)
blob = bytearray(g.binary_blob())
def add_acc(arr, typ, mn=None, mx=None):
    while len(blob) % 4: blob.append(0)
    off = len(blob); blob.extend(arr.tobytes())
    g.bufferViews.append(pygltflib.BufferView(buffer=0, byteOffset=off, byteLength=arr.nbytes))
    acc = pygltflib.Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ,
                             min=mn, max=mx)
    g.accessors.append(acc); return len(g.accessors) - 1
ti = add_acc(times, 'SCALAR', [0.0], [dur])
qi = add_acc(quats, 'VEC4')
anim = pygltflib.Animation(name='wheels_spin', samplers=[pygltflib.AnimationSampler(input=ti, output=qi, interpolation='LINEAR')], channels=[])
for w in wheels:
    anim.channels.append(pygltflib.AnimationChannel(sampler=0, target=pygltflib.AnimationChannelTarget(node=idx['W_' + w], path='rotation')))
g.animations = [anim]
g.buffers[0].byteLength = len(blob)
g.set_binary_blob(bytes(blob))
g.save_binary(out)

parts = {'version': 1, 'units': 'mm (gyökér-scale 0.001)', 'axes': '+X előre, +Y fel, +Z jobbra',
         'placeholder': True,
         'groups': [{'id': gid, 'hu': hu, 'en': en, 'color': c} for gid, hu, en, c in GROUPS],
         'parts': {k: v for k, v in sorted(extras.items())}}
json.dump(parts, open(os.path.join(SITE, 'assets/model/parts.json'), 'w'), ensure_ascii=False, indent=1)
print('nodes', len(extras), 'geoms', len(geoms), 'skipped', skipped, 'wheels', sorted(wheels),
      'size %.2f MB' % (os.path.getsize(out) / 1e6))
