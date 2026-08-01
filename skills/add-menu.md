---
description: 'FANOE tester menu structure - workflow for adding, removing, or modifying menu items in menu_data.py + code.py'
applyTo: '**/menu_data.py, **/code.py'
---

# Add/Modify Menu Skill
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊

*English:*
This skill encodes the exact workflow this project has used successfully across many menu changes (info screens, continuous modes like the Ohm-meter, confirmation-gated actions, removing whole submenus). It exists so future changes follow the same pattern instead of re-deriving it from scratch, and so known past bugs don't get reintroduced.

*Magyar:*
Ez a skill azt a munkafolyamatot rögzíti, amit a projektben eddig sikeresen alkalmaztunk a menü bővítésénél/módosításánál (info-képernyők, folyamatos módok mint az Ohm-mérő, megerősítést igénylő akciók, teljes almenük törlése). Azért létezik, hogy a jövőbeli változtatások ugyanazt a mintát kövessék, és a korábban már kijavított hibák ne térjenek vissza.

---
## NECESSARY DATA FOR THE AGENT

### Architecture recap (read `.copilot-instructions.md` Section 5 for the full rule)

- **`menu_data.py`** = pure data (`MENU_ROOT` list of dicts). NO function calls, NO hardware access, NO imports beyond nothing. Only add/edit dict entries here.
- **`code.py`** = OOP behavior layer. `MenuNavigator` walks the tree; `FanoeTesterApp` dispatches actions and owns all hardware (`Display`, `Keypad`, `RelayControl`, `StatusLed`, `OhmMeter`).
- **`tft_messages.py`** = ONLY for runtime event/error messages that are NOT tied to one specific menu leaf's fixed screen (e.g. `err_no_pullin`, `aborted_by_user`, `already_at_root`). A simple info leaf's live value (CPU freq, free RAM, flash usage, etc.) does **NOT** go through `tft_messages.py` — the action handler calls `self.display.show_pair(...)` directly with an f-string.

### Menu node schema (dict fields)

| Field | Required | Meaning |
|---|---|---|
| `label` | always | Text shown while browsing (leading space for consistent left margin). |
| `kind` | always | `"menu"` (has children, browsable) or `"leaf"` (a screen/action). |
| `activate_keys` | always | `set()` of key names (`"ENTER"`, `"RIGHT"`) that enter this item. See icon convention below. |
| `children` | `kind="menu"` only | List of child nodes. |
| `screen` | `kind="leaf"` only | `(line1, line2)` tuple shown when entered. For action-driven leaves this is a dead fallback (see below) — still fill it with a sensible placeholder in case `action`/`auto_dispatch` is ever removed for testing. |
| `action` | optional | String key resolved in `FanoeTesterApp._actions` dict. |
| `auto_dispatch` | optional | `True` → action fires immediately on first entry (no confirmation). Omit for pure static leaves. |
| `confirm_keys` | optional | `set()` of keys that CONFIRM (re-trigger) the action while already viewing the leaf. **Default is empty** — a leaf with `action` but no `confirm_keys` will NOT re-fire on a second press. Only set this for destructive/confirmable actions (e.g. `restart_device`). |

### Icon convention (keep this consistent — don't mix arbitrarily)

- **`⏎`** (ENTER icon) → `activate_keys={"ENTER"}` → leaf performs an immediate mode-switch/action, no real submenu.
- **`▶`** (triangle) → `activate_keys={"RIGHT"}` → leaf either has real children (`kind="menu"`) or enters a continuous/live mode.
- **Named exception**: `INFORMÁCIÓK` uses `⏎` but has real children, and its leaves accept `{"ENTER", "RIGHT"}` both — this was a deliberate, documented exception, not a mistake. Don't "fix" it back to strict icon matching.

### `_dispatch_action` return-value contract

Every `_action_*` handler must return:
- **`True`** — handler already rendered live/custom content itself (`self.display.show_pair(...)` or `self.display.set_line(...)` calls inside it). Caller will NOT call the generic renderer afterward.
- **`False` / `None`** — handler only changed internal state (e.g. armed a mode flag, started an LED). Caller WILL call the generic renderer afterward, which shows the leaf's static `screen` tuple.

Get this wrong and you get the exact bug seen once before: stale placeholder text flashing over live content.

---
### CODE GENERATION LOGIC & RULES

**1. Adding a simple "instant info" leaf (pattern: CPU freq, free RAM, flash usage):**
- `menu_data.py`: add a `kind="leaf"` dict with `activate_keys={"ENTER", "RIGHT"}`, `action="info_xxx"`, `auto_dispatch=True`, and a `screen` placeholder tuple.
- `code.py`: add `"info_xxx": self._action_info_xxx,` to `self._actions` in `__init__`.
- `code.py`: add a `_action_info_xxx(self)` method that computes the value, `dprint(...)`s it, calls `self.display.show_pair(label_line, f"...", None)`, and **returns `True`**.
- This is exactly 3 edits, 2 files. No `tft_messages.py` change needed.

**2. Adding a confirmation-gated action (pattern: `Szoftver reset`):**
- Same as above, but explicitly add `"confirm_keys": {"ENTER"}` to the leaf dict.
- The handler fires only when `confirm_action()` matches — i.e. the SECOND press while already viewing the leaf, not the first (which only shows the static confirm-prompt `screen`).
- Do not give this leaf `auto_dispatch: True` unless the action is safe to fire on mere entry — for reset-like actions, entry should only show the prompt.

**3. Adding a continuous/modal leaf (pattern: `FÁNOE KÉZI BE`, `ELLENÁLLÁS MÉRÉS`):**
- Needs: a dedicated hardware/state class if new peripherals are involved (see `RelayControl`, `StatusLed`, `OhmMeter` for the `start()`/`stop()` lifecycle pattern).
- `__init__`: add a `self._xxx_active` flag (and any timing/state vars).
- `_action_xxx_enter(self)`: sets the flag, starts peripherals, renders initial custom content, **returns `True`**.
- Add a periodic update block near the TOP of `run()`'s `while True:` loop (alongside the existing `_manual_hold_pressed`/`_ohm_meter_active` blocks), gated by `time.monotonic()` interval checks — never `time.sleep()`.
- Add a `_cleanup_xxx(self)` method (checks the flag, stops peripherals, resets flag) and register it inside `_cleanup_active_modes()` so it fires uniformly on any exit path (`LEFT`, short `ESC`, long `ESC`).
- If the mode needs to intercept a key specially while active (e.g. `ENTER` held for `FÁNOE KÉZI BE`), branch on the flag **before** the generic `ENTER`/`RIGHT` handling block in `run()`, and `continue` to skip the rest of that iteration.

**3b. Shared `StatusLed` (WS2812) conventions — read before adding a new continuous mode:**
- **Always `board.IO48` explicitly, never `board.NEOPIXEL`.** This board runs a Zero firmware build whose `NEOPIXEL` alias does not resolve to this hardware's actual LED pin — see `esp32s3supermini_instructions.md`. Any new code touching the LED must reuse the existing `STATUS_LED_PIN` constant, not re-derive it.
- **Only one continuous mode may own the LED at a time.** The menu design currently guarantees this structurally (only one leaf can be `in_leaf_screen` at once), so a new mode does not need its own mutex — but it DOES need to call `self.led.start()` on entry and `self.led.stop()` (which `deinit()`s the pixel) via its `_cleanup_xxx()`, exactly like the existing modes. Never leave a previous mode's color "hanging" — the `stop()`/re-`start()` cycle is what guarantees a clean color state for the next mode.
- **Color meaning is established and should stay consistent** across the whole menu, not be reinvented per feature: green = idle/armed-and-safe, red = active output/danger (e.g. relay energized), orange = a measurement is actively sampling. If a new mode needs a 4th state, pick a color that doesn't collide with this existing red/green/orange vocabulary, and document the new meaning here.
- **`StatusLed.start()` is idempotent** (checks `self._pixel is None` before creating) — safe to call every time a mode is entered, no need to guard against "already started" at the call site.

**4. Removing a menu item:**
- Delete the dict entry from `menu_data.py`.
- If it had an `"action"` key AND a real handler existed in `code.py`, remove the `_actions` dict entry and the `_action_*` method too. If it was still a dummy `screen`-only placeholder (no `action`), `menu_data.py` alone is enough — nothing to remove in `code.py`.
- No `tft_messages.py` change unless the removed leaf was the only user of some message key there (check before deleting keys).

**5. Known pitfalls — do not reintroduce these:**
- `UP`/`DOWN` handlers in `run()` MUST check `if not self.navigator.in_leaf_screen:` before calling `move_updown()`/`_render()` — otherwise pressing them while viewing any leaf briefly flashes the static `screen` placeholder over live content.
- `confirm_action()`'s default `confirm_keys` is an **empty set**, not `{"ENTER"}` — if you see an auto-dispatch leaf mysteriously re-triggering itself and desyncing the display (top line shows main menu while bottom line still updates), check whether `confirm_keys` was accidentally left defaulting to something non-empty for that item.
- Every continuous mode MUST register its cleanup in `_cleanup_active_modes()` — an orphaned mode left running in the background (LED stuck on, ADC still sampling) after the user backs out is a real bug class here, not a hypothetical.
- Never invent a `VERSION` string — always ask the user, they track it manually (`0vXX` scheme) and increment it themselves per change.

**6. Verification checklist before handing code back:**
- Run (or ask to run) a Python syntax check (`py_compile`) — several past edits introduced indentation breaks from careless insertions.
- Confirm every new `action` key referenced in `menu_data.py` has a matching entry in `code.py`'s `_actions` dict, and vice versa (no orphaned dict entries).
- Confirm label icon (`⏎`/`▶`) matches the `activate_keys` set, per the convention above, unless it's a deliberately documented exception.

> **🤖 SYSTEM NOTE FOR THE AI AGENT:**
> This skill overrides nothing in `.copilot-instructions.md` — it is a focused, on-demand workflow for menu changes specifically. Always still follow the global OOP/naming/logging rules from `.copilot-instructions.md` Section 5 on top of everything above. When in doubt about a NEW pattern not covered here (e.g. a menu leaf needing a genuinely new interaction shape), stop and ask the user rather than guessing — this project's history shows that guessing on interaction design (e.g. confirm-vs-auto-dispatch semantics) reliably produces bugs that are caught only through live hardware testing.