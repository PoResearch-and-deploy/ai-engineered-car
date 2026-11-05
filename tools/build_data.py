#!/usr/bin/env python3
"""Adatfájlok generálása a weboldalhoz (build-lépés nélküli statikus oldal; ezt a szkriptet kézzel futtatjuk).

  python3 tools/build_data.py
Kimenetek:
  content/bom.json           <- /home/claude/work/calc/bom.csv (később: végleges BOM)
  content/calc.json          <- layout_v2.json (Trophy truck) + results.json (régi, buggy) – kártyák + ábrák
  assets/lib/library.json    <- cadlib/manifest_*.json
  assets/lib/thumbs/*.webp   <- könyvtár PNG-k (~300 px)
  assets/fig/*.webp          <- számítási / makett ábrák (≤1600 px)
  assets/fig/hero.webp       <- látványterv v0.2, 3/4 nézet kivágása (hero helyőrző)
"""
import csv, glob, json, os, re
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); SITE = os.path.dirname(HERE)
W = '/home/claude/work'
LIBPNG = '/mnt/user-data/uploads/AI challange/cad/lib'
os.makedirs(f'{SITE}/content', exist_ok=True); os.makedirs(f'{SITE}/assets/lib/thumbs', exist_ok=True)
os.makedirs(f'{SITE}/assets/fig', exist_ok=True)

def num(s):
    try: return float(str(s).replace(',', '.'))
    except Exception: return None

# --- BOM ---
rows = []
for r in csv.DictReader(open(f'{W}/calc/bom.csv', encoding='utf-8')):
    rows.append({'pos': r['poz'], 'group': r['részegység'], 'name': r['megnevezés'], 'partno': r['cikkszám'],
                 'qty': int(num(r['darab']) or 0), 'color': r['szín'], 'mass_g': num(r['becsült tömeg g']),
                 'check': r['ellenőrzés'], 'note': r['megjegyzés'], 'url': r['forrás-URL']})
json.dump({'source': 'calc/bom.csv (buggy-változat – a Trophy truck végleges BOM-ja váltja)', 'placeholder': True,
           'rows': rows}, open(f'{SITE}/content/bom.json', 'w'), ensure_ascii=False, indent=1)

# --- könyvtár ---
GROUPS = {'E1': ('Gerendák', 'Beams'), 'V1': ('Gerendák', 'Beams'), 'V2': ('Keretek', 'Frames'),
          'E2': ('Tengelyek, csapok', 'Axles & pins'), 'K1': ('Tengelyek, csapok', 'Axles & pins'),
          'E5': ('Fogaskerekek', 'Gears'), 'M1': ('Fogaskerekek', 'Gears'),
          'E6': ('Kormány, kardán', 'Steering & U-joints'), 'E8': ('Futómű', 'Suspension'),
          'M2': ('Futómű', 'Suspension'), 'E10': ('Kerekek', 'Wheels'), 'R1': ('Kerekek', 'Wheels'),
          'K2': ('Összekötők', 'Connectors'), 'B1': ('Burkolat', 'Panels'), 'K3': ('Kiegészítők', 'Extras'),
          'K4': ('Váltó, V8', 'Gearbox & V8')}
items = []
for f in sorted(glob.glob(f'{W}/cadlib/manifest_*.json')):
    fam = json.load(open(f))
    key = fam['family'].split('_')[0]
    ghu, gen = GROUPS.get(key, ('Egyéb', 'Other'))
    for p in fam.get('parts', []):
        p['partno'] = p.get('partno') or p.get('design_id')
        if not p['partno']: continue
        src = (p.get('png') or re.sub(r'\.SLDPRT$', '.png', p.get('sldprt', ''), flags=re.I)).replace('\\', '/')
        thumb = None
        if src:
            rel = src.split('/cad/lib/')[-1]
            pth = os.path.join(LIBPNG, rel)
            if os.path.exists(pth):
                name = re.sub(r'[^A-Za-z0-9._-]', '_', os.path.basename(rel))[:-4] + '.webp'
                out = f'{SITE}/assets/lib/thumbs/{name}'
                if not os.path.exists(out):
                    im = Image.open(pth).convert('RGB'); im.thumbnail((300, 300)); im.save(out, 'WEBP', quality=78)
                thumb = f'assets/lib/thumbs/{name}'
        items.append({'partno': p['partno'], 'name': p.get('name', ''), 'family': fam['family'], 'group': ghu,
                      'group_en': gen, 'status': p.get('status', ''), 'bbox_mm': p.get('bbox_mm'),
                      'volume_mm3': p.get('volume_mm3'), 'thumb': thumb})
json.dump({'count': len(items), 'items': items}, open(f'{SITE}/assets/lib/library.json', 'w'), ensure_ascii=False, indent=1)
for old in ('manifest.json',):
    if os.path.exists(f'{SITE}/assets/lib/{old}'): os.remove(f'{SITE}/assets/lib/{old}')

# --- ábrák ---
def webp(src, dst, maxw=1600, crop=None):
    im = Image.open(src).convert('RGB')
    if crop: im = im.crop(crop)
    im.thumbnail((maxw, maxw * 3)); im.save(f'{SITE}/assets/fig/{dst}', 'WEBP', quality=82); return im.size
figs = []
FIGS = [(f'{W}/layout/fig/01_nezetek.png', 'makett_nezetek.webp', 'Digitális makett – nézetek', 'Digital mock-up – views'),
        (f'{W}/layout/fig/02_futomu_szelso.png', 'futomu_szelso.webp', 'Futómű szélső helyzetekben', 'Suspension at its limits'),
        (f'{W}/layout/fig/03_valto_fokozatok.png', 'valto_fokozatok.webp', 'Szekvenciális váltó fokozatai', 'Sequential gearbox ratios'),
        (f'{W}/layout/fig/04_hajtaslanc_blokk.png', 'hajtaslanc.webp', 'Hajtáslánc: kerekek → V8', 'Driveline: wheels → V8'),
        (f'{W}/calc/fig/d_tengely_csavaras.png', 'tengely_csavaras.webp', 'Mikor csavarodik el a tengely?', 'When does the axle twist off?'),
        (f'{W}/feas/fem_gerenda.png', 'fem_gerenda.webp', 'VEM-teszt: 15L gerenda', 'FEM test: 15L beam')]
for src, dst, hu, en in FIGS:
    if os.path.exists(src):
        w, h = webp(src, dst); figs.append({'src': f'assets/fig/{dst}', 'w': w, 'h': h, 'hu': hu, 'en': en})
hero = '/mnt/user-data/outputs/latvanyterv_v02.png'
if os.path.exists(hero): webp(hero, 'hero.webp', 1400, crop=(150, 220, 1110, 760))

# --- számítás-kártyák (Trophy truck: layout_v2 az elsődleges) ---
L = json.load(open(f'{W}/layout/layout_v2.json')); fm = L['fo_meretek']
fmt = lambda x, d=1: (f'{x:.{d}f}').replace('.', ',')
cards = [
    {'k': 'wheelbase', 'v': fmt(fm['tengelytav'], 0), 'u': 'mm', 'hu': 'Tengelytáv', 'en': 'Wheelbase', 'shu': '24 modul', 'sen': '24 studs'},
    {'k': 'track', 'v': f"{fmt(fm['nyomtav_elol'])} / {fmt(fm['nyomtav_hatul'], 0)}", 'u': 'mm', 'hu': 'Nyomtáv elöl / hátul', 'en': 'Track front / rear', 'shu': 'kormánycsap a rácson', 'sen': 'kingpin on the grid'},
    {'k': 'mass', 'v': fmt(fm['tomeg_g'], 0), 'u': 'g', 'hu': 'Becsült tömeg', 'en': 'Estimated mass', 'shu': f"súlypont z = {fmt(fm['sulypont'][2], 0)} mm", 'sen': f"CoG z = {fm['sulypont'][2]:.0f} mm"},
    {'k': 'travel', 'v': f"±{fmt(max(abs(x) for x in fm['rugout_elol']), 0)}", 'u': 'mm', 'hu': 'Első rugóút', 'en': 'Front wheel travel', 'shu': 'hosszú lengőkarok', 'sen': 'long-travel A-arms'},
    {'k': 'artic', 'v': f"±{fmt(fm['csuklas_hatul_fok'])}", 'u': '°', 'hu': 'Hátsó híd csuklása', 'en': 'Rear axle articulation', 'shu': '4-link, merev híd', 'sen': '4-link solid axle'},
    {'k': 'ground', 'v': fmt(fm['hasmagassag']), 'u': 'mm', 'hu': 'Hasmagasság', 'en': 'Ground clearance', 'shu': f"Ø{fmt(fm['kerek_atmero'])} terepgumi", 'sen': f"Ø{fm['kerek_atmero']} mm off-road tyres"},
    {'k': 'ackermann', 'v': '0,4', 'u': '°', 'hu': 'Ackermann-hiba', 'en': 'Ackermann error', 'shu': 'belső kerék ≤ 30°', 'sen': 'inner wheel ≤ 30°'},
    {'k': 'gears', 'v': '5,44 · 3,27 · 1,81', 'u': '', 'hu': 'Váltó: főtengely / kerék', 'en': 'Gearbox: crank / wheel', 'shu': 'szekvenciális, 3 fokozat', 'sen': 'sequential, 3 speeds'},
]
json.dump({'source': 'layout_v2.json (digitális makett v2.1)', 'cards': cards, 'figs': figs},
          open(f'{SITE}/content/calc.json', 'w'), ensure_ascii=False, indent=1)
print('bom', len(rows), 'lib', len(items), 'thumbs', sum(1 for i in items if i['thumb']), 'figs', len(figs))
