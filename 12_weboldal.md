# 12 – Weboldal (váz, 2026-11-03)

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

## truck.glb – csomópont-konvenció (az animációs/CAD-export ágens ehhez igazodjon)
- Tengelyek: **+X előre, +Y fel, +Z jobbra** (a makett x előre / y balra / z fel rendszeréből: (x,y,z) → (x, z, −y)). Egység mm, gyökér `truck` csomópont `scale 0.001`.
- Csoportok: `G_vaz`, `G_elso_futomu` (bal/jobb futómű, első diff, kormány), `G_hatso_hid`, `G_hajtaslanc` (kardánok, középdiff, váltó), `G_V8`, `G_karosszeria`, `G_kerekek`; extras `{"group": "<id>"}`. A kapcsolók ezek `visible`-jét állítják; nevük/színük `parts.json` → `groups`.
- Alkatrészek: `P_<cikkszám>_<nn>` (pl. `P_44771_03`), extras `{"group","partno","design_id","name"}` → info-kártya. A robbantott nézet ezeket (és a kerékpivotokat) tolja a csoport- és a modellközéppontból kifelé.
- Kerekek: pivot `W_FL, W_FR, W_RL, W_RR` a kerékközépen; alatta gumi + felni; forgás helyi **+Z** körül (előremenet = −Z irány).
- Animáció: tetszőleges számú glTF-klip, név szerint listázva (most: `wheels_spin`, 2 s). Ha nincs klip, a nézegető demó kerékforgást generál. Javaslat a végleges modellhez: `drive` (kerekek + kardán + V8 dugattyúk), `steer`, `suspension`, `gearshift`.
- Ajánlott méret < 10 MB (tömörítés nélkül; DRACO-dekóder nincs beépítve).

## VEM GLB formátum
Egy mesh / egy primitive, mm, +Y fel: `POSITION` = deformálatlan felület; `COLOR_0` = feszültségszín a `cases.json` `scale` skálájával (grafitkék → kék → türkiz → homok → narancs); `_STRESS` = von Mises MPa csúcsonként; **morph target 0** = valós elmozdulás mm-ben (súly 1 = valós, a csúszka 0–5×). `mesh.extras {case, vmin, vmax, umax_mm}`.
`cases.json` eset: `{id, file, demo, title{hu,en}, desc{hu,en}, load{hu,en}, vmin, vmax, umax_mm, hand, deviation_pct, note{hu,en}}` – a `hand` (kézi számítás, MPa) és `deviation_pct` most `null` („folyamatban").
Generálás: `tools/build_fem.py` (VTU-ból: `von Mises [MPa]` + `u` pontadat).

## Szkriptek (`site/tools/`)
`build_model.py` (truck.glb + parts.json), `build_fem.py` (fem/*.glb + cases.json), `build_data.py` (bom, calc, library + bélyegképek, ábrák, hero), `build_naplo.py`, `check.js` (Playwright: `NODE_PATH=/opt/npm-tools/node_modules node tools/check.js`, előtte `python3 -m http.server 8765`). README.md: HU+EN cserélési útmutató.

## Nyitott / következő
1. Végleges truck.glb (összeállítás után) + animációs klipek; 2. film.mp4 + VTT, hero.mp4; 3. VEM-esetek kézi számítással; 4. Trophy truck BOM; 5. napló frissítése a leadás előtt; 6. feltöltés GitHubra + Pages bekapcsolása; 7. a valódi Pages-URL-en egy utolsó check.js-futás.
