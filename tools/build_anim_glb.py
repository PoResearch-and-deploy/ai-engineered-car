#!/usr/bin/env python3
"""MOZGÓ 3D-MODELL a weboldalra: a teljes autó (A6d 443 elem + A7 V2 burkolat 42 elem, pótkerék állítva a plató végén)
animált glTF-ként, a previs_v3 kinematikájával (export_frames.kin() -> a6d_anim.full_scene(); semmi sincs újraszámolva).

  python3 tools/build_anim_glb.py            # -> assets/model/truck.glb (+ parts.json), meshopt-tömörítéssel (gltfpack)
  python3 tools/build_anim_glb.py --raw      # csak a tömörítetlen _check/truck_raw.glb

Konvenció (12_weboldal.md): +X előre, +Y fel, +Z jobbra; gyökér `truck` scale 0.001 (alatta mm);
csoportok G_<id> (extras.group); alkatrészek P_<cikkszám>_<nn> (extras: group, partno, name, design_id, sub, explode [mm, glTF-tengelyek]).
Anyag részegységenként (`<csoport>_<fajta>`), a burkolat külön anyagokkal (`karosszeria_*`).
Klipek (hurok): gurulas, rugozas, kormanyzas, valtas, robbantas – lásd CLIPS lent.

Megjegyzés: a glTF-et közvetlenül írjuk (numpy), nem a Blender-exporterrel: így minden LDraw-háló egyszer van tárolva
(példányosítva), és a klipek pontosan a kinematika mintavételei (képkockánként TRS). A tömörítést a gltfpack végzi
(EXT_meshopt_compression + KHR_mesh_quantization), a nézegető a MeshoptDecodert használja (assets/vendor/three/addons/libs).
"""
import os, sys, json, math, struct, argparse, subprocess, collections
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__)); SITE = os.path.dirname(HERE)
PREVIS = "/home/claude/work/video/previs_v3"
ap = argparse.ArgumentParser(); ap.add_argument("--raw", action="store_true"); ap.add_argument("--fps", type=float, default=24.0)
ap.add_argument("--gltfpack", default="/tmp/claude-0/-home-claude/745ae32e-558c-5453-92a9-05a4066db304/scratchpad/npm/node_modules/.bin/gltfpack")
ARGS = ap.parse_args()
sys.argv = [sys.argv[0]]
sys.path.insert(0, PREVIS)
import export_frames as E                      # betölti az A6d-t (M.setup()), a V2 burkolatot és a pótkerék-pózt
from common import smooth
M, A4, B3 = E.M, E.A4, E.B3
FPS = ARGS.fps
names, parts, grps, kinds, ag, _moving = E.scene_meta()
NE = len(names)
GEO = {e["nev"]: e for e in json.load(open("/home/claude/work/pyA/A6d_integracio/a6d_geometry.json"))["elemek"]}
BODYJ = {"B_" + e["nev"]: e for e in json.load(open("/home/claude/work/pyA/A7_burkolat/a7_geometry_V2.json"))["burkolat"]}
LDN = {}
for e in list(GEO.values()) + list(BODYJ.values()): LDN.setdefault(e["partno"], e.get("ldraw_nev", ""))

# ------------------------------------------------------------------ csoportok
GROUPS = [  # id, hu, en, chip-szín
    ("vaz", "Váz és tartók", "Frame & brackets", "#5b6470"),
    ("elso_futomu", "Első futómű", "Front suspension", "#9aa3ad"),
    ("kormany", "Kormány", "Steering", "#a78bfa"),
    ("hatso_hid", "Hátsó híd, 4-link", "Rear axle, 4-link", "#c7a17a"),
    ("hajtaslanc", "Hajtáslánc, osztómű", "Driveline, transfer", "#F28C28"),
    ("valto", "Váltó + váltóház", "Gearbox + housing", "#4fb286"),
    ("V8", "V8", "V8", "#b8c2cc"),
    ("kerekek", "Kerekek", "Wheels", "#3a3b40"),
    ("karosszeria", "Burkolat", "Body", "#c8202a"),
]
def site_group(j):
    n, g = names[j], grps[j]
    if g == "burkolat": return "karosszeria"
    if g in ("kerek", "felni"): return "kerekek"
    sub = GEO.get(n, {}).get("reszegyseg", "")
    code = sub[:2]
    if code in ("01", "02", "03", "04"): return "vaz"
    if code == "05" or code == "11": return "valto"
    if code == "06": return "elso_futomu"
    if code == "07": return "kormany"
    if code in ("08", "09"): return "hajtaslanc"
    if code == "10": return "hatso_hid"
    if code == "12": return "V8"
    return {"vaz": "vaz", "uj6": "vaz", "futomu": "elso_futomu", "kormany": "kormany", "a1c": "hajtaslanc", "a3": "hajtaslanc",
            "a2": "hatso_hid", "valto": "valto", "v8": "V8"}.get(g, "vaz")
SG = [site_group(j) for j in range(NE)]

COL = json.load(open(os.path.join(PREVIS, "params.json")))["colors"]
PBR = {"tyre": (0.92, 0.0), "rim": (0.32, 0.55), "v8": (0.35, 0.6), "drive": (0.42, 0.15), "panel": (0.32, 0.0), "panel2": (0.35, 0.0),
       "frame": (0.55, 0.1), "susp": (0.55, 0.1), "steer": (0.5, 0.1), "other": (0.55, 0.1), "tarto": (0.55, 0.1), "csap": (0.5, 0.2)}

# ------------------------------------------------------------------ kinematika
C_GL = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.0]])          # jármű (x előre, y balra, z fel) -> glTF (x előre, y fel, z jobbra)
k_s, k_v = B3.stub_ratio()
DR = A4.DR

def st_full(th=0.0, hL=0.0, hR=0.0, s=0.0, kd=0.0, h_r=0.0, roll=0.0, gear=1, kpos=None, cA=None, cB=None, C=None):
    k = {1: 0, 2: 1, 3: 2, 0: 3}[gear] if kpos is None else kpos
    pf = -B3.RATIO * th; psi_v = k_v * k_s * pf
    return dict(hL=hL, hR=hR, s=s, thF=th, thR=th, kd=kd, h_r=h_r, roll=roll, rd=0.0, gear=gear,
                cA=DR["cA"][gear] if cA is None else cA, cB=DR["cB"][gear] if cB is None else cB,
                thA=DR["thA0"] + math.radians(90 * k), thB=DR["thB0"] - math.radians(90 * k),
                C=A4.RATIOS.get(gear, 0.0) * psi_v if C is None else C)

REST = E.kin(st_full())                                           # nyugalmi póz: 1. fokozat, minden 0
W_REV = 2 * math.pi * E.SPIN                                      # +1 kerékfordulat előre

def clip_gurulas():
    """2. fokozat, a jármű helyben gurul; 15 kerékfordulat = 49 főtengely-fordulat (49/15 = 5.444·0.6) -> pontos hurok"""
    n_rev, sec_per_rev = 15, 1.2
    nf = int(round(n_rev * sec_per_rev * FPS))
    return [E.kin(st_full(th=W_REV * n_rev * i / nf, gear=2)) for i in range(nf + 1)]

def clip_rugozas():
    """0–2 s: első+hátsó együtt be/ki; 2–6 s: keresztbe csuklás (első ellentétes, hátsó híd billen)"""
    T = 6.0; nf = int(T * FPS); out = []
    for i in range(nf + 1):
        t = i / FPS
        if t < 2.0:
            a = math.sin(2 * math.pi * t / 2.0); hL = hR = 14.0 * a; h_r = 6.0 * a; roll = 0.0
        else:
            a = math.sin(2 * math.pi * (t - 2.0) / 4.0); hL, hR = 14.0 * a, -14.0 * a; h_r = 0.0; roll = -9.0 * a
        out.append(E.kin(st_full(hL=hL, hR=hR, h_r=h_r, roll=roll)))
    return out

def clip_kormanyzas():
    T = 4.0; nf = int(T * FPS)
    return [E.kin(st_full(s=M.S_MAX * math.sin(2 * math.pi * i / nf))) for i in range(nf + 1)]

def valtas_sim(n1, n2, n3, nN, ns, wps):
    """1 -> 2 -> 3 -> N -> 1 (a tetőgomb 4×90° = 360° -> hurok); a gyűrűk a választók peremén (hiszterézissel, mint a seq2-ben),
    a főtengely a kapcsolt fokozat áttételével integrálódik (N-ben áll)."""
    plan = [("d", n1), ("s", ns), ("d", n2), ("s", ns), ("d", n3), ("s", ns), ("d", nN), ("s", ns)]
    seq = []; kk = 0
    for kind, n in plan:
        for i in range(n):
            seq.append(kk + (float(smooth((i + 1) / n)) if kind == "s" else 0.0))
        if kind == "s": kk += 1
    prev = {"SA": DR["cA"][1], "SB": DR["cB"][1]}; C = 0.0; psi_prev = 0.0; out = []
    nf = len(seq)
    for i in range(nf + 1):
        k = 0.0 if i == 0 else seq[i - 1]
        th = W_REV * wps * i / FPS
        thA = DR["thA0"] + math.radians(90 * k); thB = DR["thB0"] - math.radians(90 * k)
        rp = A4.ring_positions(thA, thB, False, False, prev); prev = {s_: rp[s_][0] for s_ in rp}
        g = M.engaged(prev["SA"], prev["SB"])
        psi_v = k_v * k_s * (-B3.RATIO * th)
        C += A4.RATIOS.get(g, 0.0) * (psi_v - psi_prev); psi_prev = psi_v
        out.append(dict(th=th, k=k, cA=prev["SA"], cB=prev["SB"], g=g, C=C))
    return out

def clip_valtas():
    wps, ns = 0.5, int(0.6 * FPS)                       # 0.5 kerékfordulat/s; váltás 0.6 s
    per_rev = int(round(FPS / wps))
    best = None
    for n1 in range(int(1.6 * FPS), int(2.4 * FPS)):
        base = n1 + int(2.0 * FPS) + int(2.0 * FPS) + 4 * ns
        for nN in range(int(1.2 * FPS), int(2.6 * FPS)):
            if (base + nN) % per_rev: continue
            S = valtas_sim(n1, int(2.0 * FPS), int(2.0 * FPS), nN, ns, wps)
            r = abs(math.remainder(S[-1]["C"], 2 * math.pi))
            if best is None or r < best[0]: best = (r, n1, nN, S)
            break
    r, n1, nN, S = best
    print(f"  valtas: n1={n1} nN={nN} kocka={len(S) - 1} főtengely-maradék {math.degrees(r):.1f}° (korrekció az 1. fokozat szakaszára)")
    # a maradékot az 1. fokozatú szakasz főtengely-szögére osztjuk szét (≤ néhány %), hogy a hurok pontosan záródjon
    Ct = S[-1]["C"]; res = math.remainder(Ct, 2 * math.pi)
    i1 = n1; C1 = S[i1]["C"]
    corr = [(-res * min(1.0, i / i1)) if i <= i1 else -res for i in range(len(S))]
    print(f"  valtas: 1. fokozat sebesség-korrekció {100 * (-res) / C1:+.1f} %")
    frames = [E.kin(st_full(th=f["th"], gear=f["g"], kpos=f["k"], cA=f["cA"], cB=f["cB"], C=f["C"] + c)) for f, c in zip(S, corr)]
    marks = []; prevg = None
    for i, f in enumerate(S):
        if f["g"] != prevg: marks.append(dict(t=round(i / FPS, 3), gear=f["g"])); prevg = f["g"]
    return frames, marks

def explode_vectors():
    """a previs E_robbantas vektorai (részegység-eltolás + szétterítés a súlyponttól), jármű-KR, mm"""
    RB = E.PRM["robbantas"]; P0 = REST[:, :3, 3]; ex = np.zeros((NE, 3))
    for gname in set(ag):
        idx = [j for j in range(NE) if ag[j] == gname]
        cg = P0[idx].mean(0); v = np.array(RB["vektor"].get(gname, [0, 0, 0]), float)
        f = RB["szetterites_vaz"] if gname == "vaz" else RB["szetterites"]
        for j in idx: ex[j] = v + (P0[j] - cg) * f
    for j in range(NE):
        if kinds[j] in ("tyre", "rim") and grps[j] != "burkolat":
            sy = 1.0 if P0[j, 1] > 0 else -1.0
            ex[j] = np.array(RB["vektor"]["kerek"]) * sy + (np.array([90, 0, 0]) if P0[j, 0] > 100 else np.array([-90, 0, 0]))
            if kinds[j] == "rim": ex[j][1] += 45 * sy
    return ex
EX = explode_vectors()

def clip_robbantas():
    T = 6.0; nf = int(T * 12); out = []                 # csak eltolás -> 12 Hz is sima (lineáris interpoláció)
    for i in range(nf + 1):
        t = i / 12
        e = float(smooth(t / 1.8)) if t < 3.0 else float(smooth((6.0 - t) / 1.8))
        Tm = REST.copy(); Tm[:, :3, 3] += EX * e; out.append(Tm)
    return out, 12.0

# ------------------------------------------------------------------ TRS
def trs(Mx):
    R = C_GL @ Mx[:3, :3]; t = C_GL @ Mx[:3, 3]
    s = np.linalg.norm(R, axis=0); Rn = R / s
    if np.linalg.det(Rn) < 0: s[0] = -s[0]; Rn[:, 0] = -Rn[:, 0]
    q = quat(Rn)
    return t, q, s

def quat(R):
    tr_ = R[0, 0] + R[1, 1] + R[2, 2]
    if tr_ > 0:
        S = math.sqrt(tr_ + 1.0) * 2; w = 0.25 * S; x = (R[2, 1] - R[1, 2]) / S; y = (R[0, 2] - R[2, 0]) / S; z = (R[1, 0] - R[0, 1]) / S
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        S = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2; w = (R[2, 1] - R[1, 2]) / S; x = 0.25 * S; y = (R[0, 1] + R[1, 0]) / S; z = (R[0, 2] + R[2, 0]) / S
    elif R[1, 1] > R[2, 2]:
        S = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2; w = (R[0, 2] - R[2, 0]) / S; x = (R[0, 1] + R[1, 0]) / S; y = 0.25 * S; z = (R[1, 2] + R[2, 1]) / S
    else:
        S = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2; w = (R[1, 0] - R[0, 1]) / S; x = (R[0, 2] + R[2, 0]) / S; y = (R[1, 2] + R[2, 1]) / S; z = 0.25 * S
    q = np.array([x, y, z, w]); return q / np.linalg.norm(q)

# ------------------------------------------------------------------ glTF-író
class GLB:
    def __init__(self):
        self.bin = bytearray(); self.g = dict(asset=dict(version="2.0", generator="ai-engineered-car build_anim_glb.py"),
                                              scene=0, scenes=[dict(name="truck", nodes=[0])], nodes=[], meshes=[], materials=[],
                                              accessors=[], bufferViews=[], buffers=[], animations=[])
    def view(self, data, target=None):
        while len(self.bin) % 4: self.bin.append(0)
        off = len(self.bin); self.bin += data
        bv = dict(buffer=0, byteOffset=off, byteLength=len(data))
        if target: bv["target"] = target
        self.g["bufferViews"].append(bv); return len(self.g["bufferViews"]) - 1
    def acc(self, arr, typ, target=None, minmax=False):
        arr = np.ascontiguousarray(arr)
        ct = {np.dtype("float32"): 5126, np.dtype("uint32"): 5125, np.dtype("uint16"): 5123}[arr.dtype]
        a = dict(bufferView=self.view(arr.tobytes(), target), componentType=ct, count=int(arr.shape[0]), type=typ)
        if minmax:
            a["min"] = [float(v) for v in arr.reshape(arr.shape[0], -1).min(0)]; a["max"] = [float(v) for v in arr.reshape(arr.shape[0], -1).max(0)]
        self.g["accessors"].append(a); return len(self.g["accessors"]) - 1
    def write(self, path):
        while len(self.bin) % 4: self.bin.append(0)
        self.g["buffers"] = [dict(byteLength=len(self.bin))]
        js = json.dumps(self.g, separators=(",", ":"), ensure_ascii=False).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
            f.write(struct.pack("<II", len(self.bin), 0x004E4942)); f.write(self.bin)

def lin(hexc):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return [f(int(hexc[i:i + 2], 16) / 255) for i in (1, 3, 5)]

def build():
    G = GLB(); g = G.g
    MS = np.load(os.path.join(PREVIS, "cache/meshes.npz"))
    # anyagok: <csoport>_<fajta>
    mats = {}
    def mat(gid, kind):
        key = f"{gid}_{kind}"
        if key not in mats:
            r, m = PBR.get(kind, (0.55, 0.1))
            md = dict(name=key, doubleSided=True, pbrMetallicRoughness=dict(baseColorFactor=lin(COL[kind]) + [1.0], metallicFactor=m, roughnessFactor=r),
                      extras=dict(group=gid, kind=kind, body=gid == "karosszeria"))
            g["materials"].append(md); mats[key] = len(g["materials"]) - 1
        return mats[key]
    # hálók: alkatrészenként egyszer (simított normálok 30° élszöggel), anyagonként primitive
    geo = {}
    def geom(p):
        if p not in geo:
            tm = trimesh.Trimesh(vertices=MS["V_" + p].astype(np.float64), faces=MS["F_" + p], process=False)
            sm = trimesh.graph.smooth_shade(tm, angle=math.radians(32))
            V = np.asarray(sm.vertices, np.float32); N = np.asarray(sm.vertex_normals, np.float32); F = np.asarray(sm.faces)
            idx = F.astype(np.uint16 if len(V) < 65535 else np.uint32).reshape(-1)
            geo[p] = (G.acc(V, "VEC3", 34962, True), G.acc(N, "VEC3", 34962), G.acc(idx, "SCALAR", 34963), len(F))
        return geo[p]
    meshes = {}
    def mesh(p, mi):
        if (p, mi) not in meshes:
            a_p, a_n, a_i, nf = geom(p)
            g["meshes"].append(dict(name=f"m_{p}_{g['materials'][mi]['name']}", primitives=[dict(attributes=dict(POSITION=a_p, NORMAL=a_n), indices=a_i, material=mi)]))
            meshes[(p, mi)] = len(g["meshes"]) - 1
        return meshes[(p, mi)]
    # csomópontok
    g["nodes"].append(dict(name="truck", scale=[0.001] * 3, children=[], extras=dict(units="mm", axes="+X elore, +Y fel, +Z jobbra")))
    gnode = {}
    for gid, hu, en, c in GROUPS:
        g["nodes"].append(dict(name="G_" + gid, children=[], extras=dict(group=gid))); gnode[gid] = len(g["nodes"]) - 1
        g["nodes"][0]["children"].append(gnode[gid])
    cnt = collections.Counter(); pnode = []; pinfo = {}
    for j in range(NE):
        p = parts[j]; cnt[p] += 1; nm = f"P_{p}_{cnt[p]:02d}"
        gid = SG[j]; t, q, s = trs(REST[j])
        src = GEO.get(names[j]) or BODYJ.get(names[j]) or {}
        ex = dict(group=gid, partno=p, name=src.get("ldraw_nev") or LDN.get(p, p), design_id=p, element=names[j],
                  sub=src.get("reszegyseg", "Burkolat (A7 V2)" if gid == "karosszeria" else ""),
                  explode=[round(float(v), 2) for v in C_GL @ EX[j]])
        nd = dict(name=nm, mesh=mesh(p, mat(gid, kinds[j])), translation=t.tolist(), rotation=q.tolist(), extras=ex)
        if np.abs(s - 1).max() > 1e-6: nd["scale"] = s.tolist()
        g["nodes"].append(nd); ni = len(g["nodes"]) - 1; pnode.append(ni); g["nodes"][gnode[gid]]["children"].append(ni)
        pinfo[nm] = {k: ex[k] for k in ("group", "partno", "name", "element", "sub")}
    # animációk
    rest_trs = [trs(REST[j]) for j in range(NE)]
    def add_clip(name, frames, fps):
        F = np.array(frames); nfr = len(F)
        times = (np.arange(nfr) / fps).astype(np.float32)
        a_t = G.acc(times, "SCALAR", None, True)
        samplers, channels = [], []; nmov = 0; maxstep = 0.0
        for j in range(NE):
            Tj = F[:, j]
            if np.abs(Tj - REST[j][None]).max() < 1e-4: continue
            nmov += 1
            TR = [trs(Tj[i]) for i in range(nfr)]
            tt = np.array([x[0] for x in TR], np.float32); qq = np.array([x[1] for x in TR]); ss = np.array([x[2] for x in TR], np.float32)
            for i in range(1, nfr):
                if qq[i] @ qq[i - 1] < 0: qq[i] = -qq[i]
            if nfr > 1: maxstep = max(maxstep, float(np.degrees(2 * np.arccos(np.clip(np.abs((qq[1:] * qq[:-1]).sum(1)), 0, 1))).max()))
            r_t, r_q, r_s = rest_trs[j]
            for path, arr, ref, typ in (("translation", tt, r_t, "VEC3"), ("rotation", qq.astype(np.float32), None, "VEC4"), ("scale", ss, r_s, "VEC3")):
                if path == "rotation":
                    if np.abs(np.abs(qq @ r_q) - 1).max() < 1e-7: continue
                elif np.abs(arr - ref[None]).max() < 1e-4: continue
                samplers.append(dict(input=a_t, output=G.acc(arr.astype(np.float32), typ), interpolation="LINEAR"))
                channels.append(dict(sampler=len(samplers) - 1, target=dict(node=pnode[j], path=path)))
        g["animations"].append(dict(name=name, samplers=samplers, channels=channels))
        print(f"  {name}: {nfr} kocka, {(nfr - 1) / fps:.2f} s, {nmov} mozgó elem, {len(channels)} csatorna, max. elfordulás/kocka {maxstep:.0f}°", flush=True)
        return (nfr - 1) / fps, nmov
    info = {}
    info["gurulas"] = add_clip("gurulas", clip_gurulas(), FPS)
    info["rugozas"] = add_clip("rugozas", clip_rugozas(), FPS)
    info["kormanyzas"] = add_clip("kormanyzas", clip_kormanyzas(), FPS)
    fr, marks = clip_valtas(); info["valtas"] = add_clip("valtas", fr, FPS)
    fr, f12 = clip_robbantas(); info["robbantas"] = add_clip("robbantas", fr, f12)
    return G, pinfo, info, marks

CLIP_META = [
    ("gurulas", "Gurulás (2. fokozat)", "Rolling (2nd gear)",
     "Kerekek, féltengelyek, diffek, kardánok, váltó és a V8 főtengely + dugattyúk, mind a saját áttételével (kerék → főtengely 1 : 3,27).",
     "Wheels, half-shafts, diffs, prop shafts, gearbox and the V8 crank + pistons, each at its own ratio (wheel → crank 1 : 3.27)."),
    ("rugozas", "Rugózás", "Suspension",
     "Első független futómű ±14 mm, majd keresztbe csuklás: a hátsó merev híd ±9°-ot billen a 4-linken.",
     "Independent front ±14 mm, then cross-axle articulation: the solid rear axle rolls ±9° on its 4-link."),
    ("kormanyzas", "Kormányzás", "Steering",
     "A tetőkormány az oszlopon és két kardánon át a pinion → léc láncot hajtja, a kerekek végállásig fordulnak.",
     "The roof wheel drives the pinion → rack through the column and two U-joints; the wheels steer lock to lock."),
    ("valtas", "Váltás 1 → 2 → 3 → N", "Shifting 1 → 2 → 3 → N",
     "A tetőgomb 90°-onként fordítja a választókat, azok tolják a kapcsológyűrűket – a dugattyúk sebessége fokozatonként változik, N-ben állnak.",
     "The roof knob turns the selector drums 90° per step, which slide the shift rings – piston speed changes with each gear and stops in N."),
    ("robbantas", "Robbantás", "Explode",
     "A részegységek szétválnak, majd visszaállnak (a previs robbantási vektoraival).",
     "Sub-assemblies fly apart and return (same explode vectors as the film previs)."),
]

if __name__ == "__main__":
    os.makedirs(os.path.join(SITE, "_check"), exist_ok=True)
    G, pinfo, info, marks = build()
    raw = os.path.join(SITE, "_check", "truck_raw.glb"); G.write(raw)
    print(f"nyers GLB: {os.path.getsize(raw) / 1e6:.2f} MB, {len(G.g['nodes'])} csomópont, {len(G.g['meshes'])} háló, {len(G.g['materials'])} anyag")
    if ARGS.raw: sys.exit(0)
    out = os.path.join(SITE, "assets/model/truck.glb")
    gp = [ARGS.gltfpack] if os.path.exists(ARGS.gltfpack) else ["npx", "-y", "gltfpack@0.25.0"]
    cmd = gp + ["-i", raw, "-o", out, "-cc", "-kn", "-km", "-ke", "-ac", "-af", str(int(FPS)), "-vp", "16"]
    print(" ".join(cmd)); subprocess.run(cmd, check=True)
    print(f"tömörített GLB: {os.path.getsize(out) / 1e6:.2f} MB")
    pj = dict(version=3, units="mm (gyökér-scale 0.001)", axes="+X előre, +Y fel, +Z jobbra", placeholder=False,
              source="A6d teljes jármű (443 elem, a6d_anim.full_scene kinematika) + A7 V2 burkolat (42 elem, pótkerék állítva) – LDraw-hálók; tools/build_anim_glb.py",
              compression="EXT_meshopt_compression + KHR_mesh_quantization (gltfpack)",
              animations=[dict(name=n, loop_s=round(info[n][0], 3), moving=info[n][1], hu=hu, en=en, desc_hu=dh, desc_en=de) for n, hu, en, dh, de in CLIP_META],
              gear_marks=marks, groups=[dict(id=a, hu=b, en=c, color=d, count=SG.count(a)) for a, b, c, d in GROUPS], parts=pinfo)
    json.dump(pj, open(os.path.join(SITE, "assets/model/parts.json"), "w"), ensure_ascii=False, indent=1)
    print("parts.json kész")
