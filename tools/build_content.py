#!/usr/bin/env python3
"""Weboldal-tartalom (2026-11-05): ábrák WebP-be, videók + poszterek, letöltések, BOM.
Források: /home/claude/work/pyA (A1–A7), /home/claude/work/export (STEP), /home/claude/work/video (S1, S2, previs_v3),
a SolidWorks-képek (cad\\assy_v2, a felhasználó gépéről csak olvasva: /mnt/user-data/uploads/AI challange/cad/assy_v2).
Futtatás: python3 tools/build_content.py"""
import csv, json, os, shutil, subprocess, zipfile, collections
from PIL import Image
W = '/home/claude/work'; S = W + '/site'
RGEOM = os.environ.get('TT_GEOM')          # R: rögzítés-javított geometria (BOM + STEP-zip ebből)
ONLY_DATA = bool(os.environ.get('ONLY_DATA'))  # csak BOM + letöltések (ábrák/videók változatlanok)
STEPDIR = os.environ.get('STEPDIR', W + '/export')
SW = '/mnt/user-data/uploads/AI challange/cad/assy_v2'

import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rotate_cad                          # 11-05: a 4 elforgatott SW-képernyőkép visszaforgatása (tools/rotate_cad.py)
def webp(src, dst, maxw=1600, q=82):
    im = Image.open(src).convert('RGB')
    if os.path.basename(src)[:-4] in rotate_cad.ROT_CW: im = rotate_cad.fix(im)
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(dst, 'WEBP', quality=q, method=6); return im.size

FIG = {  # részegység-ábrák (Python-modell)
 'A1_01': 'pyA/A1_elso_futomu/fig/A1_01_elolnezet.png', 'A1_05': 'pyA/A1_elso_futomu/fig/A1_05_ellenorzo_diagramok.png',
 'A1c_04': 'pyA/A1c_elso_osztomu/fig/A1c_04_izometrikus_3d.png', 'A1c_05': 'pyA/A1c_elso_osztomu/fig/A1c_05_kupkerek_kapcsolodas.png',
 'A2_04': 'pyA/A2_hatso_hid/fig/A2_04_izometrikus_3d.png', 'A2_01': 'pyA/A2_hatso_hid/fig/A2_01_hatulnezet.png',
 'A3_04': 'pyA/A3_kozepso_hajtaslanc/fig/A3_04_izometrikus_3d.png', 'A3_03': 'pyA/A3_kozepso_hajtaslanc/fig/A3_03_kozepdiff_metszet.png',
 'A4_04': 'pyA/A4_valto_V8/fig/A4_04_izometrikus_3d.png', 'A4_03': 'pyA/A4_valto_V8/fig/A4_03_fokozatok_erofolyam.png',
 'A4_06': 'pyA/A4_valto_V8/fig/A4_06_V8.png', 'A6d_1': 'pyA/A6d_integracio/fig/A6d_fig1_teljes_jarmu.png',
 'A6c_01': 'pyA/A6c_valtohaz_motortarto/fig/A6c_01_iso.png', 'A3_07': 'pyA/A3_kozepso_hajtaslanc/fig/A3_07_letrakeret.png',
 'A7_V2': 'pyA/A7_burkolat/fig/A7_V2_izometrikus.png', 'A7_cmp': 'pyA/A7_burkolat/fig/A7_osszehasonlitas.png',
}
CAD = ['SA_elso_futomu/SA_elso_futomu_kormany_max_izometrikus.png', 'SA_elso_futomu/SA_elso_futomu_rugozas_B_plus8_izometrikus.png',
       'SA_hatso_futomu/SA_hatso_futomu_csuklas_11fok_hatulnezet.png', 'SA_hatso_futomu/SA_hatso_futomu_statikus_kardannal_izometrikus.png',
       'SA_valto/SA_valto_C1b_izometrikus.png', 'SA_valto/C5_F1.png', 'SA_vaz/SA_vaz_izometrikus.png', 'SA_vaz/SA_vaz_felul.png']
sizes = {}
if ONLY_DATA:
    sizes = json.load(open(f'{S}/assets/fig/sizes.json'))
    sizes['cad/TT_teljes_step'] = webp(f'{STEPDIR}/TT_teljes_elonezet_1_izometrikus.png', f'{S}/assets/fig/cad/TT_teljes_step.webp', 1400)
    json.dump({k: list(v) for k, v in sizes.items()}, open(f'{S}/assets/fig/sizes.json', 'w'), indent=0)
for k, p in ({} if ONLY_DATA else FIG).items(): sizes['sub/' + k] = webp(f'{W}/{p}', f'{S}/assets/fig/sub/{k}.webp')
for p in ([] if ONLY_DATA else CAD):
    k = os.path.basename(p)[:-4]; sizes['cad/' + k] = webp(f'{SW}/{p}', f'{S}/assets/fig/cad/{k}.webp', 1400)
if not ONLY_DATA: sizes['cad/TT_teljes_step'] = webp(f'{STEPDIR}/TT_teljes_elonezet_1_izometrikus.png', f'{S}/assets/fig/cad/TT_teljes_step.webp', 1400)
if not ONLY_DATA: json.dump({k: list(v) for k, v in sizes.items()}, open(f'{S}/assets/fig/sizes.json', 'w'), indent=0)

# videók (H.264, mind < 10 MB) + poszterek
V = {'previs_v3.mp4': 'video/previs_v3/previs_v3.mp4', 'S1_vem_hu.mp4': 'video/snitt_S1_vem/S1_vem_hu.mp4', 'S1_vem_en.mp4': 'video/snitt_S1_vem/S1_vem_en.mp4',
     'S2_hajtaslanc_hu.mp4': 'video/snitt_S2_hajtaslanc/S2_hajtaslanc_hu.mp4', 'S2_hajtaslanc_en.mp4': 'video/snitt_S2_hajtaslanc/S2_hajtaslanc_en.mp4'}
for d, s in ({} if ONLY_DATA else V).items():
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{W}/{s}', '-c', 'copy', '-movflags', '+faststart', f'{S}/assets/video/{d}'], check=True)
for name, src, t in [] if ONLY_DATA else [('previs_v3', 'previs_v3.mp4', 54), ('S1_vem', 'S1_vem_hu.mp4', 7), ('S2_hajtaslanc', 'S2_hajtaslanc_hu.mp4', 5)]:
    tmp = f'/tmp/claude-0/{name}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', f'{S}/assets/video/{src}', '-frames:v', '1', tmp], check=True)
    webp(tmp, f'{S}/assets/video/{name}.webp', 1280, 80)

# letöltések: a 120 MB-os STEP zip-elve (GitHub-korlát 50 MB/fájl)
z = f'{S}/downloads/TT_teljes.step.zip'
if RGEOM or not os.path.exists(z):
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(f'{STEPDIR}/TT_teljes.step', 'TT_teljes.step')
        zf.write(f'{STEPDIR}/TT_teljes_hianyok.md', 'TT_teljes_hianyok.md')

# BOM: A6d (443 elem, részegységenként) + A7 V2 burkolat (42 elem)
SUB = {'01': ('Váz', 'Frame'), '02': ('Váz', 'Frame'), '03': ('Váz', 'Frame'), '04': ('Váz', 'Frame'), '05': ('Váltóház', 'Gearbox housing'),
       '06': ('Első futómű', 'Front suspension'), '07': ('Kormány', 'Steering'), '08': ('Első osztómű', 'Front axle drive'),
       '09': ('Középső hajtáslánc', 'Centre driveline'), '10': ('Hátsó híd', 'Rear axle'), '11': ('Váltó', 'Gearbox'), '12': ('V8', 'V8'),
       '13': ('Burkolat', 'Body'), 'R': ('Rögzítés', 'Fastening')}
FIXNAME = {'2850': 'Technic Engine Cylinder (2850a/2850b)', '3648': 'Technic Gear 24 Tooth (3648b)'}
rows = collections.OrderedDict(); notes = {}
for r in csv.DictReader(open(f'{W}/pyA/A6d_integracio/bom_A6_osszesitett.csv', encoding='utf-8')): notes[r['partno']] = r['megj']
def add(pn, name, sub, n):
    e = rows.setdefault(pn, {'partno': pn, 'name': FIXNAME.get(pn, name), 'qty': 0, 'where': collections.OrderedDict(), 'note': notes.get(pn, '')})
    e['qty'] += n; e['where'][sub] = e['where'].get(sub, 0) + n
if RGEOM:   # egy forrás: r_geometry.json (elemenként)
    LDN = {e['partno']: e['ldraw_nev'] for e in json.load(open(f'{W}/pyA/A6d_integracio/a6d_geometry.json'))['elemek']}
    for e in json.load(open(RGEOM, encoding='utf-8'))['elemek']:
        k = e['reszegyseg'][:2]; k = 'R' if k.startswith('R') else k
        add(e['partno'], e.get('ldraw_nev') or LDN.get(e['partno'], e['partno']), k, 1)
else:
  for r in csv.DictReader(open(f'{W}/pyA/A6d_integracio/bom_A6.csv', encoding='utf-8')):
    add(r['partno'], r['ldraw_nev'], r['reszegyseg'][:2], int(r['db']))
  geo = json.load(open(f'{W}/pyA/A7_burkolat/a7_geometry_V2.json', encoding='utf-8'))
  for e in geo['burkolat']: add(e['partno'], e['ldraw_nev'], '13', 1)
out = []
for e in sorted(rows.values(), key=lambda e: (-e['qty'], e['partno'])):
    w = collections.OrderedDict()
    for k, n in e['where'].items(): w[SUB[k][0]] = w.get(SUB[k][0], 0) + n
    wen = collections.OrderedDict()
    for k, n in e['where'].items(): wen[SUB[k][1]] = wen.get(SUB[k][1], 0) + n
    out.append({'partno': e['partno'], 'name': e['name'], 'qty': e['qty'], 'where_hu': ' · '.join(f'{k} {n}' for k, n in w.items()),
                'where_en': ' · '.join(f'{k} {n}' for k, n in wen.items()), 'groups': sorted({SUB[k][0] for k in e['where']}), 'note': e['note']})
tot = sum(r['qty'] for r in out)
json.dump({'source': ('pyA/R_rogzites/%s (%d elem: A6d + A7 V2 burkolat + R/R2 rögzítés)' % (os.path.basename(RGEOM), tot)) if RGEOM else 'pyA/A6d_integracio/bom_A6.csv (443) + pyA/A7_burkolat/a7_geometry_V2.json (42)', 'total': tot, 'rows': out,
           'groups': [[v[0], v[1]] for k, v in SUB.items() if k not in ('02', '03', '04')]},
          open(f'{S}/content/bom.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
with open(f'{S}/downloads/TT_darabjegyzek.csv', 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['cikkszam', 'megnevezes_ldraw', 'db', 'reszegysegek', 'megjegyzes'])
    for r in out: w.writerow([r['partno'], r['name'], r['qty'], r['where_hu'], r['note']])
print('BOM', len(out), 'tétel,', tot, 'db'); print('ábrák', len(sizes))
