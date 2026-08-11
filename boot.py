"""boot.py - FANOE tester: USB-meghajtó és írási mód kapcsolása boot közben."""
# ezt a filét boot.py névvel kell menteni a CIRCUITPY gyökérbe
# ver 1.1 -- 2026.07.13. # Claude Sonnet 4.6 javaslata
# ...hogy akkor is tudja a code.py írni a fájlrendszert (memóriát) amikor a REPL USB-n fut
# ver 1.2 -- 2026.08.01.
# - Hozzáadva: CPU órajel csökkentése (energiatakarékosság/hőmérséklet optimalizálás)
# - Hozzáadva: USB meghajtó írási jogának hardveres (kapcsolós) vezérlése
#
# ver 1.3 -- 2026.08.11.
# - Hozzáadva: Wi-Fi letiltás
# - Hozzáadva: Bluetooth letiltva
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

# ver 1.2 -- 2026.08.01 Gemini3 flash (működési freki/órajel fix beállítás a boot során

import board
import digitalio
import storage
import microcontroller

print("\n--- BOOT.PY INDUL ---")

# ==========================================
# 1. CPU Órajel beállítása
# ==========================================
try:
    # Órajel beállítása (240MHz helyett 160MHz)
    microcontroller.cpu.frequency = 160000000
    # microcontroller.cpu.frequency = 80000000
    # visszaolvassuk és átváltjuk MHz-re a kiíratáshoz
    freq_mhz = microcontroller.cpu.frequency // 1000000
    print(f"[OK] CPU órajel beállítva: {freq_mhz} MHz")
except Exception as e:
    print(f"[HIBA] Nem sikerült az órajelet módosítani! ({e})")

# ==========================================
# 2. USB / Fájlrendszer írási jogok beállítása
# ==========================================
# Válassz egy szabad GPIO lábat a kapcsolónak.
SWITCH_PIN = board.IO39

# A kiválasztott láb beállítása bemenetként, belső felhúzó ellenállással.
switch = digitalio.DigitalInOut(SWITCH_PIN)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# A kapcsoló állapotának ellenőrzése.
if not switch.value:
    print("[MÓD] Felhasználói mód:")
    print("      - USB meghajtó letiltva")
    print("      - Fájlírás a code.py számára ENGEDÉLYEZVE")
    storage.disable_usb_drive()
else:
    print("[MÓD] Fejlesztői mód:")
    print("      - USB meghajtó engedélyezve")
    print("      - Fájlírás a code.py számára TILTVA")

# ==========================================
# 3. WiFi és Bluetooth letiltása (nem használt rádiók, energiatakarékosság)
# ==========================================
try:
    import wifi
    wifi.radio.enabled = False
    print("[OK] WiFi radio letiltva")
except Exception as e:
    print(f"[HIBA] WiFi letiltasa sikertelen: {e}")

try:
    import _bleio
    _bleio.adapter.enabled = False
    print("[OK] Bluetooth adapter letiltva")
except Exception as e:
    print(f"[HIBA] Bluetooth letiltasa sikertelen: {e}")


# A láb felszabadítása `code.py` számára
switch.deinit()

print("--- BOOT.PY BEFEJEZŐDÖTT ---\n")