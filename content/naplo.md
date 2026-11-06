# Projektnapló – AI Kihívás

> Mit, milyen eszközzel, milyen prompttal csináltunk; hol akadtunk el, és hogyan jutottunk túl rajta.
> Jelölés: 🤖 AI végezte · 🧑 emberi beavatkozás · ⚠️ elakadás · ✅ megoldás

## Eszközök
| Eszköz | Mire |
|---|---|
| Claude (Cowork) – „karmester" chat | Tervezés, döntés-előkészítés, ágensek vezénylése, MCP-vezérlés |
| Claude projekt-dokumentumok | Közös memória a chatek és ágensek között (állapot, döntések, jelentések) |
| Claude al-ágensek és háttér-munkafolyamat (workflow) | Párhuzamos és sorba kötött munka: kutatás, Python-modellek, CAD-körök, render |
| SOLIDWORKS 2023 + 0xFFD/solidworks-mcp v0.2.0 | Az AI ezen keresztül modellez: könyvtár, részegységek mozgó kényszerekkel, motion study |
| Python: numpy, scipy, shapely, trimesh, manifold3d | Kinematika, ütközés- és rögzítésvizsgálat, saját STEP- és glTF-író |
| LDraw alkatrész-könyvtár | Valós Technic-geometria: furattípusok, fogprofilok, illesztési próbák |
| gmsh + CalculiX + PyVista; saját 3D gerendamodell | Végeselem-számítás (alkatrészek), létrakeret-számítás (807 csomópont) |
| Blender 4.5 (felhő + a saját gép GPU-ja) | Previs, mérnöki snittek, végleges film |
| Piper TTS, ffmpeg | Gépi magyar narráció, vágás és hangkeverés |
| three.js, gltfpack, Playwright | Mozgó 3D a weben, tömörítés, automatikus böngészős ellenőrzés |
| GitHub Desktop + GitHub Pages | Forráskód és nyilvános weboldal |

---

## 2026-11-03 (kedd) – Indítás és tervezés

**🤖 Témajavaslatok és eszközválasztás**
- Prompt (ember): *„Leírtam pontosan a projekt lényegét… Szeretnék valami tuti cuccot csinálni, mivel mérnök vagyok, ilyen minőségben is."*
- Az AI témákat javasolt (bolygómű, PU-s alkatrész, hobbi), és rákérdezett a 3D-s tapasztalatra.
- 🧑 Döntés: a 3D modellt **az AI-nak kell elkészítenie MCP-n keresztül**, SolidWorksben.

**🤖 Munkamódszer: karmester + ágensek**
- Prompt (ember): *„Tudsz-e chateket nyitni egy projekten belül, majd utasításokat kiadni ezeknek a chateknek? Fel kéne építeni egy stratégiát… Fontos, hogy a task célja, hogy mindent az AI csináljon."*
- ⚠️ Korlát: az AI nem tud új chatet nyitni és azoknak üzenni.
- ✅ Megoldás: a karmester chat al-ágenseket indít; a projekt-dokumentumok (00–09 briefek) közös memóriaként működnek.
- 🤖 Elkészült: `00_strategia.md` (fázisok, ütemterv, kockázati mátrix).

**🧑🤖 Témaválasztás – vita az AI-jal**
- 🧑 Három ötlet: (1) LEGO Technic autó, (2) alkatrész-fejlesztés egy E39 BMW-hez, (3) teljes váltótervezés.
- 🤖 Az AI pontozta őket (MCP-vel modellezhető, mérnöki mélység, látványosság, időkeret, hitelesség), és a 2-est javasolta.
- 🧑 Ellenvetés: *„a laikus zsűri nem értené a mélységét"*. Az AI elfogadta, és LEGO + váltó hibridet javasolt.
- 🧑 Ellenvetés: *„6 fogaskerék LEGO-ban nem izgalmas… egy LEGO autóhoz az embereknek kötődésük van"*.
- ✅ **Döntés: LEGO® Technic-kompatibilis autó** igazi mérnöki tervezési folyamaton végigvezetve. Személyes szál: gyerekkori LEGO-építés, a 8 éves fiam.
- 💡 Tanulság: az AI javaslata jó kiindulópont volt, de a célközönség ismerete az emberi oldalon volt.
- 🤖 Elkészült: `01_specifikacio.md`.

**🤖 SolidWorks MCP kiválasztása és biztonsági átnézése**
- 🤖 Az AI 6 közösségi SolidWorks MCP szervert hasonlított össze.
- ⚠️ Az elsőként kinézett (Slacker-LLC) repó közben eltűnt a GitHubról.
- ✅ Választás: **0xFFD/solidworks-mcp** (114 eszköz, fogaskerék- és fogasléc-kényszer, motion study, robbantott nézet).
- 🤖 Az AI a céges gép miatt átnézte a forráskódot: nincs hálózati hívás, és a szerver csak a munkamappába ír. Egy konkrét, átnézett commitot rögzítettünk.
- 🤖 Elkészült: `02_mcp_telepites.md`.

**🧑 Telepítés – a „három konfigurációs fájl" kalandja**
- 🧑 Telepítés PowerShellben (venv + pip), a `solidworks-mcp install` beírta a konfigurációt.
- ⚠️ 1. elakadás: az AI által adott JSON-t PowerShellbe illesztettem → szintaxishiba. ✅ Az AI kész PowerShell-szkriptet adott, ami biztonsági mentéssel, a meglévő beállítások megtartásával írja a fájlt.
- ⚠️ 2. elakadás: az app továbbra sem látta a szervert. Diagnózis: **Microsoft Store-os Claude** → virtualizált AppData. ✅ Oda is beírtuk – de még mindig semmi.
- ⚠️ 3. elakadás: MCP-napló sehol → az app meg sem próbálta indítani. Képernyőkép a Settings → Developer oldalról: „No servers added".
- ✅ Megoldás: az **Edit config** gomb megmutatta a valódi helyet: `AppData\Local\Claude-Data\…`. Az AI összefésülő szkriptet írt, ami ellenőrzi, hogy az app ki van-e lépve (különben felülírná a fájlt).
- 💡 Tanulság: az AI nem lát rá a gépre – a diagnózis az ember „szemén" (kimenetek, képernyőképek) keresztül ment. A kérdezés sorrendje (konfig → Store → napló → UI) módszeres hibakeresés volt.

**🤖 Füstteszt – az AI először modellez SolidWorksben**
- Kapcsolat: SOLIDWORKS 2023, MCP 0.2.0, munkamappa `AI challange\cad`.
- 🤖 5 lyukú Technic gerenda: hornyos (slot) vázlat Ø4,8 lyukrácssal, 7,2 mm szimmetrikus kihúzás. Ellenőrzés kézi számítással: várt térfogat ≈ 1300,4 mm³, SolidWorks: 1300,6 mm³ ✓
- ⚠️ STEP-export hiba: a szerver a SW 2026 API-jára íródott, a 2023-ban nincs `GetMBDSTEP242Data`. ✅ STEP AP214-re váltva működik.
- 🤖 Mini összeállítás: 2 gerenda + csap. Kényszerek: síkillesztés, 2× koncentrikus, távolság, szöghatároló (csukló 0–120°). Ütközésvizsgálat: 0 ✓
- ⚠️ A távolság-kényszer először rossz irányba tolta a csapot (z = 5,0 a várt 3,6 helyett). ✅ Az AI a komponens-pozíciók lekérdezésével észrevette, törölte és fordított iránnyal újra felvette.
- 💡 Tanulság: az AI „vakon" dolgozik a CAD-ben – minden lépés után számmal (térfogat, pozíció, ütközés) és képernyőképpel ellenőriz.
- Fájlok: `cad\smoke\` (beam5, pin2, hinge_test + PNG-k)

**🧑 GitHub-fiók**
- 🧑 Fióknév-ötletelés az AI-jal (R&D-szójátékok) → `PoResearch-and-deploy`. A repót (`ai-engineered-car`) én hozom létre – nyilvános repót az AI biztonsági okból nem hozhat létre helyettem.

**🤖 Párhuzamos ágensek: számítás és videó-forgatókönyv**
- 🤖 Számítási ágens (~17 perc, ~230k token): Technic-méretek forrásokkal, 114 tételes BOM valós cikkszámokkal, elrendezés, kormánygeometria (Ackermann-trapézzal 9,3° → 0,9° hiba), hajtáslánc, rugózás, és a „mikor csavarodik el a tengely?" (2D Prandtl-megoldás: a kereszt-szelvény a teli kör csavarási merevségének 16,5%-a; PF XL motornál biztonsági tényező ≈ 1,0).
- 🤖 Videó-ágens (~6 perc): 2:28-as forgatókönyv 11 jelenettel, magyar gépi narráció (Piper TTS) – ⚠️ a Hugging Face a proxyn tiltva → ✅ a hangmodellek egy GitHub-kiadásból.
- ⚠️ Az ágenseket „előtérben" indítottam, így 17 percig nem tudtunk beszélni. ✅ Megoldás: háttérben futó munkafolyamat (workflow).

**🧑 Fontos fordulat: „előbb beszéljük át, aztán indíts"**
- ⚠️ Az AI rákérdezés nélkül indított egy 10 ágenses éjszakai munkafolyamatot (CAD-könyvtár + web + render + VEM).
- 🧑 *„Fontos lenne a jövőre nézve, hogy mielőtt folyamatot indítasz, szólj… Több 10 ezer alkatrész van, lehet, hogy elfogy a keretem."*
- ✅ A felhős ágenseket leállítottuk (a célt még nem tisztáztuk – újra kellett volna csinálni), csak a CAD-lánc fut tovább, szűkítve a BOM elemeire. Új szabály: minden indítás előtt terv + jóváhagyás.
- 💡 Tanulság: az AI hajlamos „előremenekülni"; a költség és a cél kontrollja emberi feladat.

**🧑🤖 Alkatrészkönyvtár – 2. kör tervezése**
- 🧑 Prioritás: mechanika (fogaskerekek mind, differenciál, csuklók), sok kötőelem és vázelem, kevés kerék, mértékkel burkolat.
- 🤖 Az AI ~80 alkatrészes listát állított össze csoportokra bontva; minden cikkszámot az ágens webes forrással ellenőriz.

**🧑🤖 Látványterv – két kör**
- 🤖 v0.1: terepes buggy (vektoros koncepció kódból: Python → SVG, 3D primitívek saját vetítéssel).
- 🧑 *„Egészen más kéne. Menjünk a nagy truckok irányába… nagy rugóút, magas hasmagasság, összkerékhajtás."* → az AI három versenyautó-típust ajánlott (Monster truck / Trophy truck / Ultra4).
- ✅ Döntés: **Trophy truck** (Baja-típus). v0.2: hosszú motorháztető, nyitott plató pótkerékkel, elöl független hosszú lengőkarok, hátul merev híd, kerekenként 2 lengéscsillapító, összkerékhajtás, Ø≈62 mm terepgumi, tengelytáv 24 modul.
- ⚠️ Mellékhatás: a korábbi elrendezés és a kerékméret (30–40 mm) elavult → a 2. CAD-kör kerékcsoportját Ø55–70 mm-re írtuk át, a merev híd elemeit felvettük.

**🤖 Alkatrészkönyvtár – kész (éjszakai ágenslánc)**
- 1. kör (BOM-alap): 40 alkatrész, ~35 perc, ~0,93 M token; 2. kör (bővített): 59 alkatrész, ~89 perc, ~1,8 M token. Minden cikkszám webes forrással ellenőrizve – az ágens két AI-tévedést is kijavított (24T kerék BrickLink-száma 3648; az 5×11-es keret 64178).
- 🧑 Kiegészítő lista a felhasználótól (LEGO design ID-k) + Toypro mint forrás → K3 (10 elem), majd K4 váltó- és V8-elemek.
- ⚠️ A kontaktlapon gyanúsnak tűnt a 32009 dupla hajlított gerenda – kiderült: a szög jó volt, egy süllyesztett lyuk hiányzott.

**🧑🤖 Döntések egy este alatt**
- Csak digitális; motor nincs, a kerekek hajtanak egy dugattyús V8-at; 3+N szekvenciális váltó; „hand of god" tetőkormány; teljesen digitális videó gépi narrációval; Apple-szerű sötét weboldal HU/EN.
- 🧑 *„Nem éri meg saját váltót tervezni?"* → félreértés tisztázása: „saját konstrukció Technic-elemekből". 🤖 Benchmark-kutatás (42110 Defender, 42083 Bugatti): egyik sem fér a váltótérbe → marad a saját 3+N.

**⚠️ Kuplung, ami nem kapcsolt – három kör**
- K4: a kapcsológyűrű bordái szélesebbek, mint a kerék hornya → K5: horony szélesítése → az illeszkedési próba szerint **még mindig nem kapcsol** (0 mm benyúlás).
- ✅ K6: az LDraw-geometria alapos elemzése megmutatta, hogy **nem a belső bordák kapcsolnak, hanem a hüvely külső fülei** a kerék mélyedésének blokkjai közé. Újramodellezés után 3 állásban (bal / üres / jobb) 0 ütközés, 1,7 mm kapcsolódás.
- 💡 Tanulság: az illeszkedési próba (mini-összeállítás + ütközésvizsgálat) nélkül ez csak az összeállításnál derült volna ki.

**⚠️ Az ágensek „túl óvatosak" lettek**
- A CAD-javító ágens kétszer megtagadta a futást: a projekt-memóriában tárolt szabály („indítás előtt jóváhagyás") miatt, mert a felhasználó legutóbbi üzenetében nem látta a jóváhagyást.
- ✅ Megoldás: a felhasználó a chatben szó szerint megerősítette, és a promptokba a jóváhagyás szövegét is idézzük.
- 💡 Tanulság: a memóriába írt szabályt az ágensek komolyan veszik – ez jó, de pontosan kell kommunikálni.

**🤖 Megvalósíthatóság és digitális makett**
- VEM-lánc (gmsh + CalculiX + PyVista) működik; render: Eevee 720p ~15–18 s/kép, Cycles ~41 s/kép (2 CPU-mag) → a filmhez Eevee.
- Makett v2.2 (Python, CAD nélkül): 8 mm-es rács, alkatrész-transzformációk, kinematika, 38 ellenőrzés (34 ✓). Talált hibák: a V8 ütközik a kormányoszloppal (→ oszlop kerülővel), egy „0° kormányszög" hamis találat volt (a nyomtávrúd a saját fogaslécével ütközött a számításban).
- ⚠️ 22:00 körül a munkamenet újraindult, a futó ágensek elvesztek → ✅ átadó dokumentum (00_allapot.md) + folytató újraindítás a részeredményekből.

## 2026-11-04 (szerda) – Éjszakai munka

**🤖 SolidWorks-összeállítás (23:10–03:46, ~4,7 óra, ~3,7 M token, 10 ágens egymás után)**
- Modellfa: TT_000 fő-összeállítás → TT_100 váz, TT_200 első futómű (210 bal / 220 jobb), TT_300 kormányzás, TT_400 hátsó híd, TT_500 hajtáslánc, TT_600 váltó, TT_700 V8, TT_800 karosszéria, TT_900 kerék + al-részegységek (rugóstagok, kardán, CV). **223 komponens**, natív SLDASM + STEP, robbantott nézetek (minden alkatrész), részegység-kiemelés.
- Ellenőrzés részegységenként: kényszerek, kulcspontok ±0,3 mm a maketthez, ütközés, mozgásteszt, képernyőképek.
- ⚠️ Korlátok: az MCP nem tud „flexible" részegységet → a teljes kerék→V8 mozgás csak részegységenként ellenőrizhető; a differenciál működése mate-ekkel nem szimulálható.
- ⚠️ Talált problémák: a váltó 32 mm-rel magasabb a tervezettnél (átszúrja a fülketetőt), első kerék ↔ lengőkar-végek, ajtópanel ↔ hátsó rugóstag, V8-hengerek ↔ vázoszlop, könyvtári hibák (rugó belső Ø, CV-kehely horony, váltóvilla horony).
- ✅ K7: a könyvtári hibák _v2 javítása (rugó, CV-kehely 39,5°-ig ütközésmentes, villa).

**🤖 VEM – 4 eset (CalculiX)**
- Lengőkar 5 g földet érés: 6,0 MPa, biztonsági tényező 6,7 · féltengely csavarása (kerék megakad): 22,1 MPa, a 3D VEM és a 2D Prandtl 1,4%-on belül, BT 1,8 · fogtő a váltó 3. fokozatában: Lewis 20,5 vs VEM 20,2–23,8 MPa, BT 1,7–2,0 (a leggyengébb pont) · létrakeret csavarómerevsége 14,3 N·mm/fok (egy 9L tengellyel 2,4×).

**🤖 Videó és animáció**
- Forgatókönyv v2: 2:28, 11 jelenet, teljesen digitális, gépi narráció újragenerálva (kiejtési trükkök: „Szolidvörksz", „Teknik").
- Animációs pipeline (Blender, kódból számolt kinematika): 195 alkatrész, kerék → hajtáslánc → váltó → V8-dugattyúk, rugózás a terepből, Ackermann-kormányzás, robbantás + részegység-kiemelés. Teljes render szándékosan NEM (🧑 *„A renderhez menjünk biztosra, részleteket is beszéljük át."*).

**🤖 Weboldal-váz**
- Sötét, Apple-szerű, HU/EN, 3D-nézegető (robbantás, részegységek, animáció), interaktív VEM-nézegető (színskála + deformáció-csúszka), számítások, könyvtár, napló. Playwright-tal ellenőrizve asztalon és mobilon.

## 2026-11-04 (szerda) – Módszerváltás: kis lépések, Python a CAD előtt

**🧑 Reggeli átnézés: az éjszakai összeállítás nem jó**
- Az éjszakai 223 komponens látványos volt, de mérnökileg nem állta meg a helyét: lebegő alkatrészek, ütközések, és a mechanizmus nem mozgott együtt.
- 🧑 *„Menjünk kisebb lépésekben. Minden részegységet külön, első körben csak Python-kódban modellezzünk."*
- ✅ Új munkarend: **célzott kutatás → Python-modell → ellenőrzés (GO / NO-GO) → csak utána CAD**. Ez lett a projekt gerince.

**🤖 Kutatás részegységenként (R1–R4)**
- R1 első futómű, R2 hátsó híd, R3 hajtáslánc és kúpkerekek, R4 váltó + karosszéria: valós Technic-megoldások, gyári modellek, méretek és cikkszámok forrásokkal.

**🧑🤖 A1 – első futómű (Python, LDraw-geometriával)**
- 🧑 *„Elöl a 2-2 lengőkar nem jó… felül egy és alul 2/oldal már stabil."* és *„Távtartó nélkül."*
- ✅ Kettős keresztlengőkar: alul gerendás kar két vázbekötéssel, felül 57515 A-kar; kerékhordozó 65766 két gömbcsapon; rugóút ±16 mm, a féltengely csúszása a teljes rugóúton 0,00 mm. A belső kormányszög 17,7°, Ackermann ~132 % – tudatos kompromisszum, mert csak gyári elemekkel dolgozunk.

**⚠️ A1c / A2 – amikor a számítás nemet mond**
- A1c (első osztómű): a modell kimutatta, hogy a differenciál csapágyának **0,0 mm hely** maradt – a kardán homlokkal ért a diffházhoz. ✅ D2: a teljes sarok 4 mm-rel kifelé, közé egy 6632 gerenda mint csapágy; a kinematika változatlan.
- A2 (hátsó híd): a kutatás egyetlen 64179 keretet javasolt hídháznak, de a 12 fogú pinion tengelye az anyagon menne át. ✅ D3: **két 64179 féltengely-csőként**, 4-link gömbcsuklókkal, csúszó kardánnal; rugóút ~+9/−8 mm, csuklás ±11°.
- 🧑 *„A kúpkerekek osztóköre kapcsolódjon – ne homlokkerékkel közelítsd."* ✅ K8: LDraw-alapú kúpkerék-könyvtár, minden párra illesztési próba (fogbehatolás, forgásirány).

**⚠️ A4 – a 24 fogú kuplungkerék, ami nem létezik**
- A kutatás egy 24 fogú kuplungos kerékre építette a váltót. Az A4-modell ellenőrizte: ilyen elem nincs, csak 16 és 20 fogú.
- ✅ Új elrendezés három mellékhajtással; a fokozatsorrendet a 35188 választóelem LDraw-ból **kimért** peremprofilja adja (N, +, N, −). A V8 főtengelye a váltó kimenete.
- 🧑 *„A motor fordulata legyen állandó, és a kerék fordulatszáma változzon."* – a váltás-animáció logikája ennek megfelelően épült fel.
- 🤖 A3 (középső hajtáslánc): a középdiff helye a rácson kényszer – egyetlen 4 mm-es rácspont felel meg mindkét oldal feltételének.

**🤖⚠️ A5–A6 – animáció és részlettervezés**
- A5: ellenőrző animációk a teljes első futóműről és a teljes járműről, ütközésméréssel minden 5. képkockán.
- ⚠️ A6c: az LDraw furattípusainak beolvasása kimutatta, hogy több forgó tengely **keresztfuratban** ült volna – ott nem tud forogni. ✅ A lapok helye maradt, a típusuk kerek furatúra cserélődött; minden forgó tengelynek lett legalább egy valódi csapágya. Egy korábban elfogadott csere is hibásnak bizonyult – ezt a modell jelezte, nem az ember.
- A6a/b: rugóstag ↔ vázoszlop 0,05 mm-es hézagok feloldása (rugóstagok áthelyezése, gömbcsap megfordítása → 2,66 mm), rögzítési hiányok pótlása.

**🧑🤖 A7 – burkolat-változatok**
- Három változat a mozgási burkoló (rugózás × kormányzás × csuklás) ismeretében, kerék–karosszéria hézag ≥ 1,5 mm. ✅ Döntés: **V2 klasszikus Trophy truck**, piros-fehér, a pótkerék a plató végén.

## 2026-11-04 éjjel → 11-05 – CAD SolidWorksben, részegységenként

**🤖 Mozgó részegységek valódi kényszerekkel**
- 🧑 *„Mehet CAD-ben az egész autó."*
- C1 váltó: 40 komponens, fokozat-konfigurációk (N / 1 / 2 / 3), a motion study szerint az áttételek 1,000 / 0,600 / 0,333 ✓, a forgásirány mindhárom fokozatban azonos.
- C2 első futómű: kormányzás a tetőkormánytól a kerékig, rugózás, hajtás. C3 hátsó híd: 4-link gömbcsuklókkal, csúszó kardán. C4 váz: létrakeret + középső hajtáslánc fogaskerék-kényszerekkel.
- ⚠️ Az MCP `insert_component` nem tud forgatni. ✅ Python STEP-összefésülés: a könyvtári STEP-eket a jármű koordináta-rendszerébe transzformáljuk, a SolidWorks csak importál. Mellékes, de kemény tanulság: egy tizedespont nélküli szám a STEP-ben összeomlasztja az importot.

**⚠️ A SolidWorks befagyott**
- Egy komponens újrabeszúrása után az MCP nem válaszolt; az utolsó javítókör mentetlen maradt.
- 🧑 Fordulat: *„Gyorsabb lenne Pythonnal… aztán csak kiexportálni STEP-be?"*
- ✅ Döntés: **a teljes autó Pythonból készül STEP-be és mozgó glb-be** (az LDraw-geometriához mérve 0,00002 mm-es egyezéssel); a SolidWorks-részegységek a folyamat bizonyítékai és bemutatói.

## 2026-11-05 (csütörtök) – Ellenőrzés, weboldal, videó

**🤖 VEM a mostani létrakereten**
- Saját 3D gerendamodell a valós lyukközéppontokkal (807 csomópont, 641 elem, 214 kötés), a korábbi tömör VEM-re kalibrálva.
- ⚠️ Eredmény: 3 g-s földetérésnél az első segédkeret **9L tengelye a gyenge pont** (64 MPa > 40 MPa); a modell **2 hiányzó csapot** is talált a hossztartó és az oszlop között – nélkülük a csavarást egyetlen tengely viszi, a keret csavarómerevsége 3,8 N·mm/fok-ra esik. A csapok bekerültek a modellbe.

**🧑 Emberi átnézés: a teljes STEP SolidWorksben**
- 🧑 *„Sárvédő-gerendák nincsenek rögzítve… Sok-sok kötőelem hiányzik."*
- Az ütközésvizsgálat ezt nem fogta meg: ami lebeg, az nem ütközik.
- ✅ Rögzítési gráf az egész autóra: minden csap és tengely a furatában egy-egy él; merev csak az, ami kereszt-kötéssel vagy legalább két vonalon ül. **42 → 5 → 0 lebegő elem**, összesen 110 új tartó és kötőelem.
- 🧑 *„Inkább feljebb tenném az oldalpanelt, nem kijjebb."* → az ajtólap 28 mm-rel feljebb, saját tartóval; a hátsó pinion két csapágyat kapott.

**🤖 Mozgás és weboldal**
- CV-csukló és váltás-animáció javítása; mozgó 3D-modell a weben (kormányzás, rugózás, hajtás, robbantás), CAD-nézegető, VEM-nézegető, napló. Playwright-tal ellenőrizve asztalon és mobilon.
- Ráadás: **Próbaút** – egy kis böngészős játék a modellel.

**⚠️✅ GitHub**
- ⚠️ A Cowork-felhőből a git-proxy nem enged írni a repóba (ismert hiba). Egy hozzáférési token próbáját a biztonsági szabályok jogosan megállították.
- ✅ Megoldás: az oldal a saját gépre kerül, és **GitHub Desktop** tölti fel; **GitHub Pages** szolgálja ki.

**🤖🧑 Videó: previs → GPU → film**
- Previs a felhőben, majd a render átkerült a saját gépre: **GPU-n ~0,57 s/kocka, a felhőben ~15 s/kocka** – nagyjából 25-szörös különbség.
- Próbavideó → visszajelzés → narráció-csiszolás (rövidebb, szárazabb mondatok, homokpor, naplemente) → végleges film, 1920×1080, 24 fps.

**🧑🤖 Záró szekció: „A következő autó a tiéd."**
- 🧑 Ötlet: *„Mi a haszna ennek az egésznek? Az AI segítségével bárki megtervezheti a saját autóját… és promózhatnánk, hogy az AI összeállítja a rendelési listát és útmutatót csinál az építéshez."* Az első szövegváltozatot csiszoltabbra kérte – a végleges cím: **„Mire jó mindez? – A következő autó a tiéd."**
- 🤖 **Három koncepció** (versenyautó, nyerges vontató, autódaru) ugyanabból a 80 cikkszámos LDraw-hálókönyvtárból, kódból összerakva (80 / 77 / 127 elem), Blenderben a film TRON-stílusában renderelve, „Koncepció – nem végigtervezett" jelöléssel. Szándékosan gyors vázlatok: nincs bennük méretezés vagy ütközésvizsgálat.
- 🤖 **Működő rendelési lista:** a darabjegyzékből BrickLink-kívánságlista (XML) készült, 105 tétel, 588 elem, színekkel. ⚠️ Az LDraw- és a BrickLink-cikkszám nem mindig egyezik (pl. 32123a → 4265c, 3648 → 3648b); ahol biztos volt, átírtuk, a 8 kétséges tételt a lista és az oldal is jelöli. A rugóstag rugója kimaradt, mert egységként kapható. A színek a digitális modell színei.
- 🤖 **Építési útmutató-minta** a bal első kerékfelfüggesztésből, LEGO-útmutató-stílusban: 4 lépés, az alkatrész-keretben darabszámmal, az új elemek narancs kontúrral, nyíllal. ⚠️ Az első változatban a kerék eltakarta a nyomtávrudat → ✅ a lépések átcsoportosítva, a kerék külön lépésbe került.
- Playwright-tal ellenőrizve asztalon és mobilon, HU/EN: a képek betöltenek, az XML letölthető és érvényes.

## Tanulságok

1. **Kis lépések, és a Python bizonyít a CAD előtt.** Az éjszakai „mindent egyszerre" CAD látványos volt, de hibás. Részegységenként a Python-modell olcsón mondott nemet (0 mm csapágyhely, nem létező fogaskerék, keresztfuratban forgó tengely), mielőtt a CAD-ben drága lett volna.
2. **Az ütközés-ellenőrzés nem elég – rögzítés-ellenőrzés is kell.** Ami lebeg, az nem ütközik. A rögzítési gráf olyan hibát talált meg, amit minden korábbi ellenőrzés átengedett.
3. **Az emberi átnézés pótolhatatlan.** A legfontosabb hibákat (lebegő elemek, hiányzó kötőelemek) mérnöki szem vette észre a modellben; az AI ebből már gyorsan és módszeresen csinált ellenőrző eszközt.
4. **A CAD-MCP korlátai valósak.** Nincs flexible részegység, a beszúrás nem forgat, egy beragadt hívás befagyasztja a munkamenetet. A hibrid út – a geometria Pythonból, a mozgó bemutató SolidWorksben – megbízhatóbbnak bizonyult.
5. **A renderelés helye számít.** Ugyanaz a jelenet a saját GPU-n ~25-ször gyorsabb volt, mint a felhőben; a nehéz számítást oda kell vinni, ahol a hardver van.
6. **A jóváhagyási szabálynak ára és haszna is van.** Lassította az éjszakai munkát, és az ágensek néha túl óvatosak lettek – cserébe minden költséges lépés előtt volt egy tudatos emberi döntés, és nem futottunk el rossz irányba.

## Röviden számokban

| | |
|---|---|
| Elemszám | **592 elem**, 80 különböző cikkszám |
| Részegységek | váz, első futómű + kormányzás, első osztómű, hátsó híd, középső hajtáslánc, 3+N váltó, V8, karosszéria, kerekek |
| Lebegő elemek | 42 → 5 → **0** |
| Film | ~1:53, 1920×1080, 24 fps, 2724 kocka; GPU-n ~0,57 s/kocka |
| Weboldal | https://poresearch-and-deploy.github.io/ai-engineered-car/ |
| Forráskód | https://github.com/PoResearch-and-deploy/ai-engineered-car |
