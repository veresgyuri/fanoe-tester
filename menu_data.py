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
        "screen": (" Ohm-mérés üzemmód", "   123.4 Ω (kamu)"),
    },
    {
        "label": " FÁNOE KÉZI BE ▶",
        "kind": "leaf",
        "activate_keys": {"RIGHT"},
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
                "screen": (" ESP32-S3 CPU órajel:", "     {freq} MHz"),
            },
            {
                "label": " CPU hőmérséklet ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "screen": (" ESP32-S3 CPU hőfok:", "     {temp} °C"),
            },
            {
                "label": " Szabad memória ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "screen": (" Szabad RAM memória:", "    {ram,flash} MB)"),
            },
            {
                "label": " Alaplap azonosító ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "screen": (" Board azonosító:", "     {board_id}"),
            },
            {
                "label": " Chip azonosító ->",
                "kind": "leaf",
                "activate_keys": {"ENTER", "RIGHT"},
                "screen": (" Chip típus azonosító:", "     {uid}"),
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
                "screen": (" Software verzió:", "   {version} ✓"),
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
                "label": "   Szoftver reset ⏎",
                "kind": "leaf",
                "activate_keys": {"ENTER"},
                "action": "restart_device",
                "confirm_keys": {"ENTER"},
                "screen": ("     biztos benne?", "   igen ⏎ | nem ESC"),
            },
        ],
    },
]