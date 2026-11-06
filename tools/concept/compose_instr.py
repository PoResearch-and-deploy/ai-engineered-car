"""LEGO-útmutató-stílusú lapok összeállítása (PIL): lépésszám, alkatrész-keret darabszámmal, új elemek narancs kontúrral, nyíl.
Bemenet: out_instr/s{k}_col.png, s{k}_mask.png, t_<cikkszám>.png, meta.json.  Kimenet: out_instr/utmutato_{k}.png
"""
import os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "out_instr")
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
if not os.path.exists(FB): FB = "/home/claude/work/video/render_v3/fonts/Inter-SemiBold.otf"
BG = (238, 243, 247); ACC = (242, 140, 40); INK = (29, 29, 31)
W, H = 1400, 1000
meta = json.load(open(os.path.join(D, "meta.json")))
N = len(meta["steps"])

cols = [Image.open(os.path.join(D, f"s{k + 1}_col.png")).convert("RGBA") for k in range(N)]
masks = [np.asarray(Image.open(os.path.join(D, f"s{k + 1}_mask.png")).convert("RGBA")).astype(int) for k in range(N)]
# közös kivágás: minden lépés alfa-uniója
A = np.zeros(cols[0].size[::-1], bool)
for c in cols: A |= np.asarray(c)[:, :, 3] > 8
ys, xs = np.where(A); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
pad = 40; x0, y0 = max(0, x0 - pad), max(0, y0 - pad); x1, y1 = min(A.shape[1], x1 + pad), min(A.shape[0], y1 + pad)
area = (420, 150, W - 40, H - 30)   # a fő kép helye
sc = min((area[2] - area[0]) / (x1 - x0), (area[3] - area[1]) / (y1 - y0))
ox = area[0] + ((area[2] - area[0]) - (x1 - x0) * sc) / 2; oy = area[1] + ((area[3] - area[1]) - (y1 - y0) * sc) / 2


def fnt(s): return ImageFont.truetype(FB, s)


def arrow(dr, p0, p1, col, w=10):
    p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]])
    head = 34; base = p1 - u * head
    for (ww, cc) in ((w + 8, (255, 255, 255)), (w, col)):
        dr.line([tuple(p0), tuple(base)], fill=cc, width=ww)
        hw = head * 0.62 + (4 if cc == (255, 255, 255) else 0)
        tip = p1 + (u * 5 if cc == (255, 255, 255) else 0)
        dr.polygon([tuple(tip), tuple(base + n * hw), tuple(base - n * hw)], fill=cc)


for k in range(N):
    page = Image.new("RGB", (W, H), BG); dr = ImageDraw.Draw(page)
    im = cols[k].crop((x0, y0, x1, y1)); im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    m = masks[k]; mag = (m[:, :, 1] < 140) & (m[:, :, 0] > m[:, :, 1] + 60) & (m[:, :, 3] > 100)
    mk = Image.fromarray((mag[y0:y1, x0:x1] * 255).astype(np.uint8)).resize(im.size, Image.NEAREST)
    # narancs kontúr az új elemek körül (dilatált maszk - maszk), a kép mögé
    dil = mk.filter(ImageFilter.MaxFilter(11))
    glow = Image.new("RGBA", im.size, ACC + (0,)); glow.putalpha(dil)
    page.paste(glow, (int(ox), int(oy)), glow)
    page.paste(im, (int(ox), int(oy)), im)
    # nyíl az új elemek súlypontja felé, bal felülről
    yy, xx = np.where(np.asarray(mk) > 0)
    if len(xx):
        cx, cy = ox + xx.mean(), oy + yy.mean()
        # a legközelebbi új-elem pont a bal felső irányból
        dvec = np.array([-0.62, -0.78]); dvec /= np.linalg.norm(dvec)
        proj = (xx - xx.mean()) * dvec[0] + (yy - yy.mean()) * dvec[1]; j = np.argmax(proj)
        tip = np.array([ox + xx[j], oy + yy[j]]) + dvec * 18
        arrow(dr, tip + dvec * 150, tip, ACC)
    # lépésszám
    dr.text((44, 30), str(k + 1), font=fnt(96), fill=INK)
    # alkatrész-keret
    items = list(meta["steps"][k]["new"].items()); cell = 118
    bx0, by0 = 44, 160; bw = cell * min(3, len(items)) + 28; rows = math.ceil(len(items) / 3); bh = rows * (cell + 34) + 24
    dr.rounded_rectangle((bx0, by0, bx0 + bw, by0 + bh), radius=18, fill=(255, 255, 255), outline=(150, 178, 200), width=3)
    for i, (p, n) in enumerate(items):
        tx = bx0 + 14 + (i % 3) * cell; ty = by0 + 14 + (i // 3) * (cell + 34)
        th = Image.open(os.path.join(D, f"t_{p}.png")).convert("RGBA"); th.thumbnail((cell - 12, cell - 12), Image.LANCZOS)
        page.paste(th, (tx + (cell - th.width) // 2, ty + (cell - th.height) // 2), th)
        dr.text((tx + 8, ty + cell - 4), f"{n}x", font=fnt(26), fill=INK)
    page.save(os.path.join(D, f"utmutato_{k + 1}.png"))
    print("lap", k + 1, items)
