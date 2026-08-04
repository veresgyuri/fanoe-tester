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
# FÁNOE Mérési Ciklus Állapotmátrix és Hibavédelmi Táblázat

Ez a dokumentum a `FanoeMeasurementCycle` állapotgép futásidejű viselkedését, a digitális (IO6) és analóg (IO14) bemenetek lehetséges eseményeit, valamint a szoftveres reakciókat foglalja össze.
```
| Ciklusfázis / Időtartam | Vezérlés (IO7) | Fizikai kontaktus (IO6) várt állapota | Analóg Ohm-mérés (IO14) állapota | Lehetséges rendellenes esemény (Edge Case) | Szoftveres reakció / Hibajelzés |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Indítás előtti pillanat** | `OFF` | **Nyitott** (Pull-Up miatt HIGH) | Magas ellenállás / Szakadt | **Beragadt kontaktus:** Az IO6 már indítás előtt ZÁRT (`LOW`). | **Megszakítás:** `error_already_closed` flag beállítása. A relé *nem* húz be, a ciklus azonnal megszakad, a RESULT listában megjelenik: `HIBA: alapból zárva`. |
| **T_ELO** <br>*(Előkésleltetés)* | `OFF` | **Nyitott** marad | Magas ellenállás | **Peremfeltétel 1:** T_ELO alatt a kontaktus véletlenül bezár, majd el is ejt. | **Ignorálás:** Mivel a szoftver csak a `T_BENT` fázistól kezdi el érdemben figyelni a behúzási éleket, ez nem rontja el a `t_be` mérést. |
| **T_BENT** <br>*(Gerjesztési fázis)* | `ON` | **Záródnia kell** (IO6 átvált `LOW`-ra) | Stabil alacsony ellenállás (`< r_ell`, majd zárolódik `fanoe_ell`) | **A) Nem húz be időben:** T_BENT végéig nincs záró él. | **Hibajelzés:** `error_no_pullin` = `True`. A ciklus lefut végig, a RESULT listában: `HIBA: nem húzott be` és `t_be: N/A`. |
| **T_BENT** <br>*(Gerjesztési fázis)* | `ON` | Zárt állapot fenntartása | Stabil ellenállás (`fanoe_ell` zárolva) | **B) Korai elengedés:** Beépül (`fanoe_be` rögzítve), de a T_BENT lejárta *előtt* kinyit az érintkező. | **Hibajelzés:** `error_premature_dropout` = `True`. A ciklus lefut végig, a RESULT listában: `HIBA: korai elengedés`. |
| **T_BENT** <br>*(Gerjesztési fázis)* | `ON` | Zárt állapot | Az ellenállás az `r_ell` küszöb felett marad (`r_be_time` rögzítés) | **C) Érintkezési hiba / Magas átmeneti ellenállás:** Az IO6 zár, de az IO14-en mért ellenállás szakadást (`szakadt`) vagy magas értéket mutat. | **Mérés / Jelzés:** `fanoe_ell` = `szakadt` vagy valós magas érték. A ciklus lefut, a RESULT listában megjelenik a mért/szakadt érték (minősítést a kezelő végez). |
| **T_UTO** <br>*(Utóidő / Elejtés)* | `OFF` | **Nyitnia kell** (IO6 átvált `HIGH`-ra) | Megemelkedik az ellenállás (`> r_ell`) | **A) Nem ejt el időben:** A ciklus végéig (T_UTO lejárta) nincs nyitó él. | **Hibajelzés:** `error_no_dropout` = `True`. A ciklus lefut végig, a RESULT listában: `HIBA: nem ejtett el` és `t_ki: N/A`. |
| **T_UTO** <br>*(Utóidő / Elejtés)* | `OFF` | Nyitott állapot fenntartása | Magas ellenállás / Szakadt (`r_ki_time` rögzítés) | **B) Peremfeltétel 2:** Elejt, de T_UTO alatt még egyszer véletlenül bezár, majd újra kinyit. | **Ignorálás:** A szoftver az *első* érvényes nyitó élt rögzíti `fanoe_ki_time`-ként (`T_UTO` belépésétől számolva). A későbbi utólagos pattogások/zárások nem írják felül a már rögzített `t_ki` értéket. |
```
## Fontos elvi megjegyzések:
1. **Nem blokkoló felépítés:** Egyetlen futás közbeni hiba sem állítja le a folyamatot idő előtt. A mérés mindig a teljes `cycle_duration` (`t_elo + t_bent + t_uto`) leteltéig fut.
2. **Kivétel (Indítási védelem):** Az egyetlen kivétel az indítás előtti beragadt kontaktus (`error_already_closed`), amely megakadályozza a relé behúzását, és azonnal a RESULT képernyőre urik.
3. **Független útvonalak:** Az IO6 (digitális idők) és az IO14 (analóg küszöbök) mérései egymástól függetlenül futnak.