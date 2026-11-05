"""CV-adapter a build_anim_glb.py-hoz (11-05, felhasználói hibajelzés: az első agyban lévő CV-csukló rugózáskor és
kormányzáskor nem követi a kereket / elválik a féltengelytől).

Ok: az a6d_anim.front_corner a 32494 CV-gömböt (a 2L féltengely külső végét fogadó 12 mm-es furattal) a kerékhordozóval
MEREVEN mozgatja (A1 Mhub: lokális +z = kerék-tengely befelé), pedig a gömb a féltengelyen ül: a gömb középpontja a
92909 kehelyben van (a kerékhordozóval mozog), a csonkja viszont a féltengely irányába (külső csukló C -> belső kardán J)
mutat. Rugózáskor (±14 mm) és kormányzáskor a kerék-tengely és a féltengely közti szög ~15–31°, ezért a csonk
„kiállt" a féltengely vonalából.

Javítás (a kinematika forrását, az a6d_anim.py-t nem írjuk át – a videó-lánc változatlan):
  - 32494: középpont = a kerékhordozóval mozgó C (változatlan), a lokális +z tengelyt a legkisebb elforgatással a
    (J - C) irányba fordítjuk; a kerék-forgás (th) fázisa megmarad (homokinetikus csukló: a féltengely és a kerék
    azonos szögsebességgel forog);
  - 2L féltengely (feltengely_2L_±1): az A6b döntése szerinti hossz-helyzet (J + 8 + HS_SHIFT) a J -> C egyenesen,
    ezt az a6d_anim már így számolja (ellenőrzés: tengely·u = 1.0000) – nem módosítjuk;
  - 92909 kehely, felni, gumi: a kerékkel forognak (változatlan).
A javítást az E.kin köré tesszük, MIELŐTT az R-remap (r_remap.setup) becsomagolja, így a gömbhöz kötött új R-elemek is
a javított pózt kapják.
"""
import numpy as np


def _rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); s = np.linalg.norm(v); c = float(a @ b)
    if s < 1e-12: return np.eye(3)
    k = v / s; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    ang = np.arctan2(s, c)
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def install(E, names, J_L):
    idx = {}
    for sd, tag in ((1, "B"), (-1, "J")):
        n = f"cv_32494_{tag}"
        if n in names: idx[sd] = names.index(n)
    J = {sd: np.asarray(J_L, float) * np.array([1.0, sd, 1.0]) for sd in idx}
    kin_old = E.kin

    def kin(st):
        F = kin_old(st)
        for sd, j in idx.items():
            T = F[j]; C = T[:3, 3]
            z = T[:3, 2]                                   # csonk-irány (befelé, a kerék-tengely mentén)
            d = J[sd] - C                                  # féltengely-irány a külső csuklótól a belső kardánig
            R = _rot_between(z, d)
            T2 = T.copy(); T2[:3, :3] = R @ T[:3, :3]
            F[j] = T2
        return F

    E.kin = kin
    return dict(cv=list(idx.values()))
