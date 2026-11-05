# ai-engineered-car – weboldal / website

**HU** · Statikus projektoldal (GitHub Pages), build-lépés nélkül. Sötét, Apple-szerű dizájn, HU/EN kapcsoló, three.js 3D- és VEM-nézegető.
**EN** · Static project site (GitHub Pages), no build step. Dark Apple-style design, HU/EN switch, three.js 3D and FEM viewers.

## Mappaszerkezet / Structure
```
index.html                  szekciók (hero, sztori, AI, 3D, film, VEM, számítás, könyvtár, BOM, napló, lábléc)
assets/css/style.css        stílus (színek: :root változók; narancs = --accent)
assets/js/main.js           belépési pont: nyelv, navigáció, adatvezérelt szekciók, lusta 3D-betöltés
assets/js/i18n.js           HU/EN (content/i18n/*.json; ?lang=en; localStorage)
assets/js/stage.js          közös three.js színpad
assets/js/viewer.js         3D-nézegető (robbantott nézet, részegységek, info, animáció)
assets/js/fem.js            VEM-nézegető (színskála, deformáció-nagyítás, esetfülek)
assets/vendor/three/        three.js r180 (MIT) – helyben, importmap-pel
assets/model/truck.glb      3D modell  +  parts.json (részegység-nevek, színek)
assets/fem/cases.json       VEM-esetek  +  <eset>.glb
assets/video/media.json     {"hero": bool, "film": bool} – mely videók léteznek
assets/video/film.mp4, film.hu.vtt, film.en.vtt, hero.mp4
assets/fig/*.webp           ábrák, hero.webp (helyőrző poszter)
assets/lib/library.json     alkatrészkönyvtár  +  thumbs/*.webp
content/calc.json, bom.json, naplo.hu.json, naplo.md, i18n/hu.json, i18n/en.json
tools/                      generáló szkriptek (python) + check.js (Playwright)
```

## Cserék / Replacing content
| Mit / What | Hogyan / How |
|---|---|
| **3D modell** | Írd felül `assets/model/truck.glb`-t (konvenció lent). Ha új részegység van, egészítsd ki `assets/model/parts.json` `groups` listáját. |
| **Film** | Másold be `assets/video/film.mp4` (+ `film.hu.vtt`, `film.en.vtt`), és állítsd `media.json`-ban `"film": true`. Poszter: `assets/fig/hero.webp`. |
| **Hero-videó** | `assets/video/hero.mp4` (néma, hurkolható, ≤ 8 MB) + `"hero": true`. |
| **VEM** | Új `assets/fem/<id>.glb` + bejegyzés `assets/fem/cases.json`-ba (vagy `tools/build_fem.py`). |
| **Napló** | Másold a projekt `claude/naplo.md`-jét `content/naplo.md`-be → `python3 tools/build_naplo.py`. |
| **BOM / számítás / könyvtár** | `python3 tools/build_data.py` (források: calc/bom.csv, layout/layout_v2.json, cadlib/manifest_*.json). |
| **Szövegek** | `content/i18n/hu.json` és `en.json` (azonos kulcsok). |

## truck.glb konvenció / convention
- glTF tengelyek: **+X előre, +Y fel, +Z jobbra**; egység mm, a gyökér `truck` csomópont `scale = 0.001`.
- Csoportok: `G_vaz, G_elso_futomu, G_hatso_hid, G_hajtaslanc, G_V8, G_karosszeria, G_kerekek` (extras: `{"group": id}`) – a kapcsolók ezeket rejtik/mutatják.
- Alkatrészek: `P_<cikkszám>_<nn>` (pl. `P_44771_03`), extras: `{"group","partno","design_id","name"}` – az info-kártya ezt mutatja; a robbantott nézet ezeket tolja ki.
- Kerék-pivotok: `W_FL, W_FR, W_RL, W_RR` a kerékközépen, forgás a helyi +Z körül; ezek alatt a gumi és felni.
- Animációk: bármennyi glTF-klip (a lejátszó listázza); ha nincs, a nézegető demó kerékforgást csinál.
- Méret: cél < 10 MB (Draco/meshopt nélkül; a jelenlegi helyőrző 1,4 MB).

## FEM GLB formátum
Egy mesh / egy primitive, mm, +Y fel. `POSITION` = deformálatlan felület, `COLOR_0` = feszültségszín (skála: `cases.json` `scale`), `_STRESS` = von Mises [MPa] csúcsonként, **morph target 0** = valós elmozdulás mm-ben (1,0 = valós). `mesh.extras`: `{case, vmin, vmax, umax_mm}`.

## Helyi futtatás / Local preview
```
python3 -m http.server 8765        # majd: http://localhost:8765/
NODE_PATH=$(npm root -g) node tools/check.js   # Playwright-képek a _check/ mappába
```
A `_check/` mappát nem kell feltölteni. GitHub Pages: a gyökér legyen ez a mappa (`.nojekyll` megvan), minden útvonal relatív.

---
A LEGO® a LEGO Group védjegye; ez a projekt nem kapcsolódik hozzá és nem általa támogatott. A SOLIDWORKS® a Dassault Systèmes védjegye. three.js © three.js authors (MIT).
