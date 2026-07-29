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
|ELLENÁLLÁS MÉRÉS ⏎  |      (nincs)        | Ohm-mérés üzemmód   |     xxx.x Ω        |
|                       ────────────────────────────────────────────────────────────
|FÁNOE KÉZI BE ▶     |      (nincs)        | FÁNOE behúzatás ⏎   |  csak nyomva aktív |
|                    |  ────────────────────────────────────────────────────────────
|FÁNOE BE/KI MÉRÉS ▶ |      (nincs)        |t_elo, t_bent, t_uto | Ciklus indítása  ⏎ |
|                    |  ────────────────────────────────────────────────────────────
|BEÁLLÍTÁSOK ▶       |FÁVA idő állítás ▶   |FÁVA holtidő ↑↓   ⏎  |     t_elo ms       |
|                    |Bent idő állítás ▶   |FÁNOE bent idő ↑↓ ⏎  |     t_bent ms      |
|                    |FÁNOE KI utóidő ▶    |KI utáni idő ↑↓   ⏎  |     t_uto ms       |
|                    |Ohm érték állítás ▶  |alsó Ω érték ↑↓   ⏎  |     r_ell Ω        |
|                    |Fényerő állítása ▶   |TFT fényerő  ↑↓   ⏎  |      9 / x         |
|                    |Színek állítása  ▶   |TFT színvilág ↑↓  ⏎  |      5 / x         | 
|                    |  ────────────────────────────────────────────────────────────  |       
|INFORMÁCIÓK ⏎       |CPU frekvencia ->    |ESP32-S3 CPU órajel: |   {freq} MHz       |
|                    |CPU hőmérséklet ->   |ESP32-S3 CPU hőfok:  |   {temp} °C        |
|                    |Szabad memória ->    |Szabad RAM memória:  |   {ram,flash} MB   |
|                    |Alaplap azonosító -> |Board azonosító:     |   {board_id}       |
|                    |Chip azonosító ->    |Chip típus azonosító:|   {uid}            |
|                    |Hardwer verzió ->    |Hardwer felépítés:   |   "ver.1.0 ✗"      |
|                    |Software verzió ->   |Software verzió:     |   {version} ✓      |
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
    - TFT-n megjelenik: "aborted_by_user" üzenetkulcs (-> tft_messages.py, pl. "Mérés megszakítva")
    - Kilépés: felhasználó ESC (vagy rövid időzítés után automatikusan) -> IDLE

- IDLE
    - Várakozás: IO7 = OFF. Semmilyen mérés nem fut.  
    - Kilépés:  
      - felhasználó ENTER az "Automatikus mérés" menüben -> start()  
      - felhasználó ESC -> vissza a főmenübe (menü navigáció, nem érinti a mérési logikát)

  T_ELO
    - Belépés: start() meghívva. cycle_start_time = most. IO7 = OFF.
    - Kilépés: elapsed >= t_elo -> T_BENT

  T_BENT
    - Belépés: IO7 = ON. relay_on_time = most.
               IO14 mintavételi task elindul (100ms periódussal, a ciklus végéig fut).
    - IO6: az ELSŐ záródás -> fanoe_be_time rögzítve, t_be = fanoe_be_time - t_elo
           (ha T_BENT alatt nem történik záródás -> ERROR_NO_PULLIN jelzés,
            a ciklus NEM áll le emiatt)
    - IO14: T_SETTLE_MS elteltével fanoe_be_time után figyeljük a stabilitást
            (lásd EVALUATE, fanoe_ell számítása)
    - IO14: párhuzamosan, EGYMÁSTÓL FÜGGETLENÜL figyeljük az r_ell küszöb
            ELSŐ átlépését fölfelé -> r_be_time rögzítve
            (ha nem történik meg, r_be = N/A, ez NEM hiba)
    - Kilépés: elapsed >= t_elo+t_bent -> T_UTO

  T_UTO
    - Belépés: IO7 = OFF. relay_off_time = most.
    - IO6: az ELSŐ nyitás -> fanoe_ki_time rögzítve,
           t_ki = fanoe_ki_time - relay_off_time
           (ha ciklus végéig nem történik meg -> ERROR_NO_DROPOUT jelzés,
            a ciklus NEM áll le emiatt)
    - IO14: továbbra is fut; figyeljük az r_ell küszöb UTOLSÓ átlépését lefelé
            -> r_ki_time rögzítve (ha nem történik meg, r_ki = N/A, NEM hiba)
    - Kilépés: elapsed >= t_elo+t_bent+t_uto (= cycle_duration) -> EVALUATE
               (FELTÉTEL NÉLKÜL, függetlenül attól, hogy fanoe_ki/r_ki megtörtént-e)

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
  - Kilépés: automatikusan -> RESULT

  RESULT
    - TFT-n megjelenik: t_be, t_ki, fanoe_ell (vagy "szakadt"), r_be, r_ki (vagy "N/A"),
      valamint bármelyik ERROR_NO_PULLIN / ERROR_NO_DROPOUT jelzés, ha történt.
    - Egyik jelzés SEM állítja meg korábban a ciklust - csak tájékoztató jellegű.
    - Kilépés: felhasználó ESC -> IDLE


**Fontos elvi szabályok (CODE GENERATION LOGIC szempontjából is):**  

1. A ciklus időtartama MINDIG t_elo+t_bent+t_uto (dinamikusan, a settings.toml
   mindenkori értékeiből számolva) - soha nem a kódba írt fix, pl. 15000 ms.
2. Az IO6 (digitális) és az IO14 (analóg/ADC) érzékelési útvonalak EGYMÁSTÓL
   FÜGGETLENÜL futnak. Egyik sem várja meg vagy blokkolja a másikat.
3. Egyik hibajelzés (ERROR_NO_PULLIN, ERROR_NO_DROPOUT, "szakadt") sem állítja
   le a ciklust korábban - a ciklus mindig a teljes cycle_duration-ig fut,
   utána jelentjük együtt az összes történést/hiányzó adatot.
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
        0,30 - menu struktúra hozzáadva, menu_data.py (2026-07-28)

"""
