#!/usr/bin/env python3
"""JÁTÉK-GLB a „Próbaút" aloldalhoz (probaut/): ugyanaz a 592 elemes jármű, mint az assets/model/truck.glb, de játékra optimalizálva.

  python3 tools/build_game_glb.py        # -> probaut/assets/truck_game.glb + probaut/assets/truck_game.json

A kinematika a build_anim_glb.py-ból jön (E.kin(st_full(...)), TT_GEOM = r2_geometry.json, r_remap + cv_adapter) – semmi nincs
újraszámolva, csak mintavételezve:
  - minden elemre megnézzük, mely állapotváltozóktól függ (hL, hR, s, h_r, roll, C; th = kerékforgás);
  - a független elemek EGY statikus hálóba olvadnak (anyag helyett csúcsszín -> kevés draw call);
  - a mozgó elemek csoportokba kerülnek (azonos relatív mozgás-sorozat = egy merev csomópont), és csoportonként egy
    mintatáblát írunk: FL/FR: (h, s) 9×9 rács, REAR: (h_r, roll) 7×9 rács, STEER: s 17 minta, CRANK: C 0..2π 37 minta;
  - a kerekek (gumi, felni + a velük együtt, a kerék tengelye körül forgó elemek) külön forgó gyermek-csomópontba kerülnek
    (a játék forgatja a th szerint, a tengely a JSON-ban).
A JS bilineárisan interpolál a táblák között (pozíció lerp, kvaternió nlerp). Egységek: mm, glTF-tengelyek (+X előre, +Y fel, +Z jobbra).
"""
import os, sys, json, math, subprocess, collections
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); SITE = os.path.dirname(HERE)
os.environ.setdefault("TT_GEOM", "/home/claude/work/pyA/R_rogzites/r2_geometry.json")
sys.path.insert(0, HERE)
_argv = sys.argv; sys.argv = [sys.argv[0]]
import build_anim_glb as B                      # betölti a kinematikát (nem épít glb-t: __main__-guard)
sys.argv = _argv
E, M, st = B.E, B.M, B.st_full
NE, names, parts, kinds, grps, SG = B.NE, B.names, B.parts, B.kinds, B.grps, B.SG
C_GL = B.C_GL
OUT = os.path.join(SITE, "probaut", "assets"); os.makedirs(OUT, exist_ok=True)
GLTFPACK = "/tmp/claude-0/-home-claude/745ae32e-558c-5453-92a9-05a4066db304/scratchpad/npm/node_modules/.bin/gltfpack"

REST = E.kin(st(C=0.0))
S_MAX = float(M.S_MAX)
# ------------------------------------------------------------------ függőségek
def dmask(**kw):
    F = E.kin(st(C=kw.pop("C", 0.0), **kw)); return np.abs(F - REST).reshape(NE, -1).max(1) > 1e-4
DEP = {k: dmask(**kw) for k, kw in dict(hL=dict(hL=12.0), hR=dict(hR=12.0), s=dict(s=0.7 * S_MAX), h_r=dict(h_r=6.0),
                                       roll=dict(roll=8.0), C=dict(C=1.0), th=dict(th=0.7)).items()}
def sig(j): return tuple(k for k in DEP if DEP[k][j])

GRID = {
    "FL": dict(ax=[("hL", np.linspace(-16, 16, 9)), ("s", np.linspace(-S_MAX, S_MAX, 9))]),
    "FR": dict(ax=[("hR", np.linspace(-16, 16, 9)), ("s", np.linspace(-S_MAX, S_MAX, 9))]),
    "REAR": dict(ax=[("h_r", np.linspace(-9, 9, 7)), ("roll", np.linspace(-11, 11, 9))]),
    "STEER": dict(ax=[("s", np.linspace(-S_MAX, S_MAX, 17))]),
    "CRANK": dict(ax=[("C", np.linspace(0, 2 * math.pi, 37))]),
}
def family(j):
    s = sig(j)
    if "hL" in s: return "FL"
    if "hR" in s: return "FR"
    if "h_r" in s or "roll" in s: return "REAR"
    if "s" in s: return "STEER"
    if "C" in s: return "CRANK"
    return "STATIC"
FAM = [family(j) for j in range(NE)]
for j in range(NE):
    s = sig(j)
    assert not (("hL" in s or "hR" in s) and ("h_r" in s or "C" in s)), (names[j], s)

def states(fam):
    ax = GRID[fam]["ax"]
    if len(ax) == 1: return [{ax[0][0]: float(a)} for a in ax[0][1]], [len(ax[0][1])]
    return [{ax[0][0]: float(a), ax[1][0]: float(b)} for a in ax[0][1] for b in ax[1][1]], [len(ax[0][1]), len(ax[1][1])]
SAMPLES = {}
for fam in GRID:
    sts, shape = states(fam)
    SAMPLES[fam] = (np.array([E.kin(st(C=kw.get("C", 0.0), **{k: v for k, v in kw.items() if k != "C"})) for kw in sts]), shape)

# ------------------------------------------------------------------ kerekek (forgó gyermek)
WHEELS = {"FL": "gumi_44771_B", "FR": "gumi_44771_J", "RL": "a2_gumi_bal_44771", "RR": "a2_gumi_jobb_44771"}
WC = {w: REST[names.index(n)][:3, 3].copy() for w, n in WHEELS.items()}          # jármű-KR, mm
Fth = E.kin(st(C=0.0, th=0.3))
def wheel_of(j):
    if FAM[j] not in ("FL", "FR", "REAR") or not DEP["th"][j]: return None
    Rel = Fth[j] @ np.linalg.inv(REST[j])
    cands = ["FL"] if FAM[j] == "FL" else ["FR"] if FAM[j] == "FR" else (["RL"] if REST[j][1, 3] > 0 else ["RR"])
    for w in cands:
        c = WC[w]; moved = Rel[:3, :3] @ c + Rel[:3, 3]
        ax = Rel[:3, :3] - np.eye(3)
        if np.linalg.norm(moved - c) < 0.05 and abs(Rel[1, 1] - 1) < 1e-6: return w
    return None
WOF = [wheel_of(j) for j in range(NE)]
for w, n in WHEELS.items(): assert WOF[names.index(n)] == w, (w, WOF[names.index(n)])

# ------------------------------------------------------------------ csoportosítás (azonos relatív mozgás-sorozat)
def rel_series(fam, j):
    F, _ = SAMPLES[fam]; return np.einsum("kab,bc->kac", F[:, j], np.linalg.inv(REST[j]))
clusters = collections.OrderedDict()                # kulcs -> lista
CR = {}                                             # kulcs -> relatív sorozat
for j in range(NE):
    fam = FAM[j]
    if fam == "STATIC": clusters.setdefault(("STATIC",), []).append(j); continue
    if WOF[j]: clusters.setdefault(("WHEEL", WOF[j]), []).append(j); continue
    R = rel_series(fam, j); hit = None
    for key, mem in clusters.items():
        if key[0] != fam: continue
        if np.abs(CR[key] - R).max() < 2e-3: hit = key; break
    if hit is None:
        hit = (fam, len([k for k in clusters if k[0] == fam])); clusters[hit] = []; CR[hit] = R
    clusters[hit].append(j)
# a kerék-csoport mozgása = a gumi relatív mozgása (a forgást a gyermek adja); ellenőrzés: az együtt forgó elemek ugyanígy mozognak
for w, n in WHEELS.items():
    fam = "REAR" if w[0] == "R" else w
    R0_ = rel_series(fam, names.index(n))
    for j in clusters[("WHEEL", w)]:
        assert np.abs(rel_series(fam, j) - R0_).max() < 2e-3, ("kerék-elem eltérő mozgás", names[j])

# ------------------------------------------------------------------ hálók
MS = dict(np.load(os.path.join(B.PREVIS, "cache/meshes.npz"))); MS.update(dict(np.load("/home/claude/work/export/py/R/mesh_new.npz")))
_geo = {}
def geom(p):
    if p not in _geo:
        tm = trimesh.Trimesh(vertices=MS["V_" + p].astype(np.float64), faces=MS["F_" + p], process=False)
        sm = trimesh.graph.smooth_shade(tm, angle=math.radians(32))
        _geo[p] = (np.asarray(sm.vertices, np.float64), np.asarray(sm.vertex_normals, np.float64), np.asarray(sm.faces, np.int64))
    return _geo[p]
PAINT = lambda j: SG[j] == "karosszeria" and kinds[j] in ("panel", "panel2")
def bake(js, origin=np.zeros(3)):
    """elemek a nyugalmi pózban, glTF-KR, mm, origin levonva; két primitív: fényezés / egyéb"""
    out = {}
    for j in js:
        V, N, F = geom(parts[j]); T = REST[j]
        v = (C_GL @ (V @ T[:3, :3].T + T[:3, 3]).T).T - origin
        Rn = np.linalg.inv(T[:3, :3]).T; n = (C_GL @ (N @ Rn.T).T).T; n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        col = np.array(B.lin(B.COL[kinds[j]]))
        key = "paint" if PAINT(j) else "mech"
        o = out.setdefault(key, [[], [], [], [], 0])
        o[0].append(v.astype(np.float32)); o[1].append(n.astype(np.float32)); o[2].append(np.tile(col, (len(v), 1)).astype(np.float32))
        o[3].append(F + o[4]); o[4] += len(v)
    return {k: (np.concatenate(a), np.concatenate(b), np.concatenate(c), np.concatenate(d).astype(np.uint32)) for k, (a, b, c, d, _) in out.items()}

def trs(Mx):
    t, q, s = B.trs(Mx); return t, q
def rel_trs(R):
    """relatív (jármű-KR) mátrix -> glTF-KR TRS (t mm, q xyzw)"""
    Rg = C_GL @ R[:3, :3] @ C_GL.T; tg = C_GL @ R[:3, 3]
    return tg, B.quat(Rg)

G = B.GLB(); g = G.g; g["animations"] = []
g["asset"]["generator"] = "ai-engineered-car build_game_glb.py"
MATS = {"mech": (0.62, 0.15), "paint": (0.38, 0.05), "tyre": (0.95, 0.0)}
for k, (r, m) in MATS.items():
    g["materials"].append(dict(name="g_" + k, doubleSided=True, pbrMetallicRoughness=dict(baseColorFactor=[1, 1, 1, 1], metallicFactor=m, roughnessFactor=r)))
MI = {k: i for i, k in enumerate(MATS)}
def add_mesh(name, prims):
    P = []
    for k, (v, n, c, f) in prims.items():
        P.append(dict(attributes=dict(POSITION=G.acc(v, "VEC3", 34962, True), NORMAL=G.acc(n, "VEC3", 34962), COLOR_0=G.acc(c, "VEC3", 34962)),
                      indices=G.acc(f.reshape(-1), "SCALAR", 34963), material=MI[k]))
    g["meshes"].append(dict(name=name, primitives=P)); return len(g["meshes"]) - 1
g["nodes"].append(dict(name="truck_game", children=[], extras=dict(units="mm", axes="+X elore, +Y fel, +Z jobbra")))
def add_node(nd, parent=0):
    g["nodes"].append(nd); i = len(g["nodes"]) - 1; g["nodes"][parent].setdefault("children", []).append(i); return i

meta = dict(version=1, units="mm", axes="+X előre, +Y fel, +Z jobbra (glTF)", source="tools/build_game_glb.py (TT_GEOM r2_geometry.json, %d elem)" % NE,
            grids={f: dict(axes=[a for a, _ in GRID[f]["ax"]], values=[[round(float(x), 5) for x in v] for _, v in GRID[f]["ax"]]) for f in GRID},
            S_MAX=S_MAX, ratios={"1": 5.44, "2": 3.27, "3": 1.81}, travel=dict(front=[-16, 16], rear_heave=[-9, 9], rear_roll_deg=[-11, 11]),
            nodes=[], wheels={})
tri = 0; nodes_moving = 0
for key, js in clusters.items():
    fam = key[0]
    if fam == "STATIC":
        pr = bake(js); tri += sum(len(p[3]) for p in pr.values())
        add_node(dict(name="STATIC", mesh=add_mesh("m_static", pr), extras=dict(count=len(js))))
        meta["static_count"] = len(js); continue
    if fam == "WHEEL":
        w = key[1]; famw = "REAR" if w[0] == "R" else w
        c0 = C_GL @ WC[w]
        pr = bake(js, origin=c0); tri += sum(len(p[3]) for p in pr.values())
        R = rel_series(famw, names.index(WHEELS[w]))
        samp = []
        for Rk in R:                                   # pivot = Rel · T(c0)
            Tk = Rk.copy(); Tk[:3, 3] = Rk[:3, :3] @ WC[w] + Rk[:3, 3]
            Rg = C_GL @ Tk[:3, :3] @ C_GL.T; tg = C_GL @ Tk[:3, 3]; q = B.quat(Rg)
            samp.append([round(float(x), 4) for x in tg] + [round(float(x), 6) for x in q])
        pv = add_node(dict(name="W_" + w, translation=c0.tolist(), extras=dict(count=len(js))))
        add_node(dict(name="W_" + w + "_spin", mesh=add_mesh("m_wheel_" + w, pr)), pv)
        # kerék-kormányszög (h=0 sor) a fizikához: yaw [fok] az s függvényében, + = balra
        yaw = None
        if famw in ("FL", "FR"):
            ih = list(GRID[famw]["ax"][0][1]).index(0.0); ns = len(GRID[famw]["ax"][1][1])
            yaw = [round(math.degrees(math.atan2(R[ih * ns + k][1, 0], R[ih * ns + k][0, 0])), 3) for k in range(ns)]
        rad = float(np.max(np.linalg.norm((MS["V_44771"] @ np.eye(3))[:, [0, 1]] if False else 0, axis=-1))) if False else 34.4
        meta["wheels"][w] = dict(node="W_" + w, family=famw, center=[round(float(x), 3) for x in c0], radius=rad,
                                 spin_axis=[0, 0, -1], samples=samp, yaw_vs_s=yaw, count=len(js))
        nodes_moving += 1; continue
    R = CR[key]
    pr = bake(js); tri += sum(len(p[3]) for p in pr.values())
    nm = f"{fam}_{key[1]}"
    add_node(dict(name=nm, mesh=add_mesh("m_" + nm, pr), extras=dict(count=len(js))))
    samp = []
    for Rk in R:
        tg, q = rel_trs(Rk); samp.append([round(float(x), 4) for x in tg] + [round(float(x), 6) for x in q])
    meta["nodes"].append(dict(node=nm, family=fam, count=len(js), parts=sorted(set(parts[j] for j in js)), samples=samp))
    nodes_moving += 1
# méretek a fizikához
allv = np.concatenate([(C_GL @ REST[j][:3, 3]) [None] for j in range(NE)])
bb = [np.inf] * 3, [-np.inf] * 3
lo = np.full(3, np.inf); hi = np.full(3, -np.inf)
for j in range(NE):
    V, _, _ = geom(parts[j]); T = REST[j]; v = (C_GL @ (V @ T[:3, :3].T + T[:3, 3]).T).T
    lo = np.minimum(lo, v.min(0)); hi = np.maximum(hi, v.max(0))
meta["bbox"] = dict(min=[round(float(x), 2) for x in lo], max=[round(float(x), 2) for x in hi])
fc = collections.Counter(FAM); meta["families"] = dict(fc)
raw = os.path.join(SITE, "_check", "truck_game_raw.glb"); os.makedirs(os.path.dirname(raw), exist_ok=True); G.write(raw)
print(f"elemek {NE}: {dict(fc)}; csomópont (mozgó) {nodes_moving}; háló {len(g['meshes'])}; primitív {sum(len(m['primitives']) for m in g['meshes'])}; háromszög {tri}")
for k, js in clusters.items():
    if k[0] != "STATIC": print("  ", k[0], k[1], len(js), sorted(set(parts[j] for j in js))[:6])
print("bbox", meta["bbox"])
out = os.path.join(OUT, "truck_game.glb")
si = os.environ.get("GAME_SI", "0.3")
cmd = [GLTFPACK, "-i", raw, "-o", out, "-cc", "-kn", "-km", "-ke", "-si", si, "-vp", "14", "-vc", "8"]
print(" ".join(cmd)); subprocess.run(cmd, check=True)
print(f"játék-GLB: {os.path.getsize(out) / 1e6:.2f} MB (nyers {os.path.getsize(raw) / 1e6:.1f} MB)")
json.dump(meta, open(os.path.join(OUT, "truck_game.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("truck_game.json:", os.path.getsize(os.path.join(OUT, "truck_game.json")) // 1024, "kB")
