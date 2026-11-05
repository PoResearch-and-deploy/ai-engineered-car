# Projektnapló – AI Kihívás

> Mit, milyen eszközzel, milyen prompttal csináltunk; hol akadtunk el, és hogyan jutottunk túl rajta.
> Jelölés: 🤖 AI végezte · 🧑 emberi beavatkozás · ⚠️ elakadás · ✅ megoldás

## Eszközök
| Eszköz | Mire |
|---|---|
| Claude (Cowork) – „karmester" chat | Tervezés, vezénylés, ágensek indítása, MCP-vezérlés |
| Claude projekt-dokumentumok | Közös memória a chatek/ágensek között |
| Claude al-ágensek és háttér-munkafolyamat (workflow) | Párhuzamos munka: számítás, forgatókönyv, CAD-könyvtár |
| 0xFFD/solidworks-mcp v0.2.0 | Az AI ezen keresztül vezérli a SolidWorkst |
| SOLIDWORKS 2023 | CAD |
| Python (matplotlib, saját SVG-vetítés), Piper TTS, Playwright | Számítások, látványterv, narráció, ellenőrző képek |

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
