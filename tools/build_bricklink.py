"""BrickLink Wanted List XML a darabjegyzékből.
Bemenet: content/bom.json (592 elem, LDraw-cikkszámok) + a render színkiosztása (video/render_v3/cache/scene.npz: elemenkénti 'kind').
Kimenet:  downloads/TT_bricklink_wanted.xml  (BrickLink: Wanted -> Upload)
          content/bricklink.json           (összesítő a weboldalnak: tételek, kétséges azonosítók)
Futtatás a site/ mappából:  python3 tools/build_bricklink.py [--scene <scene.npz>]
A színek a digitális modell színei (nem gyári készlet), a valós elérhetőség és ár változhat.
"""
import json, os, sys, collections, argparse
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

# render-'kind' -> BrickLink színkód (név)
KIND2BL = {"frame": 11, "susp": 11, "tarto": 11, "tyre": 11,
           "steer": 85, "other": 85, "csap": 85,
           "rim": 86, "v8": 86, "drive": 4, "panel": 5, "panel2": 1}
BLCOL = {1: "White", 4: "Orange", 5: "Red", 11: "Black", 85: "Dark Bluish Gray", 86: "Light Bluish Gray"}

# LDraw -> BrickLink cikkszám, ahol eltér vagy kétséges.  (bl, biztos?, megjegyzés HU, megjegyzés EN)
MAP = {
    "32123a": ("4265c", True, "BrickLinken 4265c (LDraw: 32123a)", "BrickLink uses 4265c (LDraw: 32123a)"),
    "3648": ("3648b", True, "BrickLinken 3648b (24 fogú, újabb változat)", "BrickLink 3648b (24 tooth, newer version)"),
    "2850": ("2850b", False, "változat (2850a/2850b) – ellenőrizd", "variant (2850a/2850b) – check"),
    "62821": ("62821b", False, "változat (62821a/b) – ellenőrizd", "variant (62821a/b) – check"),
    "32005": ("32005b", False, "„Type 2” – BrickLinken valószínűleg 32005b, ellenőrizd", "'Type 2' – probably 32005b on BrickLink, check"),
    "62519": ("62519", False, "kardáncsukló-belső; BrickLinken lehet, hogy csak egységként (61903) kapható", "U-joint centre; may only be sold as the complete 61903"),
    "62520": ("62520", False, "kardáncsukló-vég; lásd 62519", "U-joint end; see 62519"),
    "76537": ("76537", False, "teljes rugóstag – a BrickLink-azonosító eltérhet (c01 utótag)", "complete shock – BrickLink ID may carry a c01 suffix"),
    "2909": ("2909", False, "rugóstag-henger – a rugóval együtt egységként érdemes keresni", "shock cylinder – best bought as a complete unit with spring"),
    "2910": ("2910", False, "rugóstag-dugattyúrúd – lásd 2909", "shock piston rod – see 2909"),
}
SKIP = {"u9409-f1": ("a rugó a rugóstag-egység része – nincs a listában", "spring is part of the shock unit – not listed")}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--scene", default=os.path.join(ROOT, "..", "video", "render_v3", "cache", "scene.npz"))
    a = ap.parse_args()
    bom = json.load(open(os.path.join(ROOT, "content", "bom.json")))
    kinds = collections.defaultdict(collections.Counter)
    if os.path.exists(a.scene):
        import numpy as np
        D = np.load(a.scene)
        for p, k in zip(D["parts"], D["kinds"]): kinds[str(p)][str(k)] += 1
    lots = collections.OrderedDict(); doubt = []; skipped = []
    total_in = 0
    for r in bom["rows"]:
        p, q = r["partno"], int(r["qty"]); total_in += q
        if p in SKIP:
            skipped.append({"ldraw": p, "qty": q, "hu": SKIP[p][0], "en": SKIP[p][1]}); continue
        bl, sure, nhu, nen = MAP.get(p, (p, True, "", ""))
        if not sure: doubt.append({"ldraw": p, "bl": bl, "hu": nhu, "en": nen})
        split = kinds.get(p) or {"other": q}
        if sum(split.values()) != q: split = {max(split, key=split.get): q}
        cc = collections.Counter()
        for k, n in split.items(): cc[KIND2BL.get(k, 85)] += n
        for col, n in cc.items():
            key = (bl, col)
            if key not in lots: lots[key] = {"bl": bl, "ldraw": p, "color": col, "qty": 0, "name": r["name"], "sure": sure, "note": nen}
            lots[key]["qty"] += n
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<INVENTORY>"]
    for L in lots.values():
        rem = f"TT {L['ldraw']}" + ("" if L["sure"] else " – CHECK ID")
        out += ["  <ITEM>", "    <ITEMTYPE>P</ITEMTYPE>", f"    <ITEMID>{escape(L['bl'])}</ITEMID>", f"    <COLOR>{L['color']}</COLOR>",
                f"    <MINQTY>{L['qty']}</MINQTY>", "    <CONDITION>X</CONDITION>", f"    <REMARKS>{escape(rem)}</REMARKS>", "    <NOTIFY>N</NOTIFY>", "  </ITEM>"]
    out.append("</INVENTORY>")
    os.makedirs(os.path.join(ROOT, "downloads"), exist_ok=True)
    open(os.path.join(ROOT, "downloads", "TT_bricklink_wanted.xml"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    n_out = sum(L["qty"] for L in lots.values())
    summ = {"lots": len(lots), "pieces": n_out, "bom_pieces": total_in, "types": len({L['bl'] for L in lots.values()}),
            "colors": {BLCOL[c]: sum(L["qty"] for L in lots.values() if L["color"] == c) for c in sorted({L['color'] for L in lots.values()})},
            "doubtful": doubt, "skipped": skipped}
    json.dump(summ, open(os.path.join(ROOT, "content", "bricklink.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k not in ("doubtful",)}, ensure_ascii=False), "doubtful:", len(doubt))


if __name__ == "__main__":
    main()
