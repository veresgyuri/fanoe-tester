---
description: 'FANOE tester display/UI workflow for welcome screen, menu rendering, colors, text layout, and display redraws'
applyTo: '**/code.py, **/tft_messages.py'
---

# Display/UI Skill
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊

*English:*
This skill covers the workflow for changing the FANOE tester display behavior: welcome screen animation, menu rendering, text layout, colors, highlight states, and display redraw logic. It is focused on the visual layer and how the UI is presented on the ST7789 TFT.

*Magyar:*
Ez a skill a FANOE teszter kijelzőviselkedésének módosítási munkafolyamatát írja le: üdvözlőképernyő animáció, menümegjelenítés, szöveg elrendezés, színek, kiemelt állapotok és a kijelző újrarajzolási logikája. A fókusz a vizuális rétegen van, és hogy az UI hogyan jelenik meg az ST7789 TFT-n.

> Ha a módosítás akciólogikához, állapotgéphez vagy hardveres viselkedéshez kapcsolódik, akkor nézd meg a társik skillt is: [skills/add-device-action.md](skills/add-device-action.md).
> Ez a skill kizárólag a kijelző/UI réteget írja le; a tényleges műveletlogikát és eszközviselkedést a másik skill kezeli.

---
## NECESSARY DATA FOR THE AGENT

### Architecture recap (read `.copilot-instructions.md` Section 5 for the full rule)

- **`code.py`** = OOP behavior layer. The visual presentation is implemented here through the `Display` class and the app-level rendering flow, including the current built-in welcome banner under `Display.show_welcome()`.
- **`tft_messages.py`** = runtime messages for non-menu-specific feedback such as errors or status text. Do not overload this with one-off leaf-specific display content.
- **`menu_data.py`** = pure data only. Menu labels and static leaf screen placeholders live there; the visual rendering is still handled by `code.py`.

### Current display responsibilities in this project

- Welcome animation: initial banner implemented directly in `code.py` inside `Display.show_welcome()`, including border, background, text fade, and backlight ramp.
- Current menu view: two-line display with one highlighted line and a simple border/background theme.
- Status / transient UI: simple screen changes for action feedback, confirmation flow, or temporary state.
- Fonts and layout constants live in `code.py` and should stay centralized.

---
## CODE GENERATION LOGIC & RULES

**1. Changing the welcome screen:**
- Keep the welcome screen simple and startup-only.
- Avoid turning it into a full menu or measurement UI.
- Prefer a short, deterministic animation that finishes quickly and hands control back to the main app.
- Use the existing backlight and text fade style if you are extending it.

**2. Changing menu rendering:**
- Keep the two-line layout pattern unless a clear reason requires a different structure.
- Prefer changing the existing `Display.set_line()` / `Display.show_pair()` flow rather than creating a parallel display system.
- Use the existing highlighter and border palette behavior for consistency.

**3. Changing colors and theme:**
- Add or edit named constants near the top of `code.py` rather than hard-coding raw color values throughout the file.
- Keep a consistent palette for normal, highlighted, warning, and danger states.
- Avoid mixing too many unrelated color styles in one screen.

**4. Adding new text or labels:**
- If the text is a general runtime message, consider `tft_messages.py`.
- If the text is a fixed menu leaf screen, keep it in `menu_data.py` as a screen tuple.
- Avoid putting one-off UI strings directly into the render logic unless they are truly transient.

**5. Avoiding display regressions:**
- Do not create new display objects on every refresh.
- Reuse the existing `displayio.Group`, bitmaps, palettes, and labels where possible.
- Keep redraw logic simple and predictable; do not rebuild the whole UI tree unnecessarily.
- For CircuitPython, avoid any blocking pattern in the main loop. The startup animation may use short timed steps, but the normal app loop must remain non-blocking.

**6. Known pitfalls — do not reintroduce these:**
- Do not turn `menu_data.py` into a UI rendering file.
- Do not mix device action logic into the display layer.
- Do not hard-code display values inline in multiple places; use constants.
- Do not make the welcome screen too heavy or long-running.

**7. Verification checklist before handing code back:**
- Confirm the new UI still fits the 76x284 display dimensions.
- Confirm the text remains readable with the selected font and colors.
- Confirm the startup animation still exits cleanly and returns control to the menu UI.
- Confirm no new blocking sleep pattern was added to the main loop.

> **🤖 SYSTEM NOTE FOR THE AI AGENT:**
> This skill is focused on display and UI behavior only. Action behavior, measurement logic, and hardware response belong to [skills/add-device-action.md](skills/add-device-action.md). Always still follow the global CircuitPython, naming, logging, and stability rules from `.copilot-instructions.md` and the relevant instruction files.
