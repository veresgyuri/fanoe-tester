# AGENTS.md  

This is a high-level overview for AI agents, AI orchestrator.

> All rules and behavior are defined in `.copilot-instructions.md`. In case of any conflict, that file always takes precedence over this one.

## Goal
Generate working CircuitPython code for an ESP32-based diagnostic meter project.

## Hardware Stack
- `ESP32-S3-Super Mini` - Main board
- `Keypad` - 6 buttons matrix keyboard
- `Display` - 76*284 SPI TFT / ST7789

## Where to find things (Map)  
- **Filesystem & Mode control** `/boot.py`
- **Main application code:** `/code.py`  
- **Menu structure data:** `/menu_data.py`
- **TFT messages:** `/tft_messages.py`
- **CircuitPython, hardware-specific and operating logic instructions:** Found in `/instructions/`
- **Fonts & Character set** `/fonts/hu_127_ekezetes_20.pcf`
- **Configuration:** `/settings.toml`
- **AI Core Execution Rules:** `/.copilot-instructions.md`
- **On-Demand AI Skills:** Found in `/skills/`

*Note: For explicit write/read permissions for the files above, refer to `.copilot-instructions.md` Section 3.*  

*Note: Skill-based workflows are optional and on-demand. See `.copilot-instructions.md` section 8 for details and locations.*
