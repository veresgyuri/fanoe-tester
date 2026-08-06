"""
test_menu_data_navigations.py

EGYSZERŰ, KEZDŐ SZINTŰ tesztfájl a menu_data.py (MENU_ROOT) struktúrájának
és a MenuNavigator (code.py) böngészési viselkedésének ellenőrzésére.

FONTOS - hogyan fut ez a teszt:
Ez NEM a boardon fut, hanem a saját géped sima Python környezetében:

    python -m unittest test_menu_data_navigations.py

(a menu_data.py, a tft_messages.py és a code.py mellett kell lennie,
ugyanabban a mappában - a tft_messages.py-t NEM helyettesítjük kamu
modullal, mert az is tiszta adatfájl, mint a menu_data.py, ugyanúgy
importálható hardver nélkül.)

Miért kellenek a lenti "kamu" (mock) modulok?
A code.py a fájl tetején hardver-modulokat importál (board, busio, stb.),
amik csak a CircuitPython-boardon léteznek. A PC-n ezek nélkül a
`from code import MenuNavigator` sor azonnal elhasalna. Ezért indulás
előtt regisztrálunk egy-egy üres, kamu modult ezekre a nevekre - így a
VALÓDI MenuNavigator osztályt tudjuk tesztelni, nem egy külön, esetleg
később elszakadó másolatát.
"""

import sys
import types
import unittest

# --- 1. Hardver modulok kamu verziója, hogy a code.py importálható legyen ---
_FAKE_HARDWARE_MODULES = (
    "board", "busio", "digitalio", "displayio", "keypad", "microcontroller",
    "neopixel", "pwmio", "analogio", "adafruit_bitmap_font",
    "adafruit_bitmap_font.bitmap_font", "adafruit_display_text",
    "adafruit_display_text.label", "fourwire", "adafruit_st7789",
)
for _name in _FAKE_HARDWARE_MODULES:
    if _name not in sys.modules:
        sys.modules[_name] = types.ModuleType(_name)

# A code.py néhány "from X import Y" alakú sort is használ - ezekhez a
# kamu modulnak konkrét attribútumként kell tartalmaznia Y-t is.
sys.modules["fourwire"].FourWire = type("FourWire", (), {})
sys.modules["adafruit_st7789"].ST7789 = type("ST7789", (), {})
sys.modules["adafruit_bitmap_font"].bitmap_font = sys.modules["adafruit_bitmap_font.bitmap_font"]
sys.modules["adafruit_display_text"].label = sys.modules["adafruit_display_text.label"]

# A code.py induláskor (modul-szinten) hivatkozik pl. board.IO7-re
# (RELAY_PIN = board.IO7) - ezért a kamu "board" modulnak kellenek IOxx
# attribútumok is, különben AttributeError-t kapnánk importáláskor.
_fake_board = sys.modules["board"]
for _i in range(49):
    setattr(_fake_board, f"IO{_i}", _i)

# --- 2. A VALÓDI menüadat és navigációs osztály importálása ---
from menu_data import MENU_ROOT

# A "code.py" fájlnév ÜTKÖZIK a Python szabványkönyvtár "code" modul-
# jával (code.interact, REPL-emuláláshoz). A "from code import ..." ezért
# törékeny lenne: ha bármi (debugger, plugin, tesztfuttató) korábban már
# beimportálta a szabványos "code"-ot, a mi sorunk a rossz modult kapná el
# a sys.modules gyorsítótárból. Emiatt explicit fájlútvonalról töltjük be,
# egy ütközésmentes álnévvel - ez a robusztus megoldás, függetlenül attól,
# unittest-tel, pytest-tel vagy bármi mással fut a teszt.
import importlib.util
import pathlib

_code_path = pathlib.Path(__file__).parent / "code.py"
_spec = importlib.util.spec_from_file_location("fanoe_code", _code_path)
_fanoe_code = importlib.util.module_from_spec(_spec)
sys.modules["fanoe_code"] = _fanoe_code
_spec.loader.exec_module(_fanoe_code)
MenuNavigator = _fanoe_code.MenuNavigator


def walk_menu_tree(nodes):
    """Segédfüggvény: bejárja a teljes fát (menü + almenük), egyesével
    visszaadva minden node-ot."""
    for node in nodes:
        yield node
        if node.get("kind") == "menu":
            yield from walk_menu_tree(node["children"])


class TestMenuDataStructure(unittest.TestCase):
    """A menu_data.py adatszerkezetének alapvető épség-ellenőrzése -
    ezek olyan hibákat fognak meg, amik futás közben csak a boardon
    derülnének ki (pl. egy "menu" node-nak nincs "children" mezője)."""

    def test_every_node_has_label_and_valid_kind(self):
        for node in walk_menu_tree(MENU_ROOT):
            self.assertIn("label", node)
            self.assertIn(node.get("kind"), ("menu", "leaf"))

    def test_menu_nodes_have_nonempty_children(self):
        for node in walk_menu_tree(MENU_ROOT):
            if node["kind"] == "menu":
                self.assertIn("children", node)
                self.assertTrue(len(node["children"]) > 0)

    def test_leaf_nodes_have_two_line_screen(self):
        for node in walk_menu_tree(MENU_ROOT):
            if node["kind"] == "leaf":
                self.assertIn("screen", node)
                self.assertEqual(len(node["screen"]), 2)

    def test_activate_keys_only_enter_or_right(self):
        for node in walk_menu_tree(MENU_ROOT):
            for key in node.get("activate_keys", set()):
                self.assertIn(key, ("ENTER", "RIGHT"))


class TestMenuNavigatorBasics(unittest.TestCase):
    """A MenuNavigator (a valódi code.py-beli osztály) alap böngészési
    viselkedése, a valós MENU_ROOT adaton."""

    def setUp(self):
        self.nav = MenuNavigator(MENU_ROOT)

    def test_starts_at_first_item(self):
        self.assertEqual(self.nav.current_item()["label"], MENU_ROOT[0]["label"])

    def test_down_moves_to_next_item(self):
        self.nav.move_updown(1)
        self.assertEqual(self.nav.current_item()["label"], MENU_ROOT[1]["label"])

    def test_up_at_top_does_not_move(self):
        self.nav.move_updown(-1)
        self.assertEqual(self.nav.current_item()["label"], MENU_ROOT[0]["label"])

    def test_down_at_bottom_does_not_move_past_last(self):
        for _ in range(len(MENU_ROOT) + 3):  # jóval túllépjük a lista végét
            self.nav.move_updown(1)
        self.assertEqual(self.nav.current_item()["label"], MENU_ROOT[-1]["label"])

    def test_go_left_at_root_returns_false(self):
        # A gyökérszinten nincs hova visszább lépni - lásd a code.py-ban
        # az "already_at_root" villanás logikáját, ami erre az esetre épül.
        self.assertFalse(self.nav.go_left())


if __name__ == "__main__":
    unittest.main()
