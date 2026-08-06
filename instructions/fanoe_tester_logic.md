**FÁNOE tesztműszer project**  
Adafruit CircuitPython 10.1.4  

Board: ESP32-S3 Super Mini  
machine='Waveshare ESP32-S3-Zero with ESP32S3'  
https://circuitpython.org/board/makergo_esp32c3_supermini/  
Fw: https://circuitpython.org/board/waveshare_esp32_s3_zero/  

Hardver:
- ESP32-S3 (QFN56) (revision v0.2)  
A Super Mini panelen kivezetett GPIO-k száma: 18  
Board: ESP32-S3 Super Mini (lásd instructions/esp32s3supermini_instructions.md  
a hardver-specifikus részletekért, klón-board/pin-eltérésekért)  
Fw: https://circuitpython.org/board/waveshare_esp32_s3_zero/
(nincs dedikált Super Mini build, lásd fenti fájl "Board Identity Caveat" pontja)  
Board ID: waveshare_esp32_s3_zero, UID: c3f0202e6b4a  
  
- Billentyűzet: 3x2 mátrix - PROTECTA TAST-5V P283
- Kijelző: 2.25" TFT szines 76*284 - ST7789 vezérlővel  

```
************ KAPCSOLÁSI RAJZ ******************

                      TÁPFESZÜLTSÉG
PullUp resistors          REPL
   on the PCB              ↓
     ↓                   USB-C                  2.25" SPI TFT
          K           ┌────┬──┬────┐      ┌──────────────────────────┐
    5,6k -E--Column1-─┤IO1 └──┘IO13├──────┤SCL                      +├─ 3V3
    5,6k -Y--Column2-─┤IO2     IO12├──────┤SDA                      -├─ GND  
    5,6k -P--Column3-─┤IO3     IO11├──────┤RST      ST7789SP3        │  
          A ── Row1-──┤IO4     IO10├──────┤DC                        │   
          D ── Row2-──┤IO5     IO9 ├──────┤CS         76*284         │   
                      │        IO8 ├──────┤BL                        │ 
 [ENTER] [LEFT] [UP]  │            │      └──────────────────────────┘
 [ESC] [RIGHT] [DOWN] │  ESP32-S3  │  
                      │ Super Mini │  3V3
                      │            │  ┌┴┐
 NO Contact->-DigIn ──┤IO6         │  │ │150     
                      │            │  └┬┘ 
    Relay-<-DigOut--──┤IO7    *IO14├───┴──-<---[Rx]---GND
                      └────────────┘
```

************ Directory and file structure ************

/media/*user*/CIRCUITPY/lib  
|  
+-- /adafruit_bitmap_font  
+-- /adafruit_display_text  
+-- adafruit_st7789.mpy  

/media/*user*/CIRCUITPY  
|  
+-- boot.py  (handles change between user/developer mode a programból történő fájlírás kezeléséhez)  
|   
+-- code.py  (Main code, csak a boot.py után fut le)  
|  
+-- menu_data.py (menu struktúra adatfájl)  
|  
+-- settings.toml (a code.py hozza létre/írja és olvassa)  
|  
+-- tft_messages.py (központi kijelző üzenet szótár)  

```
******************* Boot sequence *******************

             +------------ 1. -----------+
             |      Rendszerindulás      |
             |   (Reset / Bekapcsolás)   |
             +-------------+-------------+
                           |
                           v
                 +-------- 2. ------+
                 |      boot.py     |
                 +---------+--------+
                           |
         GPIO39 olvasás: switch.value (HIGH/LOW)
                           |
         +-----------------+-------------------+
         |                                     |
        LOW (GND)                      HIGH (nem GND)
         |                                     |
         v                                     v
+--------+-------------------+         +-------+------+
| storage.disable_usb_drive()|         | nincs teendő |
|         fut le             |         +-------+------+
+-------------+--------------+                 |
              |                                |
              v                                v
+-------------+--------------+    +------------+--------------+
| KÖRNYEZET: FELHASZNÁLÓ MÓD |    | KÖRNYEZET: FEJLESZTŐI MÓD |
|  - USB meghajtó INAKTÍV    |    |  - USB meghajtó AKTÍV     |
+-------------+--------------+    +------------+--------------+
              |                                |
              v                                v
              |                                |
              +----------------+---------------+
                               |
            switch.deinit()  GPIO39 felszabadítása
                               |
                     +---------v-------------+
                     | USB meghajtó állapota |
                     | (látható/nem látható) |
                     +-----------------------+
                               |
                               v
                 +-------------3.------------+
                 |          code.py          |
                 |       (Fő program)        |
                 +-------------+-------------+
                               |
                        [A program fut]
                               |
                               v
          +--------------------+-----------------------+
          | Felhasználó a menüből MENTENI/TÖRÖLNI akar |
          +--------------------+-----------------------+
                               |
                               v
    +-------------------------------------------------------+
    |  Függvényhívás: pl. save_credentials()                |
    |  - lefut a storage.remount("/", False) parancs        |
    +--------------------------+----------------------------+
                               |
+------------------------------v--------------------------------+
|    A 'remount' parancs EREDMÉNYE a KÖRNYEZETTŐL függ:         |
|                                                               |
|  +-------------------------+      +------------------------+  |
|  |  FELHASZNÁLÓI MÓDBAN    |      |   FEJLESZTŐI MÓDBAN    |  |
|  | (USB meghajtó inaktív)  |      | (USB meghajtó aktív)   |  |
|  +-------------------------+      +------------------------+  |
|  | - SIKERES fájlírás      |      | - SIKERTELEN fájlírás  |  |
|  |   -> Írási jogot a      |      |   -> Exception:        |  |
|  |      program megkapta   |      |   -> "Cannot remount..."  |
|  |            |            |      |            |           |  |
|  |            v            |      |            v           |  |
|  | pl. a 'settings.toml'   |      |        Hibaüzenet      |  |
|  | fájl sikeresen          |      |   A fájlművelet nem    |  |
|  | létrejön/felülíródik    |      |   hajtódik végre       |  |
|  |                         |      |                        |  |
|  | - REPL működik          |      | - REPL működik         |  |
|  +-------------------------+      +------------------------+  |
|                                                               |
+---------------------------------------------------------------+   
```  
```  
******************* Menü struktúra **** vázlat ****** menu_data.py *********

|       FŐMENÜ       |      almenü         |     TFT 1. sor      |     TFT 2. sor     |
|-------------------22--------------------22--------------------23-------------------23
|ELLENÁLLÁS MÉRÉS ⏎  |      (nincs)        |Ohm-mérés üzemmód    |     xxx.x Ω        |
|                       ────────────────────────────────────────────────────────────
|FÁNOE KÉZI BE ▶     |      (nincs)        |FÁNOE behúzatás ⏎    |  csak nyomva aktív |
|                    |  ────────────────────────────────────────────────────────────
|FÁNOE BE/KI MÉRÉS ▶ |      (nincs)        |t_elo, t_bent, t_uto | Ciklus indítása  ⏎ |
|                    |  ────────────────────────────────────────────────────────────
|BEÁLLÍTÁSOK ▶       |FÁVA idő állítás ▶   |FÁVA holtidő ↑↓   ⏎  |     t_elo ms       |
|                    |Bent idő állítás ▶   |FÁNOE bent idő ↑↓ ⏎  |     t_bent ms      |
|                    |FÁNOE KI utóidő ▶    |KI utáni idő ↑↓   ⏎  |     t_uto ms       |
|                    |Ohm érték állítás ▶  |alsó Ω érték ↑↓   ⏎  |     r_ell Ω        |
|                    |Fényerő állítása ▶   |TFT fényerő  ↑↓   ⏎  |      9 / x         |
────────────────────────────────────────────────────────────  |       
|INFORMÁCIÓK ⏎       |CPU frekvencia ->    |ESP32-S3 CPU órajel: |   {freq} MHz       |
|                    |CPU hőmérséklet ->   |ESP32-S3 CPU hőfok:  |   {temp} °C        |
|                    |Használt memória ->  |Használt RAM memória |   {mem} KB         |
|                    |Szabad memória ->    |Szabad RAM memória:  |   {ram} KB         |
|                    |Foglalt tárhely ->   |Foglalt flash memória:   {flash} MB       |
|                    |Szabad tárhely ->    |Szabad flash memória:|   {flash} MB       |
|                    |Alaplap azonosító -> |Board azonosító:     |   {board_id}       |
|                    |Chip azonosító ->    |Chip típus azonosító:|   {uid}            |
|                    |Hardwer verzió ->    |Hardwer felépítés:   |   "ver.1.0 ✗"      |
|                    |CircutPython ver. -> |cPy firmware verzió: |   {fw.version}     | 
|                    |Software verzió ->   |Software verzió:     |   {VERSION}        |
|                    |https://github.com ->|github/veresgyuri/   |   fanoe-tester ☺   |
|                       ────────────────────────────────────────────────────────────  
|RESTART *.*  ▶ ⏎    |Sw. újraindítás ▶    |   biztos benne?     |  igen ⏎ | nem ESC  |
  
📋 ---Mozgás a menüben---
JOBB - egy szinttel beljebb
BAL - egy szinttel vissza
FEL - mozgás a menüben fel, vagy érték állítás fel (nem forog körbe)
LE - mozgás a menüben le, vagy érték állítás le (nem forog körbe)
ENTER - érték elfogadása, indítás, üzemmód váltás (pl. Ohm-mérés mód)
ESC - egy szintet vissza, hosszan nyomva (> 2mp) FŐMENÜ

**Megjegyzések:**
- A "(nincs)" jelzésű sorok nem jelennek meg a kijelzőn.  
- Aktív menü mutatása: eltérő szín + keretezés.
```  
******************* Automatikus mérési ciklus (FanoeMeasurementCycle) *******************  

**GPIO szerepek:**  
IO7  - DigOut   - FANOE relé vezérlése (behúzás/elengedés)  
IO6  - DigIn    - NO kontaktus, a FANOE érintkező tényleges állapotának visszajelzése  
IO14 - AnalogIn - FANOE belső ellenállásának mérése
                    
                    IO14 osztó: 3.3V -- 150R (referencia) -- [IO14] -- R_fanoe -- GND
                    R_fanoe = 150 * V_adc / (3.3 - V_adc)

**Konfigurálható paraméterek (settings.toml, "Beállítások" menü alól):**  
t_elo   [ms]   0-3000   - előkésleltetés a ciklus indítása és a relé behúzása között  
t_bent  [ms]   500-7000 - amíg a relé be van kapcsolva (IO7 = ON)  
t_uto   [ms]   500-5000 - utóidő a relé kikapcsolása és a ciklus vége között
r_ell   [Ohm]  70-150, alapérték 70 - küszöbérték az r_be/r_ki éldetektáláshoz  

**Fix, a kódban meghatározott (felhasználó által nem állítható) technikai konstansok:**  
T_SETTLE_MS = 150 ms - a fanoe_be után ennyit várunk, mielőtt figyelnénk, hogy a fanoe_ell érték stabil-e  
OHM_TOLERANCE  = 3 Ohm - a "stabil" (fanoe_ell zárolható) állapot Ohm-tűrése 3 egymást követő minta között  
ADC_SAMPLE_INTERVAL_MS  = 100 ms - az ellenállás-mintavételezés periódusa  

cycle_duration = t_elo + t_bent + t_uto  (MINDIG dinamikusan számolt érték, a mindenkori beállításokból)

```
Idővonal (t=0 a ciklus indításának pillanata):

  0             t_elo                  t_elo+t_bent                t_elo+t_bent+t_uto
  |--- T_ELO -----|------ T_BENT -----------|------------ T_UTO -----------|
               IO7: ON                   IO7: OFF         ciklus vége (STOP, feltétel nélkül)
                  |                         |                              |
              IO6 +-figyeli--> fanoe_be         fanoe_ki <-- IO6 figyeli --+
                  |                                                        |
                  +-------- IO14 (ADC) folyamatos mintavétel, 100ms -------+
                              (t_elo végétől a ciklus végéig fut)
```

### Állapotgép - FanoeMeasurementCycle osztály állapotai:

**Aktív állapotok: T_ELO, T_BENT, T_UTO**  
MINDEN aktív állapotban, a felhasználó ESC gombja AZONNALI és feltétel nélküli megszakítást vált ki:  
Semmilyen részeredmény (t_be, t_ki, fanoe_ell, r_be, r_ki) NEM kerül kiszámításra vagy tárolásra - nincs EVALUATE lépés ilyenkor.  
IO7 = OFF azonnal (biztonsági lekapcsolás, függetlenül az aktuális állapottól)  
Átlépés -> ABORTED 

- ABORTED
    - TFT-n megjelenik: "aborted_by_user" üzenetkulcs (-> tft_messages.py, "Mérés megszakítva, visszalépés ▶")
    - Kilépés:
      - felhasználó ESC -> vissza a főmenübe

- IDLE
    - Várakozás: IO7 = OFF. Semmilyen mérés nem fut.  
    - Kilépés:  
      - felhasználó ENTER az "Automatikus mérés" menüben -> start()  
      - felhasználó ESC -> vissza a főmenübe (menü navigáció, nem érinti a mérési logikát)

  T_ELO
    - Belépés: start() meghívva.
    - Indítás előtti ellenőrzés (biztonsági retesz):
      - A start() legelső lépéseként ellenőrizzük az IO6 állapotát.
      - Ha a kontaktus már az indítás pillanatában zárt (IO6 = LOW) -> ERROR_ALREADY_CLOSED állapot rögzítése, a ciklus normál indítása megszakad, nem húzzuk be a relét (IO7 = OFF), és azonnal a RESULT állapotba ugrunk.
      - Ha a kontaktus nyitott (helyes kiindulási állapot) -> cycle_start_time = most. IO7 = OFF.
    - Kilépés:
      - elapsed >= t_elo -> T_BENT
      - felhasználó ESC -> mérés megszakítva, visszalépés ▶

  T_BENT
    - Belépés: IO7 = ON. relay_on_time = most.
               IO14 mintavételi task elindul (100ms periódussal, a ciklus végéig fut).
    - IO6: az ELSŐ záródás -> fanoe_be_time rögzítve, t_be = fanoe_be_time - t_elo
           (ha T_BENT alatt nem történik záródás -> ERROR_NO_PULLIN jelzés,
            a ciklus NEM áll le emiatt)
    - IO6: Ha a kontaktus már sikeresen beépült (fanoe_be_time nem None), de a T_BENT fázis
           lejárta előtt (amíg a relé még aktív) a kontaktus visszanyit -> ERROR_PREMATURE_DROPOUT
           (korai elengedés hiba rögzítése, a ciklus nem áll le emiatt)
    - IO14: T_SETTLE_MS elteltével fanoe_be_time után figyeljük a stabilitást
            (lásd EVALUATE, fanoe_ell számítása)
    - IO14: párhuzamosan, EGYMÁSTÓL FÜGGETLENÜL figyeljük az r_ell küszöb
            ELSŐ átlépését fölfelé -> r_be_time rögzítve
            (ha nem történik meg, r_be = N/A, ez NEM hiba)
    - Kilépés:
      - elapsed >= t_elo+t_bent -> T_UTO
      - felhasználó ESC -> mérés megszakítva,  visszalépés ▶

  T_UTO
    - Belépés: IO7 = OFF. relay_off_time = most.
    - IO6: az ELSŐ nyitás -> fanoe_ki_time rögzítve,
           t_ki = fanoe_ki_time - relay_off_time
           (ha ciklus végéig nem történik meg -> ERROR_NO_DROPOUT jelzés,
            a ciklus NEM áll le emiatt)
    - IO14: továbbra is fut; figyeljük az r_ell küszöb UTOLSÓ átlépését lefelé
            -> r_ki_time rögzítve (ha nem történik meg, r_ki = N/A, NEM hiba)
    - Kilépés:
        - elapsed >= t_elo+t_bent+t_uto (= cycle_duration) -> EVALUATE
               (FELTÉTEL NÉLKÜL, függetlenül attól, hogy fanoe_ki/r_ki megtörtént-e)
        - felhasználó ESC ->  mérés megszakítva, visszalépés ▶

  EVALUATE  
  Számítás a gyűjtött adatokból:
  - t_be = fanoe_be_time - t_elo (vagy None, ha nem történt)
  - t_ki = fanoe_ki_time - (t_elo + t_bent) (vagy None, ha nem történt)
  - fanoe_ell = az első 3 egymást követő ADC-minta (T_SETTLE_MS után,
                    fanoe_be_time-tól számítva), amint |max-min| <= OHM_TOLERANCE
                    -> a legutolsó ilyen minta lesz a végleges érték, TÖBBÉ NEM frissül;
                    "szakadt", ha az ADC gyakorlatilag tápfeszültségen szaturál
  - r_be = r_be_time - t_elo                        (vagy N/A)
  - r_ki      = r_ki_time - (t_elo + t_bent)              (vagy N/A)
  - Kilépés:
      - automatikusan -> RESULT

  RESULT
    - TFT-n megjelenik: t_be, t_ki, fanoe_ell (vagy "szakadt"), r_be, r_ki (vagy "N/A"),
      valamint bármelyik ERROR_ALREADY_CLOSED / ERROR_PREMATURE_DROPOUT / ERROR_NO_PULLIN /
      ERROR_NO_DROPOUT jelzés, ha történt.
    - Ha ERROR_ALREADY_CLOSED történt, az összes mérési részeredmény automatikusan "N/A" lesz.
    - Egyik jelzés SEM állítja meg korábban az aktív mérést (kivéve az indítás előtti
      ERROR_ALREADY_CLOSED állapotot, amely megakadályozza a ciklus felesleges elindulását).
    - Kilépés:
        - felhasználó ESC -> vissza a főmenübe

### FANOE Mérési Ciklus Állapotmátrix és Hibavédelmi Táblázat

| Ciklusfázis / Időtartam | Vezérlés (IO7) | Fizikai kontaktus (IO6) várt állapota | Analóg Ohm-mérés (IO14) állapota | Lehetséges rendellenes esemény (Edge Case) | Szoftveres reakció / Hibajelzés |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Indítás előtti pillanat** | `OFF` | **Nyitott** (Pull-Up miatt HIGH) | Magas ellenállás / Szakadt | **Beragadt kontaktus:** Az IO6 már indítás előtt ZÁRT (`LOW`). | **Megszakítás:** `error_already_closed` flag beállítása. A relé *nem* húz be, a ciklus azonnal megszakad, a RESULT listában megjelenik: `HIBA: alapból zárva`. |
| **T_ELO** <br>*(Előkésleltetés)* | `OFF` | **Nyitott** marad | Magas ellenállás | **Peremfeltétel 1:** T_ELO alatt a kontaktus véletlenül bezár, majd el is ejt. | **Ignorálás:** Mivel a szoftver csak a `T_BENT` fázistól kezdi el érdemben figyelni a behúzási éleket, ez nem rontja el a `t_be` mérést. |
| **T_BENT** <br>*(Gerjesztési fázis)* | `ON` | **Záródnia kell** (IO6 átvált `LOW`-ra) | Stabil alacsony ellenállás (`< r_ell`, majd zárolódik `fanoe_ell`) | **A) Nem húz be időben:** T_BENT végéig nincs záró él. | **Hibajelzés:** `error_no_pullin` = `True`. A ciklus lefut végig, a RESULT listában: `HIBA: nem húzott be` és `t_be: N/A`. |
| **T_BENT** <br>*(Gerjesztési fázis)* | `ON` | Zárt állapot fenntartása | Stabil ellenállás (`fanoe_ell` zárolva) | **B) Korai elengedés:** Beépül (`fanoe_be` rögzítve), de a T_BENT lejárta *előtt* kinyit az érintkező. | **Hibajelzés:** `error_premature_dropout` = `True`. A ciklus lefut végig, a RESULT listában: `HIBA: korai elengedés`. |
| **T_BENT** <br>*(Gerjesztési fázis)* | `ON` | Zárt állapot | Az ellenállás az `r_ell` küszöb felett marad (`r_be_time` rögzítés) | **C) Érintkezési hiba / Magas átmeneti ellenállás:** Az IO6 zár, de az IO14-en mért ellenállás szakadást (`szakadt`) vagy magas értéket mutat. | **Mérés / Jelzés:** `fanoe_ell` = `szakadt` vagy valós magas érték. A ciklus lefut, a RESULT listában megjelenik a mért/szakadt érték (minősítést a kezelő végez). |
| **T_UTO** <br>*(Utóidő / Elejtés)* | `OFF` | **Nyitnia kell** (IO6 átvált `HIGH`-ra) | Megemelkedik az ellenállás (`> r_ell`) | **A) Nem ejt el időben:** A ciklus végéig (T_UTO lejárta) nincs nyitó él. | **Hibajelzés:** `error_no_dropout` = `True`. A ciklus lefut végig, a RESULT listában: `HIBA: nem ejtett el` és `t_ki: N/A`. |
| **T_UTO** <br>*(Utóidő / Elejtés)* | `OFF` | Nyitott állapot fenntartása | Magas ellenállás / Szakadt (`r_ki_time` rögzítés) | **B) Peremfeltétel 2:** Elejt, de T_UTO alatt még egyszer véletlenül bezár, majd újra kinyit. | **Ignorálás:** A szoftver az *első* érvényes nyitó élt rögzíti `fanoe_ki_time`-ként (`T_UTO` belépésétől számolva). A későbbi utólagos pattogások/zárások nem írják felül a már rögzített `t_ki` értéket. |


**Fontos elvi szabályok (CODE GENERATION LOGIC szempontjából is):**  

1. A ciklus időtartama MINDIG t_elo+t_bent+t_uto (dinamikusan, a settings.toml
   mindenkori értékeiből számolva) - soha nem a kódba írt fix, pl. 15000 ms.
2. Az IO6 (digitális) és az IO14 (analóg/ADC) érzékelési útvonalak EGYMÁSTÓL
   FÜGGETLENÜL futnak. Egyik sem várja meg vagy blokkolja a másikat.
3. Futás közbeni hibajelzés (ERROR_NO_PULLIN, ERROR_PREMATURE_DROPOUT, ERROR_NO_DROPOUT, "szakadt") sem állítja
   le a ciklust korábban - a mérés mindig a teljes cycle_duration-ig fut, utána jelentjük együtt az összes
   történést/hiányzó adatot. Ez alól egyetlen kivétel van: ha indításkor a kontaktus már alapból zárt
   (ERROR_ALREADY_CLOSED). Ebben az esetben a relé meghúzása nélkül azonnal a RESULT állapotba lépünk a
   felesleges terhelés és a téves mérések elkerülése érdekében.
4. r_be/r_ki KIZÁRÓLAG közelítő időbecslés (100ms mintavételi pontosság),
   NEM minősítés - a FANOE tényleges jó/rossz elbírálása a szervizes
   feladata a kijelzett Ohm érték alapján, ezt a kód NEM automatizálja.
5. Nem blokkoló megvalósítás kötelező (lásd CircuitPython_instructions.md) -
   a FanoeMeasurementCycle.update() metódust a fő ciklus minden körben hívja,
   time.monotonic() alapú időzítéssel; time.sleep() tilos.
6. Osztály neve: FanoeMeasurementCycle (OOP minta, lásd .copilot-instructions.md 5. pont).  

        
        Verziók:
        0.01 - kezdés... (2026-07-13)
        0.11 - boot sequence flow chart (2026-07-15)
        0.20 - automatikus mérési ciklus állapotgép specifikáció (2026-07-26)
        0.30 - menu struktúra hozzáadva, menu_data.py (2026-07-28)
        0.31 - kapcsolási rajz hozzáadva (2026-07-29)
        0.40 - indítás előtti zárt állapot és korai elengedés kezelése (2026-08-04)
        0.50 - állapotmártix és hibakezelés táblázat hozzáadva

"""
