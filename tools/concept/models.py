"""Koncepció-modellek (versenyautó, kamion, daru) valódi Technic-elemekből – gyors, NEM végigtervezett elrendezések.
Világ-KR: mm, X előre, Y balra, Z fel. Alkatrész-hálók: video/render_v3/cache/meshes.npz (LDraw-geometria, mm; LDraw 'fel' = -Y).
Kimenet: list[(partno, 4x4 mátrix, színkulcs)].
"""
import math
import numpy as np

X = np.array([1., 0, 0]); Y = np.array([0, 1., 0]); Z = np.array([0, 0, 1.])


def R(lx, ly, lz):
    m = np.column_stack([lx, ly, lz]).astype(float)
    assert abs(np.linalg.det(m) - 1) < 1e-6, ("det", np.linalg.det(m))
    return m


def rotY(a):  # dőlés: +X tengely felfelé fordul pozitív a-nál
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def rotZ(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# szabványos tájolások
BEAM_X = R(Y, Z, X)        # hossz X mentén, furatok Y irányban
BEAM_Y = R(X, -Z, Y)       # hossz Y mentén, furatok X irányban
BEAM_Z = R(Y, -X, Z)       # függőleges, furatok Y irányban
BEAM_XZ = R(Z, -Y, X)      # hossz X, furatok függőlegesek (lapos)
AX_Y = R(Y, Z, X)          # tengely (helyi X) Y irányban
AX_Z = R(Z, X, Y)          # függőleges tengely
AX_X = R(X, Y, Z)
WHL_L = R(X, Z, -Y)        # kerék, külső oldal +Y felé
WHL_R = R(X, -Z, Y)
PANEL_FLAT = R(X, -Z, Y)   # 88 X, 40 Y, vízszintes
PANEL_SIDE = R(X, -Z * -1, Z) if False else np.eye(3)  # X-Z síkban (88 X, 40 Z), normál Y
PANEL_FRONT = R(Y, -X, Z)  # Y-Z síkban (88 Y, 40 Z)
UP_LDR = None


class Model:
    def __init__(self):
        self.items = []

    def add(self, p, pos, rot=np.eye(3), col="dark"):
        T = np.eye(4); T[:3, :3] = rot; T[:3, 3] = pos
        self.items.append((p, T, col)); return self

    # kerék = gumi + felni
    def wheel(self, x, y, r=34.4, col_rim="rim"):
        rot = WHL_L if y > 0 else WHL_R
        self.add("44771", (x, y, r), rot, "tyre"); self.add("15038", (x, y, r), rot, col_rim)

    def beam_x(self, p, x, y, z, col="dark", pitch=0.0, holes=0, pin="2780", pin_col="pin"):
        rot = rotY(pitch) @ BEAM_X
        self.add(p, (x, y, z), rot, col)
        if holes:  # csapok néhány furatban (vizuális sűrűség)
            L = {"41239": 13, "32278": 15, "32525": 11, "40490": 9, "32524": 7, "32316": 5, "32523": 3}[p]
            d = rotY(pitch) @ X
            for k in range(0, L, holes):
                off = (k - (L - 1) / 2) * 8.0
                self.add(pin, np.array((x, y, z)) + d * off, rotY(pitch) @ R(Y, -X, Z) @ np.eye(3) if False else rotY(pitch) @ R(Y, Z, X) @ R(X, Y, Z), pin_col)
        return self


def mudguard(m, x, y, z, col):
    """69911 + 71689 ív a kerék fölött (hossz X, ív felfelé)."""
    rot = R(-Y, -Z, X) if y > 0 else R(Y, -Z, -X)
    m.add("69911", (x, y, z), rot, col); m.add("71689", (x, y, z), rot, col)


# ===================================================================== versenyautó
def race_car():
    m = Model(); B = "red"; W = "white"
    xf, xr, ty = 62.0, -62.0, 60.0
    for x in (xf, xr):
        for s in (1, -1):
            m.wheel(x, s * ty)
        m.add("3708", (x, 0, 34.4), AX_Y, "axle")
        for s in (1, -1):
            m.add("32123a", (x, s * 40, 34.4), R(Z, X, Y) if False else R(X, -Z, Y), "pin")
    # alváz: 4 db 13L + 2 db 15L hosszanti
    for s in (1, -1):
        m.beam_x("41239", 0, s * 28, 26, "dark", holes=2)
        m.beam_x("32278", 0, s * 12, 18, "dark", holes=3)
        m.add("41239", (0, s * 38, 30), BEAM_X, "dark")
    for x in (xf, xr, 30, -30):
        m.add("32524", (x, 0, 18 if abs(x) < 50 else 26), BEAM_Y, "dark")
    # padlólemez
    m.add("64782", (20, 0, 14), R(Y, -Z, -X) if False else R(-Y, Z * -1, X) if False else R(Y, Z, X), B) if False else None
    m.add("64782", (0, 0, 13), PANEL_FLAT, "dark")
    # sárvédők
    for x in (xf, xr):
        for s in (1, -1):
            mudguard(m, x, s * (ty - 2), 36, B)
    # oldaldobozok (sidepod) – íves panelek a kerekek között
    for s in (1, -1):
        m.add("18944", (0, s * 46, 40), R(-s * Y, -Z, X) if s > 0 else R(Y, -Z, -X), B)
        m.add("62531", (0, s * 34, 46), R(-s * Y, -Z, X) if s > 0 else R(Y, -Z, -X), W)
    # orr és motorháztető
    m.add("15458", (80, 0, 44), R(-Y, -Z, X) @ np.eye(3) if False else R(Y, X, -Z) if False else PANEL_FLAT @ rotZ(math.pi / 2).T @ rotZ(math.pi / 2) @ np.eye(3), B) if False else None
    m.add("64782", (82, 0, 40), R(Y, -Z, -X) if False else rotY(math.radians(-14)) @ R(Y, Z, X) @ R(X, Y, Z) if False else rotY(math.radians(-12)) @ R(Y, Z, X) @ np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1.]]), B) if False else None
    nose = rotY(math.radians(-14)) @ R(Y, Z, X)   # lx->Y (88 széles), ly->Z (vastagság), lz->X (40 mély)
    m.add("64782", (88, 0, 42), nose, B)
    m.add("64782", (40, 0, 50), R(Y, Z, X), W)
    # első terelő (splitter)
    m.add("15458", (106, 0, 22), R(Y, Z, X), "dark")
    # pilótafülke: bukókeret + kormány
    for s in (1, -1):
        m.add("32526", (-14, s * 20, 50), R(Y, -X, Z) @ np.eye(3), "dark")
    m.add("23801", (8, 0, 62), R(-Z, X, -Y) if False else R(Y, Z, X), "dark")
    m.add("15535", (-6, 0, 50), R(X, -Z, Y), "dark")
    # hátsó burkolat
    m.add("64782", (-50, 0, 52), rotY(math.radians(8)) @ R(Y, Z, X), B)
    # hátsó szárny: 2 függőleges tartó + lap + oldallapok
    for s in (1, -1):
        m.add("32524", (-96, s * 22, 62), BEAM_Z, "dark")
        m.add("2780", (-96, s * 22, 86), R(Y, -X, Z), "pin")
        m.add("41677", (-96, s * 46, 92), BEAM_Z, B)
    m.add("15458", (-98, 0, 92), R(Y, Z, X), W)
    m.add("32278", (-104, 0, 98), BEAM_Y, B)
    # diffúzor
    m.add("15458", (-98, 0, 20), rotY(math.radians(12)) @ R(Y, Z, X), "dark")
    # lengéscsillapítók (látható első)
    # kipufogók
    for s in (1, -1):
        m.add("3705", (-110, s * 10, 34), AX_X, "metal")
    return m


def rotX_vec(s):
    # 76537 hossza helyi +Y; állítsuk közel függőlegesre, kicsit befelé dőlve
    a = math.radians(25) * s
    c, si = math.cos(a), math.sin(a)
    Rx = np.array([[1, 0, 0], [0, c, -si], [0, si, c]])
    return Rx @ R(X, Z, -Y)


# ===================================================================== kamion (nyerges vontató)
def truck():
    m = Model(); C = "orange"
    xs = (62, -42, -116); ty = 46
    for x in xs:
        for s in (1, -1):
            m.wheel(x, s * ty)
        m.add("3706", (x, 0, 34.4), AX_Y, "axle")
    # alváz
    for s in (1, -1):
        m.beam_x("32278", -40, s * 22, 36, "dark", holes=2)
        m.beam_x("32524", 52, s * 22, 36, "dark", holes=2)
        m.beam_x("41239", -70, s * 22, 44, "dark")
    for x in (60, 0, -60, -110):
        m.add("32316", (x, 0, 28), BEAM_Y, "dark")
    # nyeregszerkezet
    m.add("64179", (-80, 0, 52), R(X, -Z, Y) @ np.eye(3), "dark")
    m.add("15535", (-80, 0, 56), R(X, -Z, Y), "metal")
    m.add("3648", (-80, 0, 50), R(X, Y, Z), "metal")
    # fülke: x 44..108, z 40..140
    xc0, xc1 = 44, 108
    for s in (1, -1):
        m.add("64782", (76, s * 44, 92), R(Z, -s * Y, X) if s > 0 else R(Z, Y * 1, -X) if False else R(Z, Y, -X) if False else side_rot(s), C)
        m.add("62531", (76, s * 46, 50), R(-Y, -Z, X) if s > 0 else R(Y, -Z, -X), "dark")
    # homlokfal: hűtőrács + szélvédőkeret
    m.add("64782", (110, 0, 64), R(Y, -X, Z), "dark")
    for s in (1, -1):
        m.add("64179", (108, s * 22, 112), R(Y, -X, Z), C)
    m.add("15458", (112, 0, 34), R(Y, -X, Z), C)   # lökhárító
    # tető + légterelő
    m.add("64782", (76, 0, 140), R(Y, Z, X), C)
    m.add("18944", (64, 0, 146), R(Y, -Z, -X) @ np.eye(3) if False else rotZ(math.pi / 2) @ R(X, -Z, Y) if False else roofdefl(), C)
    # hátfal
    m.add("64782", (42, 0, 92), R(Y, X, -Z) if False else R(Z, -X, -Y) if False else R(Y * -1, X, Z), "dark")
    # kipufogók
    for s in (1, -1):
        m.add("3708", (38, s * 40, 120), AX_Z, "metal")
        m.add("3713", (38, s * 40, 80), R(Y, Z, X) if False else R(X, Y, Z) @ np.eye(3) if False else R(Y, X, -Z), "metal")
    # sárvédők a tandem fölött
    for s in (1, -1):
        m.add("15458", (-79, s * ty, 76), R(X, -Z, Y), "dark")
        mudguard(m, 62, s * (ty - 2), 36, C)
        # üzemanyagtartály
        m.add("62821", (12, s * 36, 28), R(Y, X, -Z) if False else R(X, -Z, Y) if False else R(Z, X, Y) @ R(X, Y, Z) if False else R(-Z, Y, X) if False else tank_rot(), "metal")
    # lámpák
    for s in (1, -1):
        m.add("6628", (114, s * 36, 46), AX_X, "light")
    return m


def side_rot(s):
    # 64782: helyi X (88) -> Z (magasság), helyi Z (40) -> X (mélység), normál Y
    return R(Z, -Y, X) if s > 0 else R(Z, Y, -X)


def roofdefl():
    return R(X, -Z, Y)


def tank_rot():
    return R(Z, X, Y) @ np.eye(3) if False else np.array([[0, 0, 1.], [1, 0, 0], [0, 1, 0]])


# ===================================================================== daru
def crane():
    m = Model(); C = "yellow"
    xs = (96, 24, -60, -132); ty = 46
    for x in xs:
        for s in (1, -1):
            m.wheel(x, s * ty)
        m.add("3706", (x, 0, 34.4), AX_Y, "axle")
    for s in (1, -1):
        m.beam_x("32278", 40, s * 22, 36, "dark", holes=2)
        m.beam_x("32278", -80, s * 22, 36, "dark", holes=2)
        m.beam_x("41239", -20, s * 22, 44, "dark")
    for x in (96, 24, -60, -132):
        m.add("32316", (x, 0, 28), BEAM_Y, "dark")
    # fedélzet
    for x in (60, -28, -116):
        m.add("64782", (x, 0, 54), PANEL_FLAT, C)
    # sárvédők
    for x in xs:
        for s in (1, -1):
            m.add("15458", (x, s * ty, 74), R(X, -Z, Y) @ np.eye(3) if False else rotZ(0) @ np.array([[1, 0, 0], [0, 0, 1.], [0, -1, 0]]) @ np.eye(3) if False else R(X, -Z, Y) @ np.eye(3) @ np.diag([1, 1, 1]) @ np.eye(3) @ small_fender(), "dark")
    # kitámasztók: kinyúló 7L gerenda + függőleges láb + talp
    for x in (64, -100):
        for s in (1, -1):
            m.add("32524", (x, s * 66, 30), BEAM_Y, C)
            m.add("3705", (x, s * 88, 16), AX_Z, "metal")
            m.add("15535", (x, s * 88, 0.5), R(X, -Z, Y) @ np.diag([1, 1, 1]), "dark")
            m.add("62821", (x, s * 88, 4), R(Y, -Z, X) @ np.eye(3) if False else np.array([[1, 0, 0], [0, 0, 1.], [0, -1, 0]]) if False else R(X, Y, Z), "dark") if False else None
    # fülke (bal elöl)
    m.add("64782", (128, -14, 74), R(Y, -X, Z), C)
    m.add("64179", (128, -14, 118), R(Y, -X, Z) @ np.eye(3) if False else R(-Z, -X, Y) if False else front_window(), C)
    for yy in (30, -56):
        m.add("64782", (110, yy, 92), side_rot(1 if yy > 0 else -1), C)
    m.add("64782", (110, -14, 140), R(Y, Z, X), C)
    m.add("15458", (132, 0, 34), R(Y, -X, Z), "dark")
    # forgózsámoly + felépítmény
    xt = -60
    m.add("3648", (xt, 0, 60), R(X, Y, Z), "metal")
    m.add("62821", (xt, 0, 66), R(X, Y, Z), "dark")
    for s in (1, -1):
        m.add("64179", (xt - 6, s * 20, 90), R(X, Y * 1, Z) if s > 0 else R(-X, -Y, Z), C)
        m.add("62531", (xt - 44, s * 22, 92), R(-Y, -Z, X) if s > 0 else R(Y, -Z, -X), "dark")  # ellensúly
    m.add("64782", (xt - 44, 0, 112), R(Y, Z, X), "dark")
    # gém: csukló (xt+4, z 110), 30°-os dőlés előre
    a = math.radians(28)
    piv = np.array([xt + 6, 0, 112.0]); d = np.array([math.cos(a), 0, math.sin(a)])
    for s in (1, -1):
        for (p, c0, col) in (("32278", 60, C), ("41239", 150, C), ("32525", 236, C)):
            m.add(p, piv + d * c0 + np.array([0, s * 8, 0]), rotY(a) @ BEAM_X, col)
        for (p, c0) in (("32278", 60), ("41239", 150)):
            m.add(p, piv + d * c0 + np.array([0, s * 8, 0]) + rotY(a) @ np.array([0, 0, -8.0]), rotY(a) @ BEAM_X, "dark")
    # gém-keresztcsapok
    for k in range(0, 280, 24):
        m.add("6558", piv + d * k, rotY(a) @ R(Y, -X, Z), "pin")
    tip = piv + d * 280
    m.add("3713", tip, R(Y, Z, X) @ np.eye(3) if False else R(X, -Z, Y), "metal")
    m.add("6589", tip + np.array([0, 0, 0]), R(X, -Z, Y), "metal")
    # kötél + horog
    hook_top = tip + np.array([2, 0, -6])
    m.add("44294", hook_top + np.array([0, 0, -28]), AX_Z, "rope")
    m.add("62821", hook_top + np.array([0, 0, -72]), R(X, Y, Z) if False else R(X, -Z, Y), "orange")
    m.add("6628", hook_top + np.array([0, 0, -90]), AX_Z, "metal")
    # emelőhenger
    cyl0 = np.array([xt + 34, 0, 72.0]); cyl1 = piv + d * 110
    v = cyl1 - cyl0; L = np.linalg.norm(v); u = v / L
    # 2909 + 2910: helyi -Y irányban nyúlik -> forgassuk -Y-t u-ra
    rr = rot_to(np.array([0, -1.0, 0]), u)
    m.add("2909", cyl0 + u * 16, rr, "dark"); m.add("2910", cyl0 + u * 60, rr, "metal")
    return m


def small_fender():
    return np.eye(3)


def front_window():
    return R(Y, -X, Z)


def rot_to(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1, -1, -1.])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


MODELS = {"race": race_car, "truck": truck, "crane": crane}

if __name__ == "__main__":
    for k, f in MODELS.items():
        mm = f(); print(k, len(mm.items))
