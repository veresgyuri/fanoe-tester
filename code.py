# code.py - FANOE tesztműszer, fő program
# OOP réteg - a menüfát a menu_data.py adja (pure data, lásd .copilot-
# instructions.md Section 5). Ez a fájl adja a viselkedést: kijelző,
# keypad, navigáció, és a jövőben ide kerül a mérési/beállítás logika
# dispatch-elése is (lásd FanoeTesterApp._dispatch_action).

import time
import board
import busio
import displayio
import keypad
import microcontroller
import pwmio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from fourwire import FourWire
from adafruit_st7789 import ST7789

from menu_data import MENU_ROOT

DEBUG = True


def dprint(*args, **kwargs) -> None:
    """Print debug messages when DEBUG mode is enabled."""
    if DEBUG:
        print(*args, **kwargs)


# --- DISPLAY KONFIGURÁCIÓ ---
DISPLAY_WIDTH = 284
DISPLAY_HEIGHT = 76
DISPLAY_ROTATION = 90
DISPLAY_COLSTART = 82
DISPLAY_ROWSTART = 18
HALF_HEIGHT = DISPLAY_HEIGHT // 2  # 38 px felső / alsó sáv

TFT_SPI_SCL = board.IO13
TFT_SPI_SDA = board.IO12
TFT_CS_PIN = board.IO9
TFT_DC_PIN = board.IO10
TFT_RST_PIN = board.IO11

BACKLIGHT_PIN = board.IO8
BACKLIGHT_FREQUENCY = 1000
BACKLIGHT_ACTIVE_LOW = True
BACKLIGHT_DUTY_CYCLE = 32768

FONT_PATH = "/fonts/hu_127_ekezetes_20.pcf"
LINE1_Y = 0
LINE2_Y = 37

COLOR_BG_NORMAL = 0x000000
COLOR_TEXT_NORMAL = 0xFFFFFF
COLOR_BG_HIGHLIGHT = 0xFFCC00
COLOR_TEXT_HIGHLIGHT = 0x000000
COLOR_BORDER_HIGHLIGHT = 0x0033FF
BORDER_THICKNESS = 3

# --- WELCOME SCREEN KONFIGURÁCIÓ ---
WELCOME_TEXT = "FÁNOE tester - 2026"
WELCOME_BORDER = 8
WELCOME_BORDER_COLOR = 0xAA5AFF
WELCOME_BG_COLOR = 0x000080
WELCOME_TEXT_COLOR = 0xFFFF00
WELCOME_FADE_STEPS = (0, 96, 1024, 2048, 4096, 8192, 16384, 32768, 49152, 65535)
WELCOME_STEP_DELAY = 0.08  # egyszeri, indításkori animáció - lásd megjegyzés lent
WELCOME_HOLD_SECONDS = 2.22

# --- KEYPAD KONFIGURÁCIÓ ---
ROW_PINS = (board.IO5, board.IO4)
COLUMN_PINS = (board.IO1, board.IO2, board.IO3)
KEY_NAMES = {0: "ENTER", 1: "LEFT", 2: "UP", 3: "ESC", 4: "RIGHT", 5: "DOWN"}
LONG_PRESS_SEC = 2.0


class Keypad:
    """A 6 gombos mátrix csomagolása: nevesített gombesemények, ESC
    hosszú-nyomás detektálással."""

    def __init__(self, row_pins, column_pins, key_names, long_press_sec):
        self._matrix = keypad.KeyMatrix(row_pins=row_pins, column_pins=column_pins)
        self._key_names = key_names
        self._long_press_sec = long_press_sec
        self._press_time = {}

    def poll(self):
        """Egy esemény lekérése, vagy None, ha nincs. Visszatérési érték:
        (key_name, "pressed"|"released", duration_or_None)."""
        event = self._matrix.events.get()
        if not event:
            return None

        key_name = self._key_names.get(event.key_number, "ISMERETLEN")

        if event.pressed:
            self._press_time[event.key_number] = time.monotonic()
            return (key_name, "pressed", None)

        # event.released
        pressed_at = self._press_time.get(event.key_number)
        duration = (time.monotonic() - pressed_at) if pressed_at else 0.0
        return (key_name, "released", duration)

    def is_long_press(self, duration):
        return duration is not None and duration >= self._long_press_sec


class Display:
    """ST7789 inicializálás, font betöltés, 2 soros, kiemelhető/keretes
    megjelenítés."""

    def __init__(self):
        self._init_backlight()
        self._init_display()
        self._init_font()
        self._init_layout()

    def _init_backlight(self):
        self._backlight = pwmio.PWMOut(
            BACKLIGHT_PIN, frequency=BACKLIGHT_FREQUENCY, duty_cycle=0
        )
        self._set_backlight(0)  # induláskor kikapcsolva - show_welcome futtatja fel

    def _set_backlight(self, logical_duty):
        """logical_duty: 0 (ki) .. 65535 (teljes fényerő), a BACKLIGHT_ACTIVE_LOW
        automatikusan figyelembe véve."""
        clamped = max(0, min(65535, logical_duty))
        self._backlight.duty_cycle = (
            (65535 - clamped) if BACKLIGHT_ACTIVE_LOW else clamped
        )

    def _init_display(self):
        dprint("Initializing TFT display (invert=False)")
        displayio.release_displays()
        spi = busio.SPI(TFT_SPI_SCL, MOSI=TFT_SPI_SDA)
        display_bus = FourWire(
            spi, command=TFT_DC_PIN, chip_select=TFT_CS_PIN, reset=TFT_RST_PIN
        )
        self.display = ST7789(
            display_bus,
            width=DISPLAY_WIDTH,
            height=DISPLAY_HEIGHT,
            colstart=DISPLAY_COLSTART,
            rowstart=DISPLAY_ROWSTART,
            rotation=DISPLAY_ROTATION,
            invert=False,
        )

    def _init_font(self):
        dprint("Loading %s" % FONT_PATH)
        self.font = bitmap_font.load_font(FONT_PATH)

    def _init_layout(self):
        self.top_bitmap = displayio.Bitmap(DISPLAY_WIDTH, HALF_HEIGHT, 2)
        self.top_palette = displayio.Palette(2)
        top_sprite = displayio.TileGrid(
            self.top_bitmap, pixel_shader=self.top_palette, x=0, y=0
        )

        self.bottom_bitmap = displayio.Bitmap(DISPLAY_WIDTH, HALF_HEIGHT, 2)
        self.bottom_palette = displayio.Palette(2)
        bottom_sprite = displayio.TileGrid(
            self.bottom_bitmap, pixel_shader=self.bottom_palette, x=0, y=HALF_HEIGHT
        )

        self._draw_border(self.top_bitmap, BORDER_THICKNESS)
        self._draw_border(self.bottom_bitmap, BORDER_THICKNESS)

        self.splash = displayio.Group()
        self.splash.append(top_sprite)
        self.splash.append(bottom_sprite)

        self.line1_label = label.Label(
            self.font, text="", color=COLOR_TEXT_NORMAL, x=4, y=LINE1_Y
        )
        self.line2_label = label.Label(
            self.font, text="", color=COLOR_TEXT_NORMAL, x=4, y=LINE2_Y
        )
        self.splash.append(self.line1_label)
        self.splash.append(self.line2_label)
        self.display.root_group = self.splash

    @staticmethod
    def _draw_border(bmp, thickness):
        w, h = bmp.width, bmp.height
        for y in range(h):
            for x in range(w):
                edge = x < thickness or x >= w - thickness or y < thickness or y >= h - thickness
                bmp[x, y] = 1 if edge else 0

    def set_line(self, is_top, text, highlighted):
        palette = self.top_palette if is_top else self.bottom_palette
        lbl = self.line1_label if is_top else self.line2_label
        if highlighted:
            palette[0] = COLOR_BG_HIGHLIGHT
            palette[1] = COLOR_BORDER_HIGHLIGHT
            lbl.color = COLOR_TEXT_HIGHLIGHT
        else:
            palette[0] = COLOR_BG_NORMAL
            palette[1] = COLOR_BG_NORMAL
            lbl.color = COLOR_TEXT_NORMAL
        lbl.text = text

    def show_pair(self, top_text, bottom_text, highlight_pos):
        """highlight_pos: 0 = felső sor kiemelve, 1 = alsó sor kiemelve,
        None = egyik sem (pl. leaf 'screen' nézet)."""
        self.set_line(True, top_text, highlight_pos == 0)
        self.set_line(False, bottom_text, highlight_pos == 1)

    @staticmethod
    def _interpolate_color(start_color, end_color, ratio):
        start_r, start_g, start_b = (start_color >> 16) & 0xFF, (start_color >> 8) & 0xFF, start_color & 0xFF
        end_r, end_g, end_b = (end_color >> 16) & 0xFF, (end_color >> 8) & 0xFF, end_color & 0xFF
        r = int(start_r + (end_r - start_r) * ratio)
        g = int(start_g + (end_g - start_g) * ratio)
        b = int(start_b + (end_b - start_b) * ratio)
        return (r << 16) | (g << 8) | b

    def show_welcome(self):
        """Indítási üdvözlő képernyő, fokozatos háttérvilágítás- és
        szövegszín-felfutással. A Bitmap/Palette/Group EGYSZER épül fel,
        a fade lépései csak a paletta/szín értékét frissítik (nem
        építik újra a fát minden lépésben).

        Megjegyzés a time.sleep()-ről: ez egy egyszeri, korlátozott (kb.
        fél másodperces) indítási animáció, MIELŐTT a fő nem-blokkoló
        ciklus elindulna - nem esik a CircuitPython_instructions.md
        "no time.sleep() in main/continuous loops" szabálya alá, mert
        semmilyen más feladat (mérés, menü-navigáció) nem fut eközben.
        """
        border_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
        border_palette = displayio.Palette(1)
        border_palette[0] = WELCOME_BORDER_COLOR
        border_sprite = displayio.TileGrid(border_bitmap, pixel_shader=border_palette, x=0, y=0)

        inner_w = DISPLAY_WIDTH - WELCOME_BORDER * 2
        inner_h = DISPLAY_HEIGHT - WELCOME_BORDER * 2
        inner_bitmap = displayio.Bitmap(inner_w, inner_h, 1)
        inner_palette = displayio.Palette(1)
        inner_palette[0] = WELCOME_BG_COLOR
        inner_sprite = displayio.TileGrid(
            inner_bitmap, pixel_shader=inner_palette, x=WELCOME_BORDER, y=WELCOME_BORDER
        )

        text_area = label.Label(self.font, text=WELCOME_TEXT, color=0x000000)
        text_area.anchor_point = (0.5, 0.5)
        text_area.anchored_position = (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)

        welcome_group = displayio.Group()
        welcome_group.append(border_sprite)
        welcome_group.append(inner_sprite)
        welcome_group.append(text_area)
        self.display.root_group = welcome_group

        for duty in WELCOME_FADE_STEPS:
            self._backlight.duty_cycle = (
                (65535 - duty) if BACKLIGHT_ACTIVE_LOW else duty
            )
            ratio = duty / 65535.0
            text_area.color = self._interpolate_color(0x000000, WELCOME_TEXT_COLOR, ratio)
            time.sleep(WELCOME_STEP_DELAY)

        time.sleep(WELCOME_HOLD_SECONDS)

        # Visszaállítjuk a splash root_group-ot a menü-elrendezésre, hogy a
        # kővetkező self.display.root_group állítás (splash) ne maradjon
        # bent a menü indulásakor.
        self.display.root_group = self.splash


class MenuNavigator:
    """A menüfa bejárása: csúszóablak a főciklushoz, activate_keys-alapú
    aktiválás, leaf 'screen' nézet ki/be. Nem tud semmit a kijelzőről vagy
    a keypadről - csak állapotot tart és eseményekre reagál."""

    VISIBLE_ROWS = 2

    def __init__(self, menu_root):
        self._root = menu_root
        self.nav_stack = [(menu_root, 0, 0)]  # (siblings, index, top_index)
        self.in_leaf_screen = False

    def current_item(self):
        siblings, index, _ = self.nav_stack[-1]
        return siblings[index]

    def move_updown(self, delta):
        if self.in_leaf_screen:
            dprint("Leaf képernyő aktív: UP/DOWN a menüben hatástalan.")
            return
        siblings, index, top_index = self.nav_stack[-1]
        new_index = index + delta
        if not (0 <= new_index < len(siblings)):
            dprint("UP/DOWN -> hatar, nincs korbeforgas")
            return
        if new_index < top_index:
            top_index = new_index
        elif new_index >= top_index + self.VISIBLE_ROWS:
            top_index = new_index - (self.VISIBLE_ROWS - 1)
        self.nav_stack[-1] = (siblings, new_index, top_index)
        dprint("UP/DOWN -> index=%d (%s)" % (new_index, siblings[new_index]["label"]))

    def try_activate(self, key_name):
        """Visszaadja az aktivált leaf item-et, ha egy leaf 'screen'-be
        léptünk most (ekkor a hívó eldöntheti, kell-e action-t indítani),
        egyébként None."""
        if self.in_leaf_screen:
            dprint("Mar screen nezetben vagyunk, nincs teendo")
            return None
        item = self.current_item()
        allowed = item.get("activate_keys", {"ENTER", "RIGHT"})
        if key_name not in allowed:
            dprint(
                "%s hatastalan ezen az elemen (%s), csak %s aktival"
                % (key_name, item["label"], allowed)
            )
            return None
        if item["kind"] == "menu":
            self.nav_stack.append((item["children"], 0, 0))
            dprint("Belepes almenube: %s" % item["label"])
            return None
        self.in_leaf_screen = True
        dprint("Leaf screen mutatasa: %s" % item["label"])
        return item

    def confirm_action(self, key_name):
        """Csak akkor releváns, ha épp egy leaf 'screen' nézetben állunk.
        Ha az aktuális elemnek van 'action' kulcsa, és a lenyomott gomb
        szerepel a 'confirm_keys' halmazában, visszaadja az elemet (a hívó
        dispatch-elheti), és kilép a screen nézetből."""
        if not self.in_leaf_screen:
            return None
        item = self.current_item()
        action = item.get("action")
        if not action:
            return None
        confirm_keys = item.get("confirm_keys", {"ENTER"})
        if key_name not in confirm_keys:
            return None
        self.in_leaf_screen = False
        dprint("Action megerositve: %s" % action)
        return item

    def go_left(self):
        if self.in_leaf_screen:
            self.in_leaf_screen = False
            dprint("Kilepes screen nezetbol, vissza a bongeszeshez")
            return
        if len(self.nav_stack) > 1:
            self.nav_stack.pop()
            dprint("Egy szinttel feljebb")
        else:
            dprint("Mar a gyoker szinten vagyunk")

    def jump_to_root(self):
        self.in_leaf_screen = False
        self.nav_stack = [(self._root, 0, 0)]
        dprint("Hosszu ESC -> ugras a FOMENUbe")

    def render_state(self):
        """Visszaadja, mit kell a kijelzőnek mutatnia:
        (top_text, bottom_text, highlight_pos_or_None)."""
        if self.in_leaf_screen:
            top_text, bottom_text = self.current_item()["screen"]
            return top_text, bottom_text, None

        siblings, index, top_index = self.nav_stack[-1]
        highlight_pos = index - top_index

        top_item = siblings[top_index]
        top_text = top_item["label"]

        if top_index + 1 < len(siblings):
            bottom_text = siblings[top_index + 1]["label"]
        else:
            bottom_text = ""

        return top_text, bottom_text, highlight_pos


class FanoeTesterApp:
    """A projekt fő alkalmazás-osztálya: összeköti a Display-t, a Keypad-et
    és a MenuNavigator-t, futtatja a nem blokkoló főciklust."""

    def __init__(self):
        self.display = Display()
        self.keypad = Keypad(ROW_PINS, COLUMN_PINS, KEY_NAMES, LONG_PRESS_SEC)
        self.navigator = MenuNavigator(MENU_ROOT)
        self._actions = {
            "restart_device": self._action_restart_device,
        }

    def _render(self):
        top_text, bottom_text, highlight_pos = self.navigator.render_state()
        self.display.show_pair(top_text, bottom_text, highlight_pos)

    def _dispatch_action(self, item):
        """A menu_data.py 'action' kulcsát a megfelelő metódusra képezi le."""
        action = item.get("action")
        if not action:
            dprint("Statikus/kamu screen, nincs hozzarendelt action.")
            return
        handler = self._actions.get(action)
        if handler is None:
            dprint("Ismeretlen action: %s (nincs meg implementalva)" % action)
            return
        dprint("Action inditasa: %s" % action)
        handler()

    def _action_restart_device(self):
        dprint("Ujrainditas... (microcontroller.reset())")
        microcontroller.reset()

    def run(self):
        dprint("FanoeTesterApp starting")
        self.display.show_welcome()
        self._render()

        while True:
            event = self.keypad.poll()
            if not event:
                continue

            key_name, phase, duration = event

            if phase == "pressed":
                dprint("Lenyomva: %s" % key_name)
                if key_name in ("ENTER", "RIGHT"):
                    if self.navigator.in_leaf_screen:
                        confirmed_item = self.navigator.confirm_action(key_name)
                        if confirmed_item is not None:
                            self._dispatch_action(confirmed_item)
                    else:
                        self.navigator.try_activate(key_name)
                    self._render()
                elif key_name == "LEFT":
                    self.navigator.go_left()
                    self._render()
                elif key_name == "UP":
                    self.navigator.move_updown(-1)
                    self._render()
                elif key_name == "DOWN":
                    self.navigator.move_updown(1)
                    self._render()

            elif phase == "released" and key_name == "ESC":
                dprint("ESC felengedve, nyomvatartas: %.2f s" % duration)
                if self.keypad.is_long_press(duration):
                    self.navigator.jump_to_root()
                else:
                    self.navigator.go_left()
                self._render()


def main():
    app = FanoeTesterApp()
    app.run()


if __name__ == "__main__":
    main()