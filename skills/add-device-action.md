---
description: 'FANOE tester device actions and state-machine workflow for adding measurement modes, confirmation-gated actions, and hardware-driven behaviors'
applyTo: '**/code.py'
---

# Add/Modify Device Action Skill
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊

*English:*
This skill captures the workflow for adding device-facing actions to the FANOE tester: instant info actions, confirmation-gated actions, continuous/modal modes, and the measurement-cycle state machine. It exists so future changes follow the same pattern instead of re-deriving behavior from scratch.

*Magyar:*
Ez a skill a FANOE teszterben használható eszközszintű akciók hozzáadásának munkafolyamatát rögzíti: azonnali info akciók, megerősítést igénylő akciók, folyamatos / modal módok és a mérési ciklus állapotgépe. Célja, hogy a jövőbeli változtatások ugyanazt a mintát kövessék, ne kelljen minden alkalommal újra kitalálni a működést.

> Ha a változtatás menüelemet, almenüt vagy navigációs struktúrát is érint, akkor a párhuzamosan használandó skill a [skills/add-menu.md](skills/add-menu.md). Az akciólogika és a menüstruktúra együttműködik, ezért mindkettőt érdemes együtt olvasni.

---
## NECESSARY DATA FOR THE AGENT

### Architecture recap (read `.copilot-instructions.md` Section 5 for the full rule)

- **`menu_data.py`** = pure data (`MENU_ROOT` list of dicts). Only add/edit menu entries there.
- **`code.py`** = OOP behavior layer. This is where action handlers live.
- **`tft_messages.py`** = ONLY for runtime event/error messages that are NOT tied to one specific menu leaf's fixed screen. A simple info leaf's live value does NOT belong here.

### Action and state-machine patterns

#### 1. Simple instant info action
Use this for leaves that show a live value immediately after entry.

- `menu_data.py`: add a `kind="leaf"` node with `activate_keys={"ENTER", "RIGHT"}`, `action="info_xxx"`, `auto_dispatch=True`, and a placeholder `screen` tuple.
- `code.py`: register the handler in the action map, e.g. `"info_xxx": self._action_info_xxx`.
- `code.py`: implement `_action_info_xxx(self)` so it computes the value, `dprint(...)`s it, renders the result with `self.display.show_pair(...)`, and returns `True`.

#### 2. Confirmation-gated action
Use this for destructive or safety-sensitive actions such as reset.

- `menu_data.py`: add the leaf with `action="xxx"` and `confirm_keys={"ENTER"}`.
- The first entry only shows the confirmation prompt from the leaf's `screen` tuple.
- The second press while already viewing the leaf triggers the real action.
- Do not set `auto_dispatch=True` for reset-like actions.

#### 3. Continuous/modal action
Use this for modes that stay active until the user exits, such as manual hold, ohm measurement, or a full measurement cycle.

- `code.py`: add a dedicated state flag such as `self._xxx_active` plus any timing/state variables.
- `_action_xxx_enter(self)`: enable the mode, start hardware, render initial live content, and return `True`.
- Add periodic update logic in the main loop using `time.monotonic()` and non-blocking checks. Never use `time.sleep()` in the main loop.
- Add a cleanup method, e.g. `_cleanup_xxx(self)`, and ensure it runs on every exit path (LEFT, short ESC, long ESC, mode end).
- If the active mode needs to intercept keys specially, branch before the generic key handling and `continue` to skip the rest of the iteration.

#### 4. Measurement-cycle state machine
The FANOE measurement cycle is the clearest reference for a complex action-mode.

From `instructions/fanoe_tester_logic.md`:

- GPIO roles:
  - IO7 = relay output (FANOE pull-in / release)
  - IO6 = digital input (NO-contact feedback)
  - IO14 = analog input (resistance measurement via ADC)
- States:
  - `IDLE`
  - `T_ELO`
  - `T_BENT`
  - `T_UTO`
  - `EVALUATE`
  - `RESULT`
  - `ABORTED`
- Core rules:
  - `cycle_duration = t_elo + t_bent + t_uto` and it must be computed dynamically from settings, never hard-coded.
  - IO6 and IO14 operate independently; neither blocks the other.
  - Errors like `ERROR_NO_PULLIN`, `ERROR_NO_DROPOUT`, or `"szakadt"` do not stop the cycle early.
  - `r_be` and `r_ki` are approximate timing estimates, not pass/fail judgments.
  - The implementation must be non-blocking and driven by `time.monotonic()`.
  - The class name should be `FanoeMeasurementCycle`.

#### 5. Status LED conventions
If a new continuous action uses the onboard WS2812 LED:

- Always use `board.IO48` explicitly; never rely on `board.NEOPIXEL` for this board.
- Only one continuous mode should own the LED at a time.
- Keep the color vocabulary consistent: green = idle/armed-safe, red = active output/danger, orange = measurement sampling.

---
### CODE GENERATION LOGIC & RULES

**1. Adding a simple info action:**
- `menu_data.py`: add a leaf with `action="info_xxx"`, `auto_dispatch=True`, and a placeholder `screen` tuple.
- `code.py`: register `"info_xxx": self._action_info_xxx` in the action map.
- `code.py`: implement `_action_info_xxx(self)` to render a custom live screen and return `True`.

**2. Adding a confirmation-gated action:**
- Add `confirm_keys={"ENTER"}` to the leaf.
- The first entry should only display the confirm prompt.
- The second press should trigger the action.

**3. Adding a continuous/modal action:**
- Add the mode state flag and any timing variables.
- Start hardware in `_action_xxx_enter(self)` and render live content.
- Add cleanup in `_cleanup_xxx(self)` and invoke it from every exit path.
- Use non-blocking timing with `time.monotonic()`.

**4. Adding a full measurement-like action:**
- Model it as a state machine, not as a single blocking function.
- Follow the `FanoeMeasurementCycle` rules from `instructions/fanoe_tester_logic.md`.
- Keep the cycle duration dynamic from settings.

**5. Known pitfalls — do not reintroduce these:**
- Do not let a continuous mode leave hardware running after the user exits.
- Do not let static placeholder text overwrite live content due to a missing return value contract.
- Do not use `time.sleep()` in the main loop.
- Do not invent a `VERSION` string; ask the user to manage it manually.

**6. Verification checklist before handing code back:**
- Run a Python syntax check (`py_compile`) after edits.
- Confirm every action key in `menu_data.py` has a matching handler in `code.py`.
- Confirm live actions return `True` so the generic static renderer does not overwrite them.

> **🤖 SYSTEM NOTE FOR THE AI AGENT:**
> This skill is focused on device action behavior and state machine design. It complements the menu-structure workflow in the sibling skill. Always still follow the global OOP, naming, logging, and CircuitPython rules from `.copilot-instructions.md` and the relevant instruction files.
