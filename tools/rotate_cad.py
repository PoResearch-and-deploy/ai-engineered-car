"""SolidWorks-galéria: az első négy képernyőkép (első futómű kormányzás / +8 mm, hátsó híd csuklás / kardán) 90°-kal
elforgatott nézetből készült (a kerekek oldalt). Itt az óramutató irányába 90°-kal visszaforgatjuk (kerekek alul, a
kormányoszlop / a váz felfelé – vizuálisan ellenőrizve), a tartalomra vágjuk, és 16:10-re egészítjük ki a szélső
oszlopok ismétlésével (a SolidWorks-háttér színátmenete így folytonos marad). Használja: tools/build_content.py."""
import numpy as np
from PIL import Image

ROT_CW = {'SA_elso_futomu_kormany_max_izometrikus', 'SA_elso_futomu_rugozas_B_plus8_izometrikus',
          'SA_hatso_futomu_csuklas_11fok_hatulnezet', 'SA_hatso_futomu_statikus_kardannal_izometrikus'}

def fix(im, aspect=16 / 10, margin=0.06):
    im = im.convert('RGB').rotate(-90, expand=True)                # óramutató irányába
    a = np.asarray(im).astype(int)
    # háttér: soronként a két szélső pixel lineáris átmenete (a SW-színátmenet vízszintes lett) -> eltérés = tartalom
    bg = a[:, :1, :] + (a[:, -1:, :] - a[:, :1, :]) * np.linspace(0, 1, a.shape[1])[None, :, None]
    m = np.abs(a - bg).max(2) > 28
    ys, xs = np.where(m)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    h, w = y1 - y0, x1 - x0; my, mx = int(h * margin) + 8, int(w * margin) + 8
    y0, y1 = max(0, y0 - my), min(a.shape[0], y1 + my); x0, x1 = max(0, x0 - mx), min(a.shape[1], x1 + mx)
    c = a[y0:y1, x0:x1]
    H, W = c.shape[:2]
    if W / H < aspect:                                             # szélesíteni kell: szélső oszlopok ismétlése
        W2 = int(round(H * aspect)); pl = (W2 - W) // 2; pr = W2 - W - pl
        c = np.concatenate([np.repeat(c[:, :1], pl, 1), c, np.repeat(c[:, -1:], pr, 1)], 1)
    else:
        H2 = int(round(W / aspect)); pt = (H2 - H) // 2; pb = H2 - H - pt
        c = np.concatenate([np.repeat(c[:1], pt, 0), c, np.repeat(c[-1:], pb, 0)], 0)
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))
