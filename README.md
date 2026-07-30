# FANOE tester

Ez a repository egy ESP32-S3 alapú, CircuitPython-ban futó diagnosztikai / tesztelő rendszerhez készült firmware-t és kapcsolódó forrásfájlokat tartalmazza. A projekt célja egy 6 gombos billentyűzettel és egy kis TFT kijelzővel működő, menüvezérelt tesztműszer összeállítása.

## Rövid bemutató

A rendszer főként a következő funkciókat szolgálja:
- menüvezérelt felület a kijelzőn
- billentyűzetes navigáció
- beállítások, információs oldalak és mérési üzemmódok
- CircuitPython-alapú futtatás ESP32-S3 hardveren

A fő program a [code.py](code.py) fájlban található, a menüstruktúra a [menu_data.py](menu_data.py) fájlban van definiálva. A rendszerindítási viselkedést a [boot.py](boot.py) fájl kezeli.

## Hardver

A projekthez az alábbi hardverösszetevőket használja:
- ESP32-S3 Super Mini alaplap
- 6 gombos mátrix billentyűzet
- 76 × 284 pixel-es ST7789 vezérlésű TFT kijelző
- USB-C kapcsolat fejlesztéshez / hibakereséshez

## Fájlok és szerepük

- [code.py](code.py) – a fő alkalmazás, a kijelzővezérlés, billentyűzetkezelés és a menülogika.
- [menu_data.py](menu_data.py) – a menüfa és a felhasználói felület adatai.
- [boot.py](boot.py) – induláskor beállítja a felhasználói / fejlesztői módot, és kezeli az USB-meghajtó viselkedését.
- [instructions/](instructions/) – hardver- és szoftver-specifikus dokumentációk.
- [fonts/](fonts/) – a kijelzőn használt betűtípusok.
- [lib/](lib/) – a CircuitPython futtatáshoz szükséges könyvtárak.

## Telepítés és futtatás

1. Telepítsd a CircuitPython firmware-t az ESP32-S3 Super Mini boardra.
2. Másold a repository tartalmát a CIRCUITPY meghajtóra.
3. Győződj meg róla, hogy a szükséges könyvtárak a megfelelő helyen vannak a [lib/](lib/) mappában.
4. Indítsd újra a készüléket.
5. A [boot.py](boot.py) alapján a rendszer felhasználói vagy fejlesztői üzemmódban indulhat.

## Üzemmódok

A bootfázisban a GPIO39-es kapcsoló állapota alapján dönt a rendszer:
- felhasználói mód: az USB meghajtó inaktív, a program számára engedélyezett a fájlírás
- fejlesztői mód: az USB meghajtó aktív, ami a fejlesztéshez hasznos

## Fejlesztéshez

A projekt dokumentációja az [instructions/](instructions/) mappában található. A legfontosabb források közé tartozik:
- [instructions/fanoe_tester_logic.md](instructions/fanoe_tester_logic.md)
- [instructions/keypad_6_matrix_instructions.md](instructions/keypad_6_matrix_instructions.md)
- [instructions/esp32s3supermini_instructions.md](instructions/esp32s3supermini_instructions.md)

## Megjegyzés

Ez a projekt jelenleg aktív fejlesztés alatt áll, így a funkciók és a menüelemek a későbbiekben változhatnak.
