---
description: 'FANOE tester menu structure - workflow for adding, removing, or modifying menu items in menu_data.py + code.py'
applyTo: '**/menu_data.py, **/code.py'
---

# Add/Modify Menu Skill
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊

*English:*
This skill covers the workflow for adding, removing, or changing menu structure in the FANOE tester. It is focused on the menu tree itself: nodes, labels, submenus, activation keys, and the relationship between the menu data and the main application.

*Magyar:*
Ez a skill a FANOE teszterben használt menüstruktúra módosítási munkafolyamatot írja le. A fókusz a menüfa szerkezetén van: csomópontok, címkék, almenük, aktiválási billentyűk, valamint a menüadatok és a fő alkalmazás közötti kapcsolat.

> Ha a módosítás akcióhoz, megerősítést igénylő művelethez, élő mérési módhoz vagy állapotgéphez kapcsolódik, akkor mindenképp nézd meg a társik skillt is: [skills/add-device-action.md](skills/add-device-action.md).
> Ez a skill csak a menüstruktúrát és navigációt írja le; az akciólogikát és hardveres viselkedést a másik skill kezeli.

---
## NECESSARY DATA FOR THE AGENT

### Architecture recap (read `.copilot-instructions.md` Section 5 for the full rule)

- **`menu_data.py`** = pure data (`MENU_ROOT` list of dicts). NO function calls, NO hardware access, NO imports beyond nothing. Only add/edit dict entries here.
- **`code.py`** = OOP behavior layer. The main application uses the menu tree for navigation and rendering. Action behavior is covered by the sibling skill [skills/add-device-action.md](skills/add-device-action.md).
- **`tft_messages.py`** = ONLY for runtime event/error messages that are NOT tied to one specific menu leaf's fixed screen. A simple info leaf's live value does NOT belong here.

### Menu node schema (dict fields)

| Field | Required | Meaning |
|---|---|---|
| `label` | always | Text shown while browsing (leading space for consistent left margin). |
| `kind` | always | `"menu"` (has children, browsable) or `"leaf"` (a screen/action). |
| `activate_keys` | always | `set()` of key names (`"ENTER"`, `"RIGHT"`) that enter this item. See icon convention below. |
| `children` | `kind="menu"` only | List of child nodes. |
| `screen` | `kind="leaf"` only | `(line1, line2)` tuple shown when entered. For action-driven leaves this is a fallback placeholder. |
| `action` | optional | String key resolved by the action layer in `code.py`. |
| `auto_dispatch` | optional | `True` → the action is fired immediately on first entry. Omit for static leaves. |
| `confirm_keys` | optional | `set()` of keys that confirm an action while already viewing the leaf. |

### Icon convention (keep this consistent — don't mix arbitrarily)

- **`⏎`** (ENTER icon) → `activate_keys={"ENTER"}` → leaf performs an immediate mode-switch/action, no real submenu.
- **`▶`** (triangle) → `activate_keys={"RIGHT"}` → leaf either has real children (`kind="menu"`) or enters a continuous/live mode.
- **Named exception**: `INFORMÁCIÓK` uses `⏎` but has real children, and its leaves accept `{"ENTER", "RIGHT"}` both — this was a deliberate, documented exception, not a mistake. Don't "fix" it back to strict icon matching.

---
### CODE GENERATION LOGIC & RULES

**1. Adding a simple menu item:**
- `menu_data.py`: add or edit a dict entry in the `MENU_ROOT` tree.
- Keep the node structure plain and data-only.
- If the item needs behavior, add the action metadata (such as `action` or `confirm_keys`) and let the action skill cover the handler implementation.

**2. Adding a submenu:**
- Create a new `kind="menu"` node with a `children` list.
- The parent item should use `activate_keys={"RIGHT"}` or `{"ENTER"}` depending on the desired navigation style.

**3. Removing a menu item:**
- Delete the corresponding dict entry from `menu_data.py`.
- If the removed item had an action, remove the matching action wiring in `code.py` as well.

**4. Known pitfalls — do not reintroduce these:**
- Keep `menu_data.py` pure data; do not insert code or hardware access there.
- Keep icon conventions consistent with the `activate_keys` set.
- Do not mix menu-structure edits with device-action implementation details — use the sibling action skill for those changes.

**5. Verification checklist before handing code back:**
- Confirm the menu structure is still valid JSON-like Python data.
- Confirm any new `action` references are handled by the action skill workflow rather than being implemented inline here.

> **🤖 SYSTEM NOTE FOR THE AI AGENT:**
> This skill is focused on menu structure and navigation only. Action behavior, state-machine design, and device-facing logic belong to the sibling skill [skills/add-device-action.md](skills/add-device-action.md). Always still follow the global OOP, naming, logging, and CircuitPython rules from `.copilot-instructions.md` and the relevant instruction files.