# menu_data.py
# Tiszta adatfájl (dict/list) - a fanoe-tester menüstruktúrája.
# NEM tartalmaz függvényt, hardver-inicializálást vagy futásidejű logikát -
# lásd .copilot-instructions.md Section 5. A navigációt és a megjelenítést
# a code.py (OOP réteg) valósítja meg, ez a fájl csak leírja a fát.
#
# Az /instructions/fanoe_tester_logic.md "Menü struktúra vázlat" táblázata
# alapján. A "screen" mezőkben szereplő konkrét értékek egy része kamu
# teszt-adat - a valós, dinamikus tartalmú képernyők a code.py-ban majd
# "action" kulcsra hivatkoznak, nem statikus stringre.

MENU_ROOT = [
    {
        "label": " ELLENÁLLÁS MÉRÉS ⏎",
        "kind": "leaf",
        "activate_keys": {"ENTER"},
        "action": "ohm_meter_enter",
        "auto_dispatch": True,
        "screen": (" Ohm-mérés üzemmód", ""),
    },
    {
        "label": " FÁNOE KÉZI BE ▶",
        "kind": "leaf",
        "activate_keys": {"RIGHT"},
        "action": "fanoe_manual_hold_enter",
        "auto_dispatch": True,
        "screen": ("  FÁNOE behúzatás ⏎", "  csak nyomva aktív"),
    },
    {
        "label": " FÁNOE BE/KI MÉRÉS ▶",
        "kind": "leaf",
        "activate_keys": {"RIGHT"},
        "screen": ("t_elo,t_bent,t_uto", " Ciklus indítása ⏎"),
    },
    {
        "label": " BEÁLLÍTÁSOK ▶",
        "kind": "menu",
        "activate_keys": {"RIGHT"},
        "children": [
            {
                "label": " FÁVA idő állítás ▶",
                "kind": "leaf",
                "activate_keys": {"RIGHT"},
                "screen": ("FÁVA holtidő ↑↓ ⏎", " t_elo = 1500 ms"),
            },
            {
                "label": " Bent idő állítás ▶",
                "kind": "leaf",
                "activate_keys": {"RIGHT"},
                "screen": ("FÁNOE bent idő ↑↓ ⏎", " t_bent = 3000 ms"),
            },
            {
                "label": " FÁNOE KI utóidő ▶",
                "kind": "leaf",
                "activate_keys": {"RIGHT"},
                "screen": ("KI utáni idő ↑↓ ⏎", " t_uto = 1000 ms"),
            },
            {
                "label": " Ohm érték állítás ▶",
                "kind": "leaf",
                "activate_keys": {"RIGHT"},
                "screen": ("alsó Ω érték ↑↓ ⏎", " r_ell = 70 Ω"),
            },
            {
                "label": " Fényerő állítása ▶",
                "kind": "leaf",
                "activate_keys": {"RIGHT"},
                "screen": (" TFT fényerő ↑↓ ⏎", "   9 / 3 (kamu)"),
            },
            {
                "label": " Színek állítása ▶",
                "kind": "leaf",
                "activate_keys": {"RIGHT"},
                "screen": (" TFT színvilág ↑↓ ⏎", "   1 / 5 (kamu)"),
            },
        ],
    },
    {
        "label": " INFORMÁCIÓK ▶",
        "kind": "menu",
        "activate_keys": {"RIGHT"},
        "children": [
            {
                "label": " CPU frekvencia ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "action": "info_cpu_freq",
                "auto_dispatch": True,
                "screen": (" ESP32-S3 CPU órajel:", "     ... MHz"),
            },
            {
                "label": " CPU hőmérséklet ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "action": "info_cpu_temp",
                "auto_dispatch": True,
                "screen": (" ESP32-S3 CPU hőfok:", "     ... °C"),
            },
            {
                "label": " Szabad memória ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "action": "info_free_ram",
                "auto_dispatch": True,
                "screen": (" Szabad RAM memória:", "    ... KB"),
            },
            {
                "label": " Alaplap azonosító ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "action": "info_board_id",
                "auto_dispatch": True,
                "screen": (" Board azonosító:", "     ..."),
            },
            {
                "label": " Chip azonosító ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "action": "info_chip_uid",
                "auto_dispatch": True,
                "screen": (" Chip típus azonosító:", "     ..."),
            },
            {
                "label": " Hardwer verzió ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "screen": (" Hardwer felépítés:", "   ver.1.0 ✗"),
            },
            {
                "label": " Software verzió ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "action": "info_sw_version",
                "auto_dispatch": True,
                "screen": (" Software verzió:", "   ..."),
            },
            {
                "label": " https://github.com ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "screen": ("  github/veresgyuri/", "    fanoe-tester ☺"),
            },
        ],
    },
    {
        "label": " RESTART *.* ▶ ⏎",  # kivétel: mindkét gombbal aktiválható
        "kind": "menu",
        "activate_keys": {"RIGHT", "ENTER"},
        "children": [
            {
                "label": " Szoftver reset ⏎",
                "kind": "leaf",
                "activate_keys": {"ENTER"},
                "action": "restart_device",
                "confirm_keys": {"ENTER"},
                "screen": ("   biztos benne?", " igen ⏎ | nem ESC"),
            },
        ],
    },
]
