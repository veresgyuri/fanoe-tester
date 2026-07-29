"""boot.py - FANOE tester: USB-meghajtó és írási mód kapcsolása boot közben."""
# ver 1.1 -- 2026.07.13.
# Claude Sonnet 4.6 javaslata
# ...hogy akkor is tudja a code.py írni a fájlrendszert (memóriát) amikor a REPL USB-n fut
# ezt a filét boot.py névvel kell menteni a CIRCUITPY gyökérbe
#
# GPIO39 ----- kapcsoló ----- GND
#
# Indulási mód kiválasztása kapcsolóval.
#
# Kapcsoló nyitva:
# - fejlesztői mód
# - CIRCUITPY USB-meghajtó engedélyezve
# - a számítógép írhatja a fájlrendszert
#
# Kapcsoló zárva, GPIO39 a GND-re kötve:
# - felhasználói mód
# - CIRCUITPY USB-meghajtó letiltva
# - a CircuitPython-program írhatja a fájlrendszert
# - az USB-soros REPL továbbra is engedélyezve marad
#
# ******************* Boot sequence *******************
#
#              +------------ 1. ------- ----+
#              |      Rendszerindulás       |
#              | (Hard Reset / Bekapcsolás) |
#              +-------------+------------ -+
#                            |
#                            v
#                  +-------- 2. ------+
#                  |      boot.py     |
#                  +---------+--------+
#                            |
#          IO39 olvasás: switch.value (HIGH/LOW)
#                            |
#          +-----------------+-------------------+
#          |                                     |
#         LOW (GND)                      HIGH (nem GND)
#          |                                     |
#          v                                     v
# +--------+-------------------+         +-------+------+
# | storage.disable_usb_drive()|         | nincs teendő |
# |         fut le             |         +-------+------+
# +-------------+--------------+                 |
#               |                                |
#               v                                v
# +-------------+--------------+    +------------+--------------+
# | KÖRNYEZET: FELHASZNÁLÓ MÓD |    | KÖRNYEZET: FEJLESZTŐI MÓD |
# |  - USB meghajtó INAKTÍV    |    |  - USB meghajtó AKTÍV     |
# +-------------+--------------+    +------------+--------------+
#               |                                |
#               v                                v
#               |                                |
#               +----------------+---------------+
#                                |
#             switch.deinit()  IO39 felszabadítása
#                                |
#                      +---------v-------------+
#                      | USB meghajtó állapota |
#                      | (látható/nem látható) |
#                      +-----------------------+
#                                |
#                                v
#                  +-------------3.------------+
#                  |          code.py          |
#                  |       (Fő program)        |
#                  +-------------+-------------+
#                                |
#                         [A program fut]
#                                |
#                                v
#           +--------------------+-----------------------+
#           | Felhasználó a menüből MENTENI/TÖRÖLNI akar |
#           +--------------------+-----------------------+
#                                |
#                                v
#     +-------------------------------------------------------+
#     |  Függvényhívás: pl. save_credentials()                |
#     |  - lefut a storage.remount("/", False) parancs        |
#     |  (Felh. módban CPy 9.0+ óta technikailag már          |
#     |   felesleges, de nem árt - biztonsági redundancia)    |
#     +--------------------------+----------------------------+
#                                |
# +------------------------------v--------------------------------+
# |    A 'remount' parancs EREDMÉNYE a KÖRNYEZETTŐL függ:         |
# |                                                               |
# |  +-------------------------+      +------------------------+  |
# |  |  FELHASZNÁLÓI MÓDBAN    |      |   FEJLESZTŐI MÓDBAN    |  |
# |  | (USB meghajtó inaktív)  |      | (USB meghajtó aktív)   |  |
# |  +-------------------------+      +------------------------+  |
# |  | - SIKERES fájlírás      |      | - SIKERTELEN fájlírás  |  |
# |  |   -> Írási jogot a      |      |   -> Exception:        |  |
# |  |      program megkapta   |      |   -> "Cannot remount..."  |
# |  |            |            |      |            |           |  |
# |  |            v            |      |            v           |  |
# |  | pl. a 'settings.toml'   |      |        Hibaüzenet      |  |
# |  | fájl sikeresen          |      |   A fájlművelet nem    |  |
# |  | létrejön/felülíródik    |      |   hajtódik végre       |  |
# |  |                         |      |                        |  |
# |  | - REPL működik          |      | - REPL működik         |  |
# |  +-------------------------+      +------------------------+  |
# |                                                               |
# +---------------------------------------------------------------+

import board
import digitalio
import storage

# Válassz egy szabad GPIO lábat a kapcsolónak.
# Bármelyik szabad, nem speciális funkciójú láb megteszi.
SWITCH_PIN = board.IO39

# A kiválasztott láb beállítása bemenetként, belső felhúzó ellenállással.
# Így alapértelmezetten (ha nincs a GND-re kötve) HIGH szinten lesz.
switch = digitalio.DigitalInOut(SWITCH_PIN)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# A kapcsoló állapotának ellenőrzése.
# A `switch.value` 'True', ha a láb HIGH, és 'False', ha LOW (GND-re húzott).
# Tehát akkor tiltjuk le a meghajtót, ha a láb a földre van kötve.
if not switch.value:
    print("Felhasználói mód:")
    print("- USB meghajtó letiltva")
    print("- A fájl írása a programnak engedélyezve")
    storage.disable_usb_drive()
else:
    print("Fejlesztői mód: USB meghajtó engedélyezve.")
    print("Ebben a módban a programból nem engedélyezett a fájl írás.")
    # Itt nem kell semmit csinálni, az engedélyezés az alapértelmezett.

# A láb felszabadítása `code.py` számára, ha kell (pl. JTAG TCK részére)
switch.deinit()
