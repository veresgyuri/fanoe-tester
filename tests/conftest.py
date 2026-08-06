import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock

import pytest


def _install_circuitpython_stubs():
    """Mockolja a CircuitPython-specifikus modulokat a normál Python tesztkörnyezetben."""
    mock_modules = [
        "board",
        "busio",
        "displayio",
        "keypad",
        "neopixel",
        "pwmio",
        "analogio",
        "digitalio",
        "microcontroller",
        "fourwire",
        "adafruit_st7789",
        "adafruit_bitmap_font",
        "adafruit_display_text",
    ]

    for module_name in mock_modules:
        if module_name not in sys.modules:
            sys.modules[module_name] = MagicMock()

    board_module = sys.modules["board"]
    for pin_name in ["IO1", "IO2", "IO3", "IO4", "IO5", "IO6", "IO7", "IO8", "IO9", "IO10", "IO11", "IO12", "IO13", "IO14", "IO48"]:
        setattr(board_module, pin_name, pin_name)


def _load_project_code_module():
    """Betölti a projekt code.py-ját a tesztekhez, anélkül hogy a standard code modult sértenénk."""
    root_dir = pathlib.Path(__file__).resolve().parent.parent
    code_path = root_dir / "code.py"
    spec = importlib.util.spec_from_file_location("fanoe_project_code", code_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fanoe_project_code"] = module
    spec.loader.exec_module(module)
    return module


_install_circuitpython_stubs()
_load_project_code_module()


TEST_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = TEST_DIR.parent
MENU_DATA_PATH = ROOT_DIR / "menu_data.py"

spec = importlib.util.spec_from_file_location("menu_data", MENU_DATA_PATH)
menu_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(menu_data)

MENU_ROOT = menu_data.MENU_ROOT


@pytest.fixture
def menu_root():
    return MENU_ROOT
