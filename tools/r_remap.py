"""R-bemenet a build_anim_glb.py-hoz: a régi (previs_v3) jelenet kinematikáját átülteti az R rögzítés-javított elemlistára
(/home/claude/work/pyA/R_rogzites/r_geometry.json). Semmi kinematika nincs újraszámolva:
  - eredeti elem: a régi képkocka-transzformáció változatlanul;
  - javított elem: T(t) = F_régi(t) · REST_régi⁻¹ · P_új (a régi önmaga a gazda);
  - új elem: gazda = a rögzítési gráf (after.pkl) szerinti kapcsolt régi elem (kereszt-kötés elsőbbséggel, egyébként álló elem),
    T(t) = F_gazda(t) · REST_gazda⁻¹ · P_új  → pl. a tengelyen ülő persely a tengellyel forog, a vázcsap a vázzal áll.
"""
import json, pickle, os, numpy as np
RDIR = "/home/claude/work/pyA/R_rogzites"
# 11-05 R2: a geometria a TT_GEOM-ból (r2_geometry.json), a gráf a hozzá tartozó after-pickle-ből (r2/after2.pkl)
GEOM = os.environ.get("TT_GEOM") or (RDIR + "/r_geometry.json")
PKL = os.environ.get("TT_PKL") or (RDIR + "/r2/after2.pkl" if os.path.basename(GEOM).startswith("r2_") else RDIR + "/after.pkl")
def P(e):
    T = np.eye(4); T[:3, :3] = np.array(e["orientacio"], float); T[:3, 3] = e["pozicio"]; return T
HOST_OVERRIDE = {"R2_pinion_csapagy2_6632": "a2_pinion_csapagy_6632"}
def setup(E, names, parts, grps, kinds, ag, moving, st_rest):
    G = json.load(open(GEOM))["elemek"]
    PK = pickle.load(open(PKL, "rb")); EG = PK["E"]; edges = PK["R"]["edges"]
    assert [e["nev"] for e in EG] == [e["nev"] for e in G], "after.pkl és r_geometry sorrend eltér"
    oi = {n: j for j, n in enumerate(names)}
    def old_idx(e):
        n = e["nev"]
        return oi.get("B_" + n, oi.get(n)) if e["reszegyseg"].startswith("13") else oi.get(n)
    REST0 = E.kin(st_rest)
    host = {}; hostT = {}
    for i, e in enumerate(G):
        j = old_idx(e)
        if j is not None: host[i] = j
    # R2: a pinion 2. csapágya (6632 gerenda) a gráfban a pinion-tengelyhez (kerek furat) kapcsolódik, de NEM forog vele:
    # a gazdája az 1. csapágy (a hídházzal mozog)
    nix = {e["nev"]: i for i, e in enumerate(G)}
    for a, b in HOST_OVERRIDE.items():
        if a in nix and b in oi: host[nix[a]] = oi[b]
    adj = {}
    for ed in edges: adj.setdefault(ed["a"], []).append((ed["b"], ed["typ"])); adj.setdefault(ed["b"], []).append((ed["a"], ed["typ"]))
    # új elemek: BFS a gráfon a régi elemekig
    for _ in range(6):
        for i, e in enumerate(G):
            if i in host: continue
            nb = [(b, t) for b, t in adj.get(i, []) if b in host]
            if not nb: continue
            kr = [b for b, t in nb if t == "kereszt"]
            st = [b for b, t in nb if not moving[host[b]]]
            host[i] = host[(kr or st or [b for b, _ in nb])[0]]
    for i, e in enumerate(G):   # tartalék: legközelebbi álló régi elem
        if i in host: continue
        p = np.array(e["pozicio"]); d = [(np.linalg.norm(REST0[j][:3, 3] - p) if not moving[j] else 1e9) for j in range(len(names))]
        host[i] = int(np.argmin(d)); print("  R: kapcsolat nélkül, legközelebbi álló gazda:", e["nev"], "->", names[host[i]])
    N = []; Pp = []; Gr = []; K = []; A = []; Mv = []; Hj = []; OFF = []
    for i, e in enumerate(G):
        j = host[i]; burk = e["reszegyseg"].startswith("13"); same = old_idx(e) == j
        nm = ("B_" + e["nev"]) if burk else e["nev"]
        if same and e["forras"] == "eredeti": off = None
        else: off = np.linalg.inv(REST0[j]) @ P(e)
        if same: k = kinds[j]
        else: k = "frame" if e["partno"] in ("32526", "32291", "6536", "50451") else "csap"
        if same and e["forras"] == "javított" and e["partno"] in ("32526",): k = "tarto"
        N.append(nm); Pp.append(e["partno"]); Gr.append("burkolat" if burk else grps[j]); K.append(k); A.append("burkolat" if burk else ag[j])
        Mv.append(moving[j]); Hj.append(j); OFF.append(off)
    Hj = np.array(Hj)
    kin_old = E.kin
    def kin(st):
        F = kin_old(st); out = F[Hj].copy()
        for i, off in enumerate(OFF):
            if off is not None: out[i] = F[Hj[i]] @ off
        return out
    E.kin = kin
    rep = dict(n=len(G), uj_mozgo=[(N[i], names[Hj[i]]) for i, e in enumerate(G) if e["forras"] == "új" and moving[Hj[i]]],
               uj_gazda={N[i]: names[Hj[i]] for i, e in enumerate(G) if e["forras"] == "új"})
    return N, Pp, Gr, K, A, np.array(Mv), {(("B_" + e["nev"]) if e["reszegyseg"].startswith("13") else e["nev"]): e for e in G}, rep
