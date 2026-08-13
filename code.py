# code.py - FANOE tesztműszer, fő program
# OOP réteg - a menüfát a menu_data.py adja (pure data, lásd .copilot-
# instructions.md Section 5). Ez a fájl adja a viselkedést: kijelző,
# keypad, navigáció, és a jövőben ide kerül a mérési/beállítás logika
# dispatch-elése is (lásd FanoeTesterApp._dispatch_action).

import time
import analogio
import board
import busio
import digitalio
import displayio
import gc
import keypad
import microcontroller
import neopixel
import os
import pwmio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from fourwire import FourWire
from adafruit_st7789 import ST7789

from menu_data import MENU_ROOT
from tft_messages import TFT_MESSAGES

DEBUG = True
VERSION = "0v98 " # Ciklus indító képernyő felső sorában aktuális idősor megjelenítése


def dprint(*args, **kwargs) -> None:
    """Print debug messages when DEBUG mode is enabled."""
    if DEBUG:
        print(*args, **kwargs)


def get_int_setting(key, default):
    """settings.toml-ból int érték beolvasása os.getenv()-en keresztül.
    Az os.getenv() MINDIG stringet ad vissza (vagy None-t, ha a kulcs
    hiányzik) - ezért explicit int() konverzió kell. Hiányzó/hibás kulcs
    esetén a default-ra esik vissza."""
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        dprint(f"settings.toml: {key} erteke ervenytelen ('{raw}'), default={default}")
        return default


def save_setting(key, value):
    """Biztonságos settings.toml frissítés try-except OSError védelemmel
    (ha Fejlesztői módban vagyunk, a fájlrendszer írásvédett, OSError-t dob)."""
    settings = {}
    try:
        with open("settings.toml", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    settings[k.strip()] = v.strip()
    except OSError:
        pass

    settings[key] = str(value)

    try:
        with open("settings.toml", "w") as f:
            for k, v in settings.items():
                f.write(f"{k} = {v}\n")
        dprint(f"settings.toml mentve: {key} = {value}")
        return True
    except OSError as e:
        dprint(f"settings.toml mentési hiba (fejlesztői mód?): {e}")
        return False


def format_message(key, **kwargs):
    """TFT_MESSAGES kulcs feloldása és .format()-olása. Egysoros sablonnál
    (str) egy stringet ad vissza, kétsoros bejegyzésnél (tuple) egy
    (sor1, sor2) tuple-t - mindkettőt a hívó formázza a saját kwargs-aival."""
    template = TFT_MESSAGES[key]
    if isinstance(template, tuple):
        return tuple(line.format(**kwargs) for line in template)
    return template.format(**kwargs)

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

# Háttérvilágítás 9 diszkrét szintje (duty cycle)
BACKLIGHT_LEVELS = (96, 1024, 2048, 4096, 8192, 16384, 32768, 49152, 65535)

FONT_PATH = "/fonts/hu_127_ekezetes_20.pcf"
LINE1_Y = 0
LINE2_Y = 37

COLOR_BG_NORMAL = 0x000000
COLOR_TEXT_NORMAL = 0xFFFFFF
COLOR_TEXT_DANGER = 0xFF0000
COLOR_TEXT_WARNING = 0xFFFF00
COLOR_TEXT_SUCCESS = 0x00FF00
COLOR_BG_HIGHLIGHT = 0xFFCC00
COLOR_TEXT_HIGHLIGHT = 0x000000
COLOR_BORDER_HIGHLIGHT = 0x0033FF
BORDER_THICKNESS = 3

# --- FÁNOE RELÉ ÉS STÁTUSZ LED (Kézi BE / Ohm-mérő / Mérési ciklus módhoz) ---
RELAY_PIN = board.IO7
STATUS_LED_PIN = board.IO48  # WS2812 - MINDIG board.IO48 explicit, nem board.NEOPIXEL
STATUS_LED_GREEN = (0, 40, 0)
STATUS_LED_RED = (40, 0, 0)
STATUS_LED_ORANGE = (40, 16, 0)
STATUS_LED_YELLOW = (40, 40, 0)
MANUAL_HOLD_UPDATE_INTERVAL = 0.05  # ms-szamlalo frissitesi gyakorisaga

# --- OHM-MÉRŐ MÓD (folyamatos ellenállásmérés, IO14) ---
OHM_METER_PIN = board.IO14
OHM_METER_REF_OHMS = 150
OHM_METER_MAX_OHMS = 500
OHM_METER_SAMPLE_COUNT = 3  # egyszerű mozgóátlag a simításhoz
OHM_METER_UPDATE_INTERVAL = 0.1  # 100ms - lásd ADC_SAMPLE_INTERVAL_MS a logic.md-ben
OHM_METER_REPL_INTERVAL = 2.0  # REPL-re csak 2 mp-enként írunk

# --- AUTOMATIKUS MÉRÉSI CIKLUS (FanoeMeasurementCycle, lásd fanoe_tester_logic.md) ---
FANOE_CONTACT_PIN = board.IO6  # NO kontakt, feltételezett Pull.UP (zárva=LOW) - ellenőrizd!
T_SETTLE_S = 0.150  # fanoe_be utáni beállási idő, mielőtt fanoe_ell stabilitást figyelünk
OHM_TOLERANCE_OHM = 3  # "stabil" fanoe_ell tűrése 3 egymást követő minta között
ADC_SAMPLE_INTERVAL_S = 0.1  # ellenállás-mintavételezés periódusa a ciklus alatt
CYCLE_PROGRESS_UPDATE_INTERVAL = 0.05  # TFT ms-visszaszámláló frissítési gyakorisága

# --- settings.toml alapértékek (ha a fájl hiányzik/hibás, ezekre esünk vissza) ---
DEFAULT_T_ELO_MS = 2000
DEFAULT_T_BENT_MS = 6000
DEFAULT_T_UTO_MS = 5000
DEFAULT_R_ELL_OHM = 80
DEFAULT_BACKLIGHT_DUTY = 4096

# --- "Már a gyökérben vagyunk" villanás (LEFT/rövid ESC no-op-nál) ---
ROOT_BUMP_DURATION = 1.0

# --- WELCOME SCREEN KONFIGURÁCIÓ ---
WELCOME_TEXT = f"FÁNOE tester - {VERSION}"
WELCOME_BORDER = 8
WELCOME_BORDER_COLOR = 0xAA5AFF
WELCOME_BG_COLOR = 0x000080
WELCOME_TEXT_COLOR = 0xFFFF00
WELCOME_FADE_STEPS = (0, 96, 1024, 2048, 4096, 8192, 16384, 32768, 49152, 65535)
WELCOME_STEP_DELAY = 0.06  # egyszeri, indításkori animáció - lásd megjegyzés lent
WELCOME_HOLD_SECONDS = 0.9

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

    def set_operating_backlight(self, logical_duty):
        """A show_welcome() utáni, tartós üzemi fényerő beállítására -
        a settings.toml BACKLIGHT_DUTY értékéből hívja a FanoeTesterApp."""
        self._set_backlight(logical_duty)

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
        dprint(f"Loading {FONT_PATH}")
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

    def set_line(self, is_top, text, highlighted, bg_color=None, text_color=None):
        """bg_color/text_color megadásával a highlighted paramétert felülírja
        (pl. a Kézi BE mód piros "BE parancs kiadva" feliratához) - normál
        menü-használatnál ez a két paraméter üresen marad."""
        palette = self.top_palette if is_top else self.bottom_palette
        lbl = self.line1_label if is_top else self.line2_label
        if bg_color is not None and text_color is not None:
            palette[0] = bg_color
            palette[1] = bg_color
            lbl.color = text_color
        elif highlighted:
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
        text_area.anchor_point = (0.5, 0.7)
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


class RelayControl:
    """A FANOE relé (IO7) közvetlen ki/be kapcsolása - csak a Kézi BE
    módhoz; a mérési ciklus (FanoeMeasurementCycle) majd külön fogja
    kezelni ugyanezt a pint, saját logikával."""

    def __init__(self, pin):
        self._pin = digitalio.DigitalInOut(pin)
        self._pin.direction = digitalio.Direction.OUTPUT
        self._pin.value = False

    def on(self):
        self._pin.value = True

    def off(self):
        self._pin.value = False


class StatusLed:
    """WS2812 LED (board.IO48) - a Kézi BE, Ohm-mérő és a mérési ciklus
    állapotjelzésére. start()/stop() között foglalja/engedi el a pint, hogy
    más funkció is használhassa máskor, ha kell."""

    def __init__(self, pin):
        self._pin = pin
        self._pixel = None

    def start(self):
        if self._pixel is None:
            self._pixel = neopixel.NeoPixel(self._pin, 1, brightness=1.0, auto_write=True)

    def set_green(self):
        if self._pixel is not None:
            self._pixel[0] = STATUS_LED_GREEN

    def set_red(self):
        if self._pixel is not None:
            self._pixel[0] = STATUS_LED_RED

    def set_orange(self):
        if self._pixel is not None:
            self._pixel[0] = STATUS_LED_ORANGE

    def set_yellow(self):
        if self._pixel is not None:
            self._pixel[0] = STATUS_LED_YELLOW

    def stop(self):
        if self._pixel is not None:
            self._pixel.deinit()
            self._pixel = None


class OhmMeter:
    """FANOE ellenállás folyamatos mérése (IO14), 150R referenciával.
    R_fanoe = ref_ohms * V_adc / (V_ref - V_adc). start()/stop() között
    foglalja/engedi el az ADC pint. read_ohms() egy nyers mintát vesz,
    egy rövid mozgóátlaggal simítja, és a simított értéket adja vissza -
    vagy None-t, ha a kör gyakorlatilag szakadt (ADC a tápfeszültségen).
    Megjegyzés: hardveres felhúzó ellenállás NINCS beépítve az IO14-en,
    ezért teljesen nyitott R_fanoe esetén a csomópont NEM a v_ref közelébe
    lebeg (ahogy az OPEN_CIRCUIT_MARGIN_V-alapú ellenőrzés feltételezné),
    hanem egy köztes, board-függő szintre - ezen a panelen empirikusan
    ~1.70V / raw ADC ~33838 körül, stabilan. A FLOATING_RAW_* ablak ezt a
    konkrét jelenséget fogja el. Ha a hardver később felhúzó ellenállást
    kap, ez az ablak felülvizsgálandó/törölhető."""

    OPEN_CIRCUIT_MARGIN_V = 0.5
    FLOATING_RAW_CENTER = 33838
    FLOATING_RAW_TOLERANCE = 500  # +/- ADC count

    def __init__(self, pin, ref_ohms, sample_count):
        self._pin = pin
        self._ref_ohms = ref_ohms
        self._sample_count = sample_count
        self._adc = None
        self._samples = []

    def start(self):
        if self._adc is None:
            self._adc = analogio.AnalogIn(self._pin)
        self._samples = []

    def stop(self):
        if self._adc is not None:
            self._adc.deinit()
            self._adc = None
        self._samples = []

    def read_ohms(self):
        v_ref = self._adc.reference_voltage
        raw = self._adc.value
        v_adc = (raw / 65535) * v_ref

        is_near_vref = (v_ref - v_adc) < self.OPEN_CIRCUIT_MARGIN_V
        is_floating = abs(raw - self.FLOATING_RAW_CENTER) <= self.FLOATING_RAW_TOLERANCE

        if is_near_vref or is_floating:
            self._samples = []
            return None

        raw_ohms = self._ref_ohms * v_adc / (v_ref - v_adc)
        self._samples.append(raw_ohms)
        if len(self._samples) > self._sample_count:
            self._samples.pop(0)
        return sum(self._samples) / len(self._samples)


class FanoeMeasurementCycle:
    """Automatikus FÁNOE BE/KI mérési ciklus állapotgépe - lásd
    fanoe_tester_logic.md 'Automatikus mérési ciklus' szakasza. Nem tud
    semmit a kijelzőről/keypadről - csak IO7/IO6/IO14-et vezérel/olvas,
    és update()-tel léptethető. A hívó (FanoeTesterApp) felelős a
    non-blocking időzítésért (minden run() körben update()-et hív) és a
    renderelésért."""

    STATE_IDLE = "IDLE"
    STATE_T_ELO = "T_ELO"
    STATE_T_BENT = "T_BENT"
    STATE_T_UTO = "T_UTO"
    STATE_RESULT = "RESULT"
    STATE_ABORTED = "ABORTED"

    def __init__(self, relay, contact_pin, adc_pin, ref_ohms,
                 t_elo_ms, t_bent_ms, t_uto_ms, r_ell_ohm):
        self._relay = relay
        self._contact_pin = contact_pin
        self._adc_pin = adc_pin
        self._ref_ohms = ref_ohms
        self.t_elo_ms = t_elo_ms
        self.t_bent_ms = t_bent_ms
        self.t_uto_ms = t_uto_ms
        self.r_ell_ohm = r_ell_ohm

        self._contact = None
        self._adc = None
        self.state = self.STATE_IDLE
        self._reset_results()

    def _reset_results(self):
        self._cycle_start = None
        self._t_elo_end = None
        self._t_bent_end = None
        self._cycle_end = None
        self._last_adc_sample_time = 0
        self._ohm_samples = []
        self._r_ell_was_above = False
        self._prev_contact_closed = False  # él-detektáláshoz: fanoe_be/fanoe_ki

        self.fanoe_be_time = None
        self.fanoe_ki_time = None
        self.r_be_time = None
        self.r_ki_time = None
        self.fanoe_ell = None
        self.fanoe_ell_locked = False
        self.fanoe_szakadt = False
        
        # --- HIBA-FLAGEK ---
        self.error_already_closed = False    # Alaphelyzetben beragadt kontaktus
        self.error_premature_pullin = False  # Korai behúzás T_ELO alatt
        self.error_premature_dropout = False # Gerjesztés alatt váratlanul kinyitott kontaktus
        self.error_no_pullin = False
        self.error_no_dropout = False

        # EVALUATE eredménye, ms-ben/Ohm-ban, None ha nincs adat
        self.t_be_ms = None
        self.t_ki_ms = None
        self.r_be_ms = None
        self.r_ki_ms = None

    def start(self):
        """Ciklus indítása: pin-ek foglalása, kiinduló állapot ellenőrzése."""
        self._contact = digitalio.DigitalInOut(self._contact_pin)
        self._contact.direction = digitalio.Direction.INPUT
        self._contact.pull = digitalio.Pull.UP  # zárva (behúzva) = LOW

        self._reset_results()

        # Ellenőrizzük, hogy a kontaktus alaphelyzetben nyitva van-e (nem-e zárt még indítás előtt)
        if self.contact_closed:
            self.error_already_closed = True
            self.state = self.STATE_RESULT
            dprint("FanoeMeasurementCycle: ABORT - Contact already closed before relay trigger!")
            return False  # Sikertelen indítás a beragadt kontaktus miatt

        self._adc = analogio.AnalogIn(self._adc_pin)
        self._prev_contact_closed = False  # Mivel ellenőriztük, biztosan False volt

        now = time.monotonic()
        self._cycle_start = now
        self._t_elo_end = now + self.t_elo_ms / 1000
        self._relay.off()
        self.state = self.STATE_T_ELO
        dprint("FanoeMeasurementCycle: start -> T_ELO")
        return True

    def abort(self):
        """Azonnali, feltétel nélküli megszakítás - IO7 OFF, pinek elengedése, nincs EVALUATE."""
        self._relay.off()
        self.stop()  # Lekapcsolja a relét és deinit-eli az IO6 contact és IO14 ADC pineket!
        self.state = self.STATE_ABORTED
        dprint("FanoeMeasurementCycle: ABORTED (felhasznalo)")

    def stop(self):
        """Erőforrások elengedése (IO6/IO14 deinit). A leaf elhagyásakor,
        vagy a RESULT állapotba éréskor hívandó."""
        self._relay.off()
        if self._contact is not None:
            self._contact.deinit()
            self._contact = None
        if self._adc is not None:
            self._adc.deinit()
            self._adc = None
        self.state = self.STATE_IDLE

    @property
    def contact_closed(self):
        return not self._contact.value  # Pull.UP: zárva = LOW

    def remaining_ms(self):
        """Hátralévő idő az aktuális fázisban, ms-ben (0, ha nem aktív fázis)."""
        now = time.monotonic()
        if self.state == self.STATE_T_ELO:
            end = self._t_elo_end
        elif self.state == self.STATE_T_BENT:
            end = self._t_bent_end
        elif self.state == self.STATE_T_UTO:
            end = self._cycle_end
        else:
            return 0
        return max(0, int((end - now) * 1000))

    def _read_ohms(self):
        """Egy nyers Ohm-mintát ad vissza, vagy None-t szakadt kör esetén."""
        v_ref = self._adc.reference_voltage
        v_adc = (self._adc.value / 65535) * v_ref
        if v_ref - v_adc < 0.01:
            return None
        return self._ref_ohms * v_adc / (v_ref - v_adc)

    def _sample_ohms(self, now):
        ohms = self._read_ohms()

        if ohms is None:
            self.fanoe_szakadt = True
            self._ohm_samples = []
            return

        # fanoe_ell zárolás: T_SETTLE_S a fanoe_be_time után, 3 stabil minta
        if (not self.fanoe_ell_locked and self.fanoe_be_time is not None
                and now - self.fanoe_be_time >= T_SETTLE_S):
            self._ohm_samples.append(ohms)
            if len(self._ohm_samples) > 3:
                self._ohm_samples.pop(0)
            if len(self._ohm_samples) == 3:
                if max(self._ohm_samples) - min(self._ohm_samples) <= OHM_TOLERANCE_OHM:
                    self.fanoe_ell = self._ohm_samples[-1]
                    self.fanoe_ell_locked = True
                    dprint(f"FanoeMeasurementCycle: fanoe_ell zarolva = {self.fanoe_ell:.1f} Ohm")

        # r_be/r_ki küszöb-figyelés, a fanoe_ell zárolástól FÜGGETLENÜL
        above = ohms >= self.r_ell_ohm
        if above and not self._r_ell_was_above and self.r_be_time is None:
            self.r_be_time = now
            dprint(f"FanoeMeasurementCycle: r_be @ {now - self._cycle_start:.3f}s")
        if (not above) and self._r_ell_was_above:
            self.r_ki_time = now
            dprint(f"FanoeMeasurementCycle: r_ki @ {now - self._cycle_start:.3f}s")
        self._r_ell_was_above = above

    def _evaluate(self):
        # Ha bármilyen korai anomália történt (T_ELO alatti behúzás vagy T_BENT alatti elengedés),
        # az időeredmények érvénytelenek (None / N/A) lesznek!
        if self.error_premature_pullin or self.error_premature_dropout:
            self.fanoe_be_time = None
            self.t_be_ms = None
            self.fanoe_ki_time = None
            self.t_ki_ms = None
        else:
            if self.fanoe_be_time is not None:
                self.t_be_ms = int((self.fanoe_be_time - self._t_elo_end) * 1000)
            if self.fanoe_ki_time is not None:
                self.t_ki_ms = int((self.fanoe_ki_time - self._t_bent_end) * 1000)

        if self.r_be_time is not None:
            self.r_be_ms = int((self.r_be_time - self._t_elo_end) * 1000)
        if self.r_ki_time is not None:
            self.r_ki_ms = int((self.r_ki_time - self._t_bent_end) * 1000)
            
        dprint(
            f"FanoeMeasurementCycle: EVALUATE t_be={self.t_be_ms} "
            f"t_ki={self.t_ki_ms} fanoe_ell={self.fanoe_ell} "
            f"r_be={self.r_be_ms} r_ki={self.r_ki_ms} "
            f"err_prem_pullin={self.error_premature_pullin} "
            f"err_no_pullin={self.error_no_pullin} err_no_dropout={self.error_no_dropout} "
            f"szakadt={self.fanoe_szakadt}"
        )

    def update(self):
        """Nem blokkoló léptetés - minden run() körben hívandó, amíg a
        state nem IDLE/RESULT/ABORTED."""
        if self.state in (self.STATE_IDLE, self.STATE_RESULT, self.STATE_ABORTED):
            return

        now = time.monotonic()

        if self.state in (self.STATE_T_BENT, self.STATE_T_UTO):
            if now - self._last_adc_sample_time >= ADC_SAMPLE_INTERVAL_S:
                self._last_adc_sample_time = now
                self._sample_ohms(now)

        if self.state == self.STATE_T_ELO:
            # Figyeljük, hogy a T_ELO alatt bezár-e a kontaktus (korai behúzás hiba)
            if self.contact_closed:
                if not self.error_premature_pullin:
                    self.error_premature_pullin = True
                    dprint("FanoeMeasurementCycle: ERROR - Premature pullin during T_ELO!")

            if now >= self._t_elo_end:
                self.state = self.STATE_T_BENT
                self._relay.on()
                self._t_bent_end = now + self.t_bent_ms / 1000
                self._last_adc_sample_time = now
                dprint("FanoeMeasurementCycle: T_BENT, IO7 ON")

        elif self.state == self.STATE_T_BENT:
            current_closed = self.contact_closed
            if (self.fanoe_be_time is None and current_closed
                    and not self._prev_contact_closed):
                self.fanoe_be_time = now
                dprint(f"FanoeMeasurementCycle: fanoe_be @ {now - self._cycle_start:.3f}s")
            
            # Váratlan bontás (korai elengedés) figyelése T_BENT alatt, amennyiben már beépült
            if self.fanoe_be_time is not None and not current_closed:
                if not self.error_premature_dropout:
                    self.error_premature_dropout = True
                    dprint("FanoeMeasurementCycle: ERROR - Premature dropout during T_BENT!")

            self._prev_contact_closed = current_closed
            if now >= self._t_bent_end:
                if self.fanoe_be_time is None:
                    self.error_no_pullin = True
                    dprint("FanoeMeasurementCycle: ERROR_NO_PULLIN")
                self.state = self.STATE_T_UTO
                self._relay.off()
                self._cycle_end = now + self.t_uto_ms / 1000
                dprint("FanoeMeasurementCycle: T_UTO, IO7 OFF")

        elif self.state == self.STATE_T_UTO:
            current_closed = self.contact_closed
            
            # Csak akkor figyeljük a T_UTO alatti nyitást, ha NEM volt korai elengedés a T_BENT-ben
            if not self.error_premature_dropout:
                if (self.fanoe_ki_time is None and self.fanoe_be_time is not None
                        and not current_closed and self._prev_contact_closed):
                    self.fanoe_ki_time = now
                    dprint(f"FanoeMeasurementCycle: fanoe_ki @ {now - self._cycle_start:.3f}s")
            
            self._prev_contact_closed = current_closed
            
            if now >= self._cycle_end:
                # HIBA: Csak akkor adunk "nem ejtett el" hibát, ha NEM volt korai elengedés, 
                # ÉS a ciklus végén a kontaktus MÉG MINDIG ZÁRT (beragadt).
                if self.fanoe_ki_time is None and not self.error_premature_dropout:
                    if current_closed:  # Ha a ciklus végén is zárt maradt -> BERAGADT
                        self.error_no_dropout = True
                        dprint("FanoeMeasurementCycle: ERROR_NO_DROPOUT (beragadt)")
                
                self._evaluate()
                self.state = self.STATE_RESULT


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
        dprint(f"UP/DOWN -> index={new_index} ({siblings[new_index]['label']})")

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
                f"{key_name} hatastalan ezen az elemen ({item['label']}), csak {allowed} aktival"
            )
            return None
        if item["kind"] == "menu":
            self.nav_stack.append((item["children"], 0, 0))
            dprint(f"Belepes almenube: {item['label']}")
            return None
        self.in_leaf_screen = True
        dprint(f"Leaf screen mutatasa: {item['label']}")
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
        confirm_keys = item.get("confirm_keys", set())
        if key_name not in confirm_keys:
            return None
        self.in_leaf_screen = False
        dprint(f"Action megerositve: {action}")
        return item

    def go_left(self):
        """Visszaadja: True, ha történt tényleges lépés (screen bezárása
        vagy egy szinttel feljebb lépés), False, ha már a gyökérszinten
        voltunk és nem történt semmi (a hívó ilyenkor jelezhet a usernek)."""
        if self.in_leaf_screen:
            self.in_leaf_screen = False
            dprint("Kilepes screen nezetbol, vissza a bongeszeshez")
            return True
        if len(self.nav_stack) > 1:
            self.nav_stack.pop()
            dprint("Egy szinttel feljebb")
            return True
        dprint("Mar a gyoker szinten vagyunk")
        return False

    def jump_to_root(self):
        self.in_leaf_screen = False
        self.nav_stack = [(self._root, 0, 0)]
        dprint("Hosszu ESC -> ugras a FOMENUbe")

    def push_result_list(self, labels):
        """Egy futásidőben generált, egysoros szövegekből álló listát tol a
        nav_stack tetejére - ugyanaz a csúszóablakos/kiemelt böngészés
        jelenik meg rá, mint a menüpontoknál (pl. RESULT képernyő a mérés
        után). ESC/BAL ugyanúgy egy szinttel visszalép, mint bármelyik
        almenüből. 'labels' egy lista sima stringekből - itt csomagoljuk
        be leaf-dict-té, üres activate_keys-szel (ENTER/JOBB hatástalan
        rajtuk, csak böngészhetők)."""
        lines = [
            {"label": text, "kind": "leaf", "activate_keys": set()}
            for text in labels
        ]
        self.in_leaf_screen = False
        self.nav_stack.append((lines, 0, 0))
        dprint(f"RESULT lista megjelenitve, {len(lines)} elem")

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
        self._t_elo_ms = get_int_setting("T_ELO_MS", DEFAULT_T_ELO_MS)
        self._t_bent_ms = get_int_setting("T_BENT_MS", DEFAULT_T_BENT_MS)
        self._t_uto_ms = get_int_setting("T_UTO_MS", DEFAULT_T_UTO_MS)
        self._r_ell_ohm = get_int_setting("R_ELL_OHM", DEFAULT_R_ELL_OHM)
        self._backlight_duty = get_int_setting("BACKLIGHT_DUTY", DEFAULT_BACKLIGHT_DUTY)
        dprint(
            f"settings.toml: t_elo={self._t_elo_ms}ms t_bent={self._t_bent_ms}ms "
            f"t_uto={self._t_uto_ms}ms r_ell={self._r_ell_ohm}Ohm "
            f"backlight={self._backlight_duty}"
        )

        self.display = Display()
        self.keypad = Keypad(ROW_PINS, COLUMN_PINS, KEY_NAMES, LONG_PRESS_SEC)
        self.navigator = MenuNavigator(MENU_ROOT)
        self.relay = RelayControl(RELAY_PIN)
        self.led = StatusLed(STATUS_LED_PIN)
        self.ohm_meter = OhmMeter(OHM_METER_PIN, OHM_METER_REF_OHMS, OHM_METER_SAMPLE_COUNT)
        self.measurement_cycle = FanoeMeasurementCycle(
            self.relay, FANOE_CONTACT_PIN, OHM_METER_PIN, OHM_METER_REF_OHMS,
            self._t_elo_ms, self._t_bent_ms, self._t_uto_ms, self._r_ell_ohm,
        )
        self._manual_hold_active = False  # True, amíg a "FÁNOE KÉZI BE" leaf-en állunk
        self._manual_hold_pressed = False  # True, amíg ENTER lenyomva tartva
        self._manual_hold_start = None
        self._manual_hold_last_update = 0
        self._manual_hold_contact = None  # IO6 DigitalInOut, csak a leaf aktív ideje alatt él
        self._manual_hold_pullin_ms = None  # None = még nem húzott be; -1 = alapból zárva volt; utána a behúzás (ms)
        self._ohm_meter_active = False  # True, amíg az "ELLENÁLLÁS MÉRÉS" leaf-en állunk
        self._ohm_meter_last_update = 0
        self._ohm_meter_last_repl = 0
        self._cycle_active = False  # True, amíg a mérési ciklus fut (T_ELO/T_BENT/T_UTO)
        self._cycle_last_update = 0
        self._suppress_next_esc_release = False  # ciklus-megszakítás utáni ESC-felengedés elnyelése
        self._root_bump_until = 0  # 0 = inaktív; monotonic timestamp, ameddig villog
        self._save_msg_until = 0  # 0 = inaktív; monotonic timestamp, ameddig a mentés-üzenet látszik
        
        # --- Szerkesztési állapottartók ---
        self._active_setting_key = None
        self._active_setting_val = 0
        self._active_setting_min = 0
        self._active_setting_max = 0
        self._active_setting_step = 0
        self._active_setting_unit = ""
        
        # --- Háttérvilágítás szerkesztési index ---
        self._backlight_index = 0

        self._actions = {
            "restart_device": self._action_restart_device,
            "info_cpu_freq": self._action_info_cpu_freq,
            "info_cpu_temp": self._action_info_cpu_temp,
            "info_used_ram": self._action_info_used_ram,
            "info_free_ram": self._action_info_free_ram,
            "info_used_flash": self._action_info_used_flash,
            "info_free_flash": self._action_info_free_flash,
            "info_board_id": self._action_info_board_id,
            "info_chip_uid": self._action_info_chip_uid,
            "info_fw_version": self._action_info_fw_version,
            "info_sw_version": self._action_info_sw_version,
            "fanoe_manual_hold_enter": self._action_fanoe_manual_hold_enter,
            "ohm_meter_enter": self._action_ohm_meter_enter,
            "start_measurement_cycle": self._action_start_measurement_cycle,
            "settings_edit_numeric": self._action_settings_edit_numeric,
            "backlight_edit": self._action_backlight_edit,
        }

    def _render(self):
        top_text, bottom_text, highlight_pos = self.navigator.render_state()
        # Ha épp a FÁNOE BE/KI MÉRÉS leaf screen-en állunk, felülírjuk a felső sort a dinamikus időkkel
        item = self.navigator.current_item()
        if self.navigator.in_leaf_screen and item.get("action") == "start_measurement_cycle":
            top_text = f" {self._t_elo_ms} ▶ {self._t_bent_ms} ▶ {self._t_uto_ms} ms"
        self.display.show_pair(top_text, bottom_text, highlight_pos)

    def _dispatch_action(self, item):
        """A menu_data.py 'action' kulcsát a megfelelő metódusra képezi le.
        Visszaadja a handler eredményét: True, ha a handler már renderelt
        saját (élő) tartalmat a kijelzőre (a hívónak nem kell generikus
        render-t futtatnia utána), egyébként None/False."""
        action = item.get("action")
        if not action:
            dprint("Statikus/kamu screen, nincs hozzarendelt action.")
            return False
        handler = self._actions.get(action)
        if handler is None:
            dprint(f"Ismeretlen action: {action} (nincs meg implementalva)")
            return False
        dprint(f"Action inditasa: {action}")
        return handler()

    def _action_restart_device(self):
        dprint("Ujrainditas... (microcontroller.reset())")
        microcontroller.reset()

    def _action_info_cpu_freq(self):
        freq_mhz = microcontroller.cpu.frequency // 1_000_000
        dprint(f"CPU frekvencia: {freq_mhz} MHz")
        self.display.show_pair(" ESP32-S3 CPU órajel:", f"     {freq_mhz} MHz", None)
        return True

    def _action_info_cpu_temp(self):
        try:
            temp_c = microcontroller.cpu.temperature
            text = f"     {temp_c:.0f} °C"
            dprint(f"CPU homerseklet: {temp_c:.0f} C")
        except (AttributeError, NotImplementedError):
            dprint("microcontroller.cpu.temperature nem elerheto ezen a chipen")
            text = "     nem elerheto"
        self.display.show_pair(" ESP32-S3 CPU hőfok:", text, None)
        return True

    def _action_info_used_ram(self):
        used_kb = gc.mem_alloc() // 1024
        dprint(f"Használt RAM: {used_kb} KB")
        self.display.show_pair(" Használt RAM memória:", f"    {used_kb} KB", None)
        return True

    def _action_info_free_ram(self):
        free_kb = gc.mem_free() // 1024
        dprint(f"Szabad RAM: {free_kb} KB")
        self.display.show_pair(" Szabad RAM memória:", f"    {free_kb} KB", None)
        return True

    def _action_info_used_flash(self):
        fs_stat = os.statvfs('/')
        block_size = fs_stat[0]
        total_bytes = block_size * fs_stat[2]
        free_bytes = block_size * fs_stat[3]
        used_mb = (total_bytes - free_bytes) / (1024 * 1024)
        dprint(f"Foglalt flash: {used_mb:.1f} MB")
        self.display.show_pair(" Foglalt flash memória:", f"    {used_mb:.1f} MB", None)
        return True

    def _action_info_free_flash(self):
        fs_stat = os.statvfs('/')
        free_mb = (fs_stat[0] * fs_stat[3]) / (1024 * 1024)
        dprint(f"Szabad flash: {free_mb:.1f} MB")
        self.display.show_pair(" Szabad flash memória:", f"    {free_mb:.1f} MB", None)
        return True

    def _action_info_board_id(self):
        board_id = os.uname().machine
        dprint(f"Board azonosito: {board_id}")
        self.display.show_pair(" Board azonosító:", "  " + board_id[:20], None)
        return True

    def _action_info_chip_uid(self):
        uid_hex = ":".join(f"{b:02X}" for b in microcontroller.cpu.uid)
        dprint(f"Chip UID: {uid_hex}")
        self.display.show_pair(" Chip UID:", "  " + uid_hex, None)
        return True

    def _action_info_fw_version(self):
        cpy_fw = os.uname().version
        dprint(f"CircuitPython firmware verzió: {cpy_fw}")
        self.display.show_pair(" cPy firmware verzió:", f"  {cpy_fw}", None)
        return True
    
    def _action_info_sw_version(self):
        dprint(f"Software verzio: {VERSION}")
        self.display.show_pair(" Software verzió:", f"   {VERSION}", None)
        return True

    def _action_fanoe_manual_hold_enter(self):
        """A 'FÁNOE KÉZI BE' leaf-be lépéskor fut le egyszer: a LED-et
        zöldre állítja, jelzi, hogy mostantól az ENTER folyamatos nyomva
        tartását figyeljük. Létrehozza a kézi IO6 digitális bemenetet.
        A statikus screen-t a generikus render mutatja (ezért False-t adunk vissza)."""
        self._manual_hold_active = True
        self._manual_hold_contact = digitalio.DigitalInOut(FANOE_CONTACT_PIN)
        self._manual_hold_contact.direction = digitalio.Direction.INPUT
        self._manual_hold_contact.pull = digitalio.Pull.UP  # zárva (behúzva) = LOW
        self.led.start()
        self.led.set_green()
        dprint("Kezi BE mod aktiv, LED zold")
        return False

    def _cleanup_manual_hold(self):
        """Amint elhagyjuk a 'FÁNOE KÉZI BE' leaf-et (BAL/ESC), a relét és
        a LED-et biztonságosan lekapcsoljuk/elengedjük - nem visszük ki az
        állapotot az almenüből."""
        if not self._manual_hold_active:
            return
        self._manual_hold_active = False
        self._manual_hold_pressed = False
        self.relay.off()
        if self._manual_hold_contact is not None:
            self._manual_hold_contact.deinit()
            self._manual_hold_contact = None
        self.led.stop()
        dprint("Kezi BE mod elhagyva - relay/LED/contact torolve")

    def _action_ohm_meter_enter(self):
        """Az 'ELLENÁLLÁS MÉRÉS' leaf-be lépéskor fut le egyszer: elindítja
        az ADC-t, a LED-et narancssárgára állítja, és felrajzolja a
        kezdő képet. A tényleges élő frissítés a run() fő ciklusában
        történik (lásd _ohm_meter_active)."""
        self._ohm_meter_active = True
        self._ohm_meter_last_update = time.monotonic()
        self._ohm_meter_last_repl = self._ohm_meter_last_update
        self.ohm_meter.start()
        self.led.start()
        self.led.set_orange()
        self.display.set_line(True, " Ohm-mérés üzemmód", False)
        self.display.set_line(
            False, "  mérés indul...", False,
            bg_color=COLOR_BG_NORMAL, text_color=COLOR_TEXT_WARNING,
        )
        dprint("Ohm-mero mod aktiv, LED narancs")
        return True

    def _cleanup_ohm_meter(self):
        """Amint elhagyjuk az 'ELLENÁLLÁS MÉRÉS' leaf-et (BAL/ESC), az
        ADC-t és a LED-et elengedjük."""
        if not self._ohm_meter_active:
            return
        self._ohm_meter_active = False
        self.ohm_meter.stop()
        self.led.stop()
        dprint("Ohm-mero mod elhagyva - ADC/LED torolve")

    def _action_start_measurement_cycle(self):
        """A 'FÁNOE BE/KI MÉRÉS' leaf-en belüli megerősítő ENTER-re fut le
        (confirm_keys minta) - elindítja a FanoeMeasurementCycle-t."""
        self._cycle_active = True
        self._cycle_last_update = time.monotonic()
        self.led.start()
        
        # Ciklus indítása (visszatérési értéke jelzi, ha indítási hiba történt)
        started_ok = self.measurement_cycle.start()
        if not started_ok:
            # Ha már az elején hiba volt (pl. beragadt zárva a kontaktus), közvetlenül a RESULT lista jön
            self._finish_measurement_cycle()
            return True

        self._render_cycle_progress(self.measurement_cycle.state)
        dprint("Meresi ciklus inditva")
        return True

    def _action_settings_edit_numeric(self):
        """Közös handler a numerikus (idő / ohm) beállítások szerkesztéséhez."""
        item = self.navigator.current_item()
        self._active_setting_key = item.get("setting_key")
        self._active_setting_min = item.get("min_val", 0)
        self._active_setting_max = item.get("max_val", 10000)
        self._active_setting_step = item.get("step", 1)
        self._active_setting_unit = item.get("unit", "")

        # Betöltjük az aktuális értéket az App attribútumaiból
        if self._active_setting_key == "T_ELO_MS":
            self._active_setting_val = self._t_elo_ms
        elif self._active_setting_key == "T_BENT_MS":
            self._active_setting_val = self._t_bent_ms
        elif self._active_setting_key == "T_UTO_MS":
            self._active_setting_val = self._t_uto_ms
        elif self._active_setting_key == "R_ELL_OHM":
            self._active_setting_val = self._r_ell_ohm

        top_text, _ = item["screen"]
        self.display.show_pair(top_text, f" {self._active_setting_val} {self._active_setting_unit} [{self._active_setting_min}-{self._active_setting_max}]", None)
        dprint(f"Szerkesztő indítva: {self._active_setting_key} = {self._active_setting_val}")
        return True

    def _action_backlight_edit(self):
        """TFT fényerő állítás (9 diszkrét szint, élő előnézettel)."""
        self._active_setting_key = "BACKLIGHT_DUTY"
        
        # Megkeressük a legközelebbi indexet a BACKLIGHT_LEVELS listában
        closest_diff = 999999
        self._backlight_index = 0
        for i, val in enumerate(BACKLIGHT_LEVELS):
            diff = abs(val - self._backlight_duty)
            if diff < closest_diff:
                closest_diff = diff
                self._backlight_index = i

        top_text, _ = self.navigator.current_item()["screen"]
        # Megjelenítés: "9 / [index+1]" (1-től 9-ig számozva a usernek)
        self.display.show_pair(top_text, f"   9 / {self._backlight_index + 1}    [1-9]", None)
        dprint(f"Fényerő szerkesztő indítva: index={self._backlight_index}, duty={BACKLIGHT_LEVELS[self._backlight_index]}")
        return True

    def _render_cycle_progress(self, state):
        """A T_ELO/T_BENT/T_UTO fázisok élő kijelzése: fázisnévvel/színnel
        a felső sor, ms-visszaszámlálással az alsó - a LED ugyanazt a
        színt mutatja."""
        if state == FanoeMeasurementCycle.STATE_T_ELO:
            label_text, color = " FÁVA holtidő fut", COLOR_TEXT_SUCCESS
            self.led.set_green()
        elif state == FanoeMeasurementCycle.STATE_T_BENT:
            label_text, color = " BE parancs kiadva", COLOR_TEXT_DANGER
            self.led.set_red()
        elif state == FanoeMeasurementCycle.STATE_T_UTO:
            label_text, color = " Mérési utóidő fut", COLOR_TEXT_WARNING
            self.led.set_yellow()
        else:
            return

        remaining_ms = self.measurement_cycle.remaining_ms()
        self.display.set_line(True, label_text, False, bg_color=COLOR_BG_NORMAL, text_color=color)
        self.display.set_line(
            False, f"     {remaining_ms} ms", False,
            bg_color=COLOR_BG_NORMAL, text_color=COLOR_TEXT_NORMAL,
        )

    def _finish_measurement_cycle(self):
        """A ciklus RESULT állapotba érésekor fut le: összeállítja a
        lapozható eredmény-listát, elengedi az ADC/kontakt/LED-et, és a
        MenuNavigator-on keresztül megjeleníti (ugyanaz a csúszóablakos
        renderelés, mint a menü böngészésnél)."""
        cyc = self.measurement_cycle
        lines = []

        # 1. Ha el sem tudott indulni, mert alapból zárva volt
        if getattr(cyc, "error_already_closed", False):
            lines.append(format_message("result_err_already_closed"))
            lines.append(format_message("result_t_be", value=format_message("value_na")))
            lines.append(format_message("result_t_ki", value=format_message("value_na")))
            lines.append(format_message("result_fanoe_ell", value=format_message("value_na")))
        else:
            # 2. Normál lefutás (vagy futás közbeni hibák kezelése)
            if getattr(cyc, "error_premature_pullin", False):
                lines.append(format_message("result_err_premature_pullin"))
            if cyc.error_no_pullin:
                lines.append(format_message("result_err_no_pullin"))
            if getattr(cyc, "error_premature_dropout", False):
                lines.append(format_message("result_err_premature"))
            if cyc.error_no_dropout:
                lines.append(format_message("result_err_no_dropout"))

            t_be_val = str(cyc.t_be_ms) if cyc.t_be_ms is not None else format_message("value_na")
            lines.append(format_message("result_t_be", value=t_be_val))

            t_ki_val = str(cyc.t_ki_ms) if cyc.t_ki_ms is not None else format_message("value_na")
            lines.append(format_message("result_t_ki", value=t_ki_val))

            if cyc.fanoe_szakadt:
                ell_val = format_message("value_szakadt")
            elif cyc.fanoe_ell is not None:
                ell_val = f"{cyc.fanoe_ell:.1f}"
            else:
                ell_val = format_message("value_na")
            lines.append(format_message("result_fanoe_ell", value=ell_val))

            r_be_val = str(cyc.r_be_ms) if cyc.r_be_ms is not None else format_message("value_na")
            lines.append(format_message("result_r_be", value=r_be_val))

            r_ki_val = str(cyc.r_ki_ms) if cyc.r_ki_ms is not None else format_message("value_na")
            lines.append(format_message("result_r_ki", value=r_ki_val))

        self._cycle_active = False
        self.led.stop()
        cyc.stop()
        self.navigator.push_result_list(lines)
        self._render()
        dprint("Meresi ciklus kesz - RESULT lista megjelenitve")

    def _abort_measurement_cycle(self):
        """ESC bármikor, az aktív fázisok alatt - AZONNALI megszakítás."""
        self.measurement_cycle.abort()
        self._cycle_active = False
        self.led.stop()
        top_text, bottom_text = format_message("aborted_by_user")
        self.display.show_pair(top_text, bottom_text, None)
        self._suppress_next_esc_release = True
        dprint("Meresi ciklus megszakitva (ESC)")

    def _cleanup_measurement_cycle(self):
        """Védőháló: ha a ciklus valamiért aktívan maradna, amikor a
        _cleanup_active_modes lefut, biztonságosan leállítja."""
        if not self._cycle_active:
            return
        self._cycle_active = False
        self.measurement_cycle.stop()
        self.led.stop()
        dprint("Meresi ciklus vedohalo-takaritas lefutott")

    def _cleanup_active_modes(self):
        """Minden folyamatos/speciális almenü-mód takarítása egy helyen -
        bővíthető, ha később újabb ilyen mód készül."""
        if self._active_setting_key == "BACKLIGHT_DUTY":
            self.display.set_operating_backlight(self._backlight_duty)  # élő előnézet visszavonása
        self._active_setting_key = None
        self._cleanup_manual_hold()
        self._cleanup_ohm_meter()
        self._cleanup_measurement_cycle()

    def _handle_go_left(self):
        """LEFT vagy rövid ESC közös kezelése: ha volt tényleges lépés,
        normál render; ha már a gyökérszinten voltunk (no-op), egy rövid
        villanás jelzi ezt a usernek, majd magától visszavált."""
        #self._active_setting_key = None  # Szerkesztési állapot törlése balra lépéskor
        moved = self.navigator.go_left()
        self._cleanup_active_modes()
        if moved:
            self._render()
        else:
            top_text, bottom_text = format_message("already_at_root")
            self.display.set_line(
                True, top_text, False,
                bg_color=COLOR_BG_NORMAL, text_color=COLOR_BORDER_HIGHLIGHT,
            )
            self.display.set_line(
                False, bottom_text, False,
                bg_color=COLOR_BG_NORMAL, text_color=COLOR_BORDER_HIGHLIGHT,
            )
            self._root_bump_until = time.monotonic() + ROOT_BUMP_DURATION

    def run(self):
        dprint("FanoeTesterApp starting")
        self.display.show_welcome()
        self.display.set_operating_backlight(self._backlight_duty)
        self._render()

        while True:
            event = self.keypad.poll()

            if self._manual_hold_pressed:
                now = time.monotonic()
                if now - self._manual_hold_last_update >= MANUAL_HOLD_UPDATE_INTERVAL:
                    elapsed_ms = int((now - self._manual_hold_start) * 1000)

                    # Ha alapból zárva volt (-1), ne számoljunk időt, csak jelezzük a hibát
                    if self._manual_hold_pullin_ms == -1:
                        text = "   [ ALAPBÓL ZÁRVA ]"
                        color = COLOR_TEXT_DANGER
                    else:
                        if (self._manual_hold_pullin_ms is None
                                and not self._manual_hold_contact.value):  # Pull.UP: zárva = LOW
                            self._manual_hold_pullin_ms = elapsed_ms
                            dprint(f"Kezi BE: behuzott @ {elapsed_ms} ms")

                        if self._manual_hold_pullin_ms is not None:
                            text = f"  behúzott: {self._manual_hold_pullin_ms} ms"
                            color = COLOR_TEXT_SUCCESS
                        else:
                            text = f"     {elapsed_ms} ms"
                            color = COLOR_TEXT_NORMAL

                    self.display.set_line(False, text, False, bg_color=COLOR_BG_NORMAL, text_color=color)
                    self._manual_hold_last_update = now

            if self._ohm_meter_active:
                now = time.monotonic()
                if now - self._ohm_meter_last_update >= OHM_METER_UPDATE_INTERVAL:
                    ohms = self.ohm_meter.read_ohms()
                    if ohms is None:
                        text = format_message("ohm_meter_open")
                    elif ohms > OHM_METER_MAX_OHMS:
                        text = format_message("ohm_meter_high")
                    else:
                        text = f"{ohms:.1f} Ω"
                    self.display.set_line(
                        False, "  " + text, False,
                        bg_color=COLOR_BG_NORMAL, text_color=COLOR_TEXT_WARNING,
                    )
                    self._ohm_meter_last_update = now

                    if now - self._ohm_meter_last_repl >= OHM_METER_REPL_INTERVAL:
                        dprint(f"Ohm-mero: {text}")
                        self._ohm_meter_last_repl = now

            if self._cycle_active:
                self.measurement_cycle.update()
                if self.measurement_cycle.state == FanoeMeasurementCycle.STATE_RESULT:
                    self._finish_measurement_cycle()
                else:
                    now = time.monotonic()
                    if now - self._cycle_last_update >= CYCLE_PROGRESS_UPDATE_INTERVAL:
                        self._render_cycle_progress(self.measurement_cycle.state)
                        self._cycle_last_update = now

            if self._root_bump_until and time.monotonic() >= self._root_bump_until:
                self._root_bump_until = 0
                self._render()

            if self._save_msg_until and time.monotonic() >= self._save_msg_until:
                self._save_msg_until = 0
                self._cleanup_active_modes()
                self.navigator.go_left()
                self._render()

            if not event:
                continue

            key_name, phase, duration = event

            if phase == "pressed":
                dprint(f"Lenyomva: {key_name}")

                if self._cycle_active:
                    if key_name == "ESC":
                        self._abort_measurement_cycle()
                    else:
                        dprint(f"{key_name} hatastalan - meresi ciklus aktiv")
                    continue

                if self._manual_hold_active and key_name == "ENTER":
                    self._manual_hold_pressed = True
                    self._manual_hold_start = time.monotonic()
                    self._manual_hold_last_update = self._manual_hold_start
                    
                    # Ellenőrizzük a kezdeti állapotot: már most zárva van?
                    initially_closed = not self._manual_hold_contact.value if self._manual_hold_contact else False
                    
                    if initially_closed:
                        self._manual_hold_pullin_ms = -1  # -1 = Alapból zárva volt
                        dprint("Kezi BE HIBA: A kontaktus már indításkor zárva volt!")
                    else:
                        self._manual_hold_pullin_ms = None

                    self.relay.on()
                    self.led.set_red()
                    dprint("Vezérlő parancs kiadva - IO7")
                    
                    self.display.set_line(
                        True, " BE parancs kiadva", False,
                        bg_color=COLOR_BG_NORMAL, text_color=COLOR_TEXT_DANGER,
                    )
                    
                    if initially_closed:
                        self.display.set_line(
                            False, "   [ ALAPBÓL ZÁRVA ]", False,
                            bg_color=COLOR_BG_NORMAL, text_color=COLOR_TEXT_DANGER,
                        )
                    else:
                        self.display.set_line(
                            False, "     0 ms", False,
                            bg_color=COLOR_BG_NORMAL, text_color=COLOR_TEXT_NORMAL,
                        )
                    continue

                if key_name == "ENTER":
                    if self.navigator.in_leaf_screen and self._active_setting_key is not None:
                        # Mentés a settings.toml-ba
                        save_val = BACKLIGHT_LEVELS[self._backlight_index] if self._active_setting_key == "BACKLIGHT_DUTY" else self._active_setting_val
                        success = save_setting(self._active_setting_key, save_val)
                        
                        # Frissítjük az App belső változóját is
                        if self._active_setting_key == "T_ELO_MS":
                            self._t_elo_ms = self._active_setting_val
                            self.measurement_cycle.t_elo_ms = self._t_elo_ms
                        elif self._active_setting_key == "T_BENT_MS":
                            self._t_bent_ms = self._active_setting_val
                            self.measurement_cycle.t_bent_ms = self._t_bent_ms
                        elif self._active_setting_key == "T_UTO_MS":
                            self._t_uto_ms = self._active_setting_val
                            self.measurement_cycle.t_uto_ms = self._t_uto_ms
                        elif self._active_setting_key == "R_ELL_OHM":
                            self._r_ell_ohm = self._active_setting_val
                            self.measurement_cycle.r_ell_ohm = self._r_ell_ohm
                        elif self._active_setting_key == "BACKLIGHT_DUTY":
                            self._backlight_duty = save_val
                            self.display.set_operating_backlight(self._backlight_duty)

                        # Vizuális visszajelzés a mentésről - a "Sikeres/Sikertelen mentés"
                        # üzenet 0.8s-ig látszik, a run() ciklus eleji
                        # _save_msg_until blokk zárja le
                        if success:
                            top_text, bottom_text = format_message("save_ok") # pl. ("Sikeres mentés", "")
                        else:
                            top_text, bottom_text = format_message("save_fail") # pl. ("Nem menthető", "Fejlesztői módban")
                            
                        self.display.show_pair(top_text, bottom_text, None)
                        self._save_msg_until = time.monotonic() + 1.1
                        continue
 
                    elif self.navigator.in_leaf_screen:
                        confirmed_item = self.navigator.confirm_action(key_name)
                        if confirmed_item is not None:
                            rendered_custom = self._dispatch_action(confirmed_item)
                            if not rendered_custom:
                                self._render()
                        else:
                            self._render()
                    else:
                        activated_item = self.navigator.try_activate(key_name)
                        if activated_item is not None and activated_item.get("auto_dispatch"):
                            rendered_custom = self._dispatch_action(activated_item)
                            if not rendered_custom:
                                self._render()
                        else:
                            self._render()

                elif key_name == "RIGHT":
                    if not self.navigator.in_leaf_screen:
                        activated_item = self.navigator.try_activate(key_name)
                        if activated_item is not None and activated_item.get("auto_dispatch"):
                            rendered_custom = self._dispatch_action(activated_item)
                            if not rendered_custom:
                                self._render()
                        else:
                            self._render()

                elif key_name == "LEFT":
                    self._handle_go_left()

                elif key_name == "UP":
                    if self.navigator.in_leaf_screen and self._active_setting_key is not None:
                        top_text, _ = self.navigator.current_item()["screen"]
                        if self._active_setting_key == "BACKLIGHT_DUTY":
                            self._backlight_index = min(len(BACKLIGHT_LEVELS) - 1, self._backlight_index + 1)
                            # Élő előnézet (live preview)
                            self.display.set_operating_backlight(BACKLIGHT_LEVELS[self._backlight_index])
                            self.display.show_pair(top_text, f"   9 / {self._backlight_index + 1}    [1-9]", None)
                            dprint(f"Fényerő index növelve: {self._backlight_index}")
                        else:
                            self._active_setting_val = min(self._active_setting_max, self._active_setting_val + self._active_setting_step)
                            self.display.show_pair(top_text, f" {self._active_setting_val} {self._active_setting_unit}   [{self._active_setting_min}-{self._active_setting_max}]", None)
                            dprint(f"Ertek novelve: {self._active_setting_val}")
                    elif not self.navigator.in_leaf_screen:
                        self.navigator.move_updown(-1)
                        self._render()

                elif key_name == "DOWN":
                    if self.navigator.in_leaf_screen and self._active_setting_key is not None:
                        top_text, _ = self.navigator.current_item()["screen"]
                        if self._active_setting_key == "BACKLIGHT_DUTY":
                            self._backlight_index = max(0, self._backlight_index - 1)
                            # Élő előnézet (live preview)
                            self.display.set_operating_backlight(BACKLIGHT_LEVELS[self._backlight_index])
                            self.display.show_pair(top_text, f"   9 / {self._backlight_index + 1}    [1-9]", None)
                            dprint(f"Fényerő index csökkentve: {self._backlight_index}")
                        else:
                            self._active_setting_val = max(self._active_setting_min, self._active_setting_val - self._active_setting_step)
                            self.display.show_pair(top_text, f" {self._active_setting_val} {self._active_setting_unit}   [{self._active_setting_min}-{self._active_setting_max}]", None)
                            dprint(f"Ertek csokkentve: {self._active_setting_val}")
                    elif not self.navigator.in_leaf_screen:
                        self.navigator.move_updown(1)
                        self._render()

            elif phase == "released":
                if key_name == "ENTER" and self._manual_hold_active:
                    self._manual_hold_pressed = False
                    self.relay.off()
                    self.led.set_green()
                    dprint("IO7 parancs vege (elengedve)")
                    self._render()
                elif key_name == "ESC":
                    if self._suppress_next_esc_release:
                        self._suppress_next_esc_release = False
                        dprint("ESC felengedve - meresi ciklus megszakitas utan, elnyelve")
                    else:
                        dprint(f"ESC felengedve, nyomvatartas: {duration:.2f} s")
                        if self.keypad.is_long_press(duration):
                            self.navigator.jump_to_root()
                            self._cleanup_active_modes()
                            self._render()
                        else:
                            self._handle_go_left()


def main():
    app = FanoeTesterApp()
    app.run()


if __name__ == "__main__":
    main()