# 12 – Weboldal

## TARTALOMFRISSÍTÉS (2026-11-05) – ez az érvényes
Szekciók: Hero (a mozgó glTF-ből készült kép) → Projekt (téma, 485 / 77 / 3+N / 8) → Módszer (kutatás → Python → CAD MCP-n át → ellenőrzés → bemutatás; R1–R4, A1–A7, C1–C5, 114) → **mozgó 3D-nézegető** (változatlan, + glTF/STEP letöltés) → **Részegységek** (8 kártya, `content/subsystems.json`, ábrák `assets/fig/sub/`, csak a pyA-jelentések igazolt számai) → **CAD-folyamat** (4 lépés + 9 SolidWorks-kép a `cad\assy_v2`-ből, `content/cad.json`, `assets/fig/cad/`) → Alkatrészkönyvtár → **Videó** (fülek: previs_v3 / S1 VEM / S2 hajtáslánc „MUNKAVERZIÓ”, + helyőrző a végleges filmnek; S1/S2 nyelv szerint HU/EN) → **VEM** (csak a mostani geometria: 3708 féltengely, létrakeret 3 g + csavarás, fogtő) → **BOM** (77 tétel / 485 db, A6d + A7 V2, kereshető + részegység-szűrő, `content/bom.json`) → **Letöltések** (`downloads/TT_teljes.step.zip` 21 MB – a 120 MB-os STEP + hiánylista; truck.glb; BOM CSV; GitHub) → **Napló** (`content/log.json`: eszközök, 6 szakmai prompt, 10 elakadás + megoldás, 4 tanulság; link a részletes `content/naplo.md`-re) → Zárókártya védjegy-szöveggel → lábléc. Nincs LEGO-logó.
Generálás: `python3 tools/build_content.py` (ábrák, videók faststart-tal, posterek, STEP-zip, BOM). Ellenőrzés: `tools/check_site.js` (asztali HU + iPhone EN: képek, videók, letöltések, 3D, VEM, nyelvváltás, túllógás) → 0 hiba; képek `_check/site_*.png`.
A „Számítás” szekció (layout_v2-számok, elavult) kikerült; a régi napló-JSON, VEM-esetek (lengőkar, 3L féltengely, régi létrakeret, gerenda, demó) és a helyőrző modell törölve.

---
# (korábbi állapot, 2026-11-03)

**Hol:** felhő `/home/claude/work/site/` (4,6 MB, build-lépés nélkül, relatív útvonalak → GitHub Pages `/ai-engineered-car/` alútvonalon is működik). Repó: `PoResearch-and-deploy/ai-engineered-car` (gyökér = ez a mappa; `_check/` nem kell, .gitignore-ban).
**Állapot:** váz kész, Playwright-ellenőrzés (desktop 1440×900 + iPhone 13, HU+EN): **0 konzolhiba**, a 3D- és a VEM-nézegető betölt. Ellenőrző képek: `site/_check/*.png`.

## Dizájn és technika
- Apple-szerű, fekete/grafit alap, nagy tipográfia (rendszer-betűkészlet – a Google Fonts a felhő-proxyn tiltva volt, és így nincs külső függés), görgetésre előtűnés (IntersectionObserver, `prefers-reduced-motion` tisztelve). Narancs `#F28C28` csak gomb, kulcsszám, csúszka-kitöltés, VEM-skála csúcsa.
- HU (alap) / EN kapcsoló a fejlécben; minden szöveg `content/i18n/{hu,en}.json`; választás `?lang=en` + localStorage (try/catch).
- three.js **r180 helyben** (`assets/vendor/three`, importmap) – nem CDN: offline/proxy mögött is megy, verziója rögzített. A 3D és a VEM csak akkor töltődik, ha a szekció közel ér (lazy).
- Lábléc: a kért védjegy-szöveg + „Készült a Polinvent belső AI-kihívására." + GitHub-link.

## Szekciók és adatforrások
| # | Szekció | Adat | Helyőrző? → mivel cseréljük |
|---|---|---|---|
| 1 | Hero | `assets/fig/hero.webp` (látványterv v0.2 3/4 nézet, halványítva); `assets/video/hero.mp4`, ha `media.json` `hero:true` | **igen** → render-ágens hero-videója (néma, hurok, ≤ 8 MB) |
| 2 | Sztori | i18n | végleges szöveg (rövid) |
| 3 | AI-munka | inline SVG folyamatábra + 4 szám (119 könyvtár-alkatrész, 184 elhelyezett alkatrész, ~230k token, 114 MCP-eszköz) | számok frissíthetők a végén |
| 4 | 3D-nézegető | `assets/model/truck.glb` + `parts.json` | **igen** – a makett (layout_v2) transzformációiból + 14 könyvtár-STL + gerenda-proxyk; 72 csomópont, 1,4 MB → végleges összeállítás GLB-je |
| 5 | Film | `assets/video/film.mp4` + `film.{hu,en}.vtt`; `media.json` `film:true` | **igen** (most „készül" felirat) → videó-ágens |
| 6 | VEM | `assets/fem/cases.json` + `<id>.glb` | `beam15` = **valódi** CalculiX (15L gerenda, 10 N, max 37,4 MPa, 12,5 mm); `axle_demo` = **DEMÓ** (jelölve) → VEM-ágens esetei |
| 7 | Számítás | `content/calc.json` (8 kártya a layout_v2-ből: tengelytáv 192, nyomtáv 150,4/144, 596 g, ±16 mm, ±9,1°, 17,2 mm, 0,4°, 5,44·3,27·1,81) + 6 ábra lightboxszal | frissítés a 10-es dok. véglegesítésekor |
| 8 | Könyvtár | `assets/lib/library.json` (119 tétel, 116 WebP-bélyegkép), kereső + csoportszűrő, 24 után „mind mutatása" | kész; új alkatrésznél `build_data.py` |
| 9 | BOM | `content/bom.json` | **igen** – a régi (buggy) 37 soros BOM → Trophy truck végleges BOM |
| 10 | Napló | `content/naplo.hu.json` ← `content/naplo.md` (`tools/build_naplo.py`) | EN: rövid angol összefoglaló + „csak magyarul" jelzés |

## truck.glb – MOZGÓ teljes autó (2026-11-05, `tools/build_anim_glb.py`)
- **Tartalom:** A6d teljes jármű (443 elem, `a6d_anim.full_scene()` kinematika – a previs_v3 `export_frames.kin()`-jén át) + A7 **V2** burkolat (42 elem, pótkerék **állítva** a plató végén); LDraw-hálók alkatrészenként egyszer (példányosítva), 30°-os élszöggel simított normálok. 495 csomópont, 136 háló, 21 anyag.
- **Méret:** nyers 6,6 MB → **1,8 MB** (gltfpack 0.25: `EXT_meshopt_compression` + `KHR_mesh_quantization`, `-kn -km -ke -ac -af 24 -vp 16`). Dekóder helyben: `assets/vendor/three/addons/libs/meshopt_decoder.module.js` (meshoptimizer 0.25, MIT).
- **Tengelyek:** +X előre, +Y fel, +Z jobbra; gyökér `truck` scale 0.001 (alatta mm). A gltfpack a hálókat névtelen gyerek-csomópontra teszi (dekvantálás) – a `P_` csomópont Object3D, a mozgás azon van.
- **Csoportok** (`G_<id>`, a6d `reszegyseg` szerint): `vaz` (01–04), `elso_futomu` (06), `kormany` (07), `hatso_hid` (10), `hajtaslanc` (08 osztómű + 09 kardánok), `valto` (11 + 05 váltóház), `V8` (12), `kerekek`, `karosszeria` (A7 V2).
- **Alkatrészek:** `P_<cikkszám>_<nn>`, extras `{group, partno, name (LDraw-név), design_id, element (a Python-modell elemneve), sub (részegység), explode [mm, glTF-tengely]}`.
- **Anyagok:** `<csoport>_<fajta>` (fajta = previs-paletta: drive narancs, frame/susp grafit, v8 acél, tyre, rim, panel piros, panel2 fehér …); a burkolaté `karosszeria_*` → a röntgen ezeket teszi átlátszóvá.
- **Klipek** (mind hurok, a kinematika képkockánkénti mintavétele, TRS-sávok csak a mozgó elemekre):
  | klip | hossz | mi mozog |
  |---|---|---|
  | `gurulas` | 18 s | 2. fokozat, 15 kerékfordulat = 49 főtengely-fordulat (49/15 = 5,444·0,6) → pontosan záródó hurok; kerekek, féltengelyek, diffek, kardánok, váltó, V8 főtengely + hajtórudak + dugattyúk (120 elem) |
  | `rugozas` | 6 s | 0–2 s első ±14 mm + hátsó ±6 mm együtt; 2–6 s keresztbe csuklás: első ellentétes ±14 mm, hátsó híd ±9° (103 elem, a rugók skálázva) |
  | `kormanyzas` | 4 s | tetőkormány → oszlop, 2 kardán → pinion → léc → kerekek, ±S_MAX (28 elem) |
  | `valtas` | 10 s | 1 → 2 → 3 → N → 1: tetőgomb 4×90°, választók, gyűrűk (hiszterézissel, mint a seq2-ben); a főtengely a kapcsolt áttétellel integrálódik, N-ben áll; kerék 0,5 ford/s. Hurokzárás: az 1. fokozat szakaszán −0,6 % sebesség-korrekció. Fokozat-időpontok: `parts.json → gear_marks` (a nézegető kijelzi) |
  | `robbantas` | 6 s | a previs E_robbantas vektorai: szét 1,8 s, tart, vissza (485 elem) |
- **Nézegető** (`assets/js/viewer.js`): klip-gombsor, lejátszás/szünet, idővonal, sebesség (0,25–2×), röntgen-kapcsoló, robbantás-csúszka (ugyanazok a vektorok), részegység-lista (név = kiemelés: a többi szellemkép; szem = elrejtés; hover = fény), alkatrész-info (LDraw-név, cikkszám, elemnév). Robbantásnál a kamera finoman hátrébb áll. Automatikus lejátszás (gurulás), kivéve `prefers-reduced-motion`. `el._viewer.state()` az ellenőrzéshez.
- **Ellenőrzés:** `tools/check_model.js` (Playwright, SwiftShader): betöltés, mind az 5 klip halad, fokozat-kijelző 1./2./3./N, alkatrész-info; képek `_check/model_*.png`. A fej nélküli szoftveres GL csak ~1–6 kép/s – valódi GPU-n folyamatos.
- Régi (makett-alapú) modell: `_check/model_prev/`.

## VEM GLB formátum
Egy mesh / egy primitive, mm, +Y fel: `POSITION` = deformálatlan felület; `COLOR_0` = feszültségszín a `cases.json` `scale` skálájával (grafitkék → kék → türkiz → homok → narancs); `_STRESS` = von Mises MPa csúcsonként; **morph target 0** = valós elmozdulás mm-ben (súly 1 = valós, a csúszka 0–5×). `mesh.extras {case, vmin, vmax, umax_mm}`.
`cases.json` eset: `{id, file, demo, title{hu,en}, desc{hu,en}, load{hu,en}, vmin, vmax, umax_mm, hand, deviation_pct, note{hu,en}}` – a `hand` (kézi számítás, MPa) és `deviation_pct` most `null` („folyamatban").
Generálás: `tools/build_fem.py` (VTU-ból: `von Mises [MPa]` + `u` pontadat).

## Szkriptek (`site/tools/`)
`build_anim_glb.py` (mozgó truck.glb + parts.json; a régi `build_model.py` csak a helyőrzőhöz), `build_fem.py` (fem/*.glb + cases.json), `build_data.py` (bom, calc, library + bélyegképek, ábrák, hero), `build_naplo.py`, `check_model.js` (a 3D-modell klipjei), `check.js` (Playwright: `NODE_PATH=/opt/npm-tools/node_modules node tools/check.js`, előtte `python3 -m http.server 8765`). README.md: HU+EN cserélési útmutató.

## Nyitott / következő
1. Végleges truck.glb (összeállítás után) + animációs klipek; 2. film.mp4 + VTT, hero.mp4; 3. VEM-esetek kézi számítással; 4. Trophy truck BOM; 5. napló frissítése a leadás előtt; 6. feltöltés GitHubra + Pages bekapcsolása; 7. a valódi Pages-URL-en egy utolsó check.js-futás.
