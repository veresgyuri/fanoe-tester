---
description: 'CircuitPython programming language - rules for cPy code generation'
applyTo: '**/*.py'
---

# CircuitPython
### EXPLANATION FOR CARBON-BASED DEVELOPERS 😊
<img src="../images/cPy.png" alt="CircuitPython" width="300">  

*English:*
CircuitPython is a programming language specifically developed for beginners and educational purposes, which significantly simplifies the programming of low-cost microcontrollers. The platform's greatest advantage is its instant feedback, as code can be run immediately on the hardware after saving, without compilation, even via a web browser. The system boasts a vast library collection and extensive hardware support, while continuously evolving through the power of its open-source community. This tool bridges the gap between the popular Python language and physical computing, enabling users to create modern projects with easy-to-manage file storage and interactive interfaces.  

*Magyar:*
A CircuitPython egy kifejezetten kezdőknek és oktatási célokra fejlesztett programnyelv, amely jelentősen leegyszerűsíti az alacsony költségvetésű mikrokontrollerek programozását. A platform legnagyobb előnye az azonnali visszacsatolás, ugyanis a kód fordítás nélkül, mentés után rögtön futtatható a hardveren, akár böngészőn keresztül is. A rendszer hatalmas könyvtárkészlettel és széleskörű hardvertámogatással rendelkezik, miközben a nyílt forráskódú közösség erejére építve folyamatosan fejlődik. Ez az eszköz hidat képez a népszerű Python nyelv és a fizikai számítástechnika között, lehetővé téve a felhasználók számára, hogy könnyen kezelhető fájltárolással és interaktív felületeken keresztül alkossanak modern projekteket.

### Key Specifications - Főbb jellemzők
*English:*
- Core Concept and Target Audience: CircuitPython is a beginner-friendly, open-source programming language specifically designed for low-cost microcontroller boards, aiming to simplify coding education and rapid prototyping.
- Development Process: One of the language's biggest advantages is its simplicity. There's no need for compiling or installing special desktop software. When connected via USB, Wi-Fi, or Bluetooth, the board appears as a drive named CIRCUITPY. After saving the code.py file, the program runs instantly.
- Hardware and Software Support: Currently, it supports over 600 different microcontroller boards. Its ecosystem includes more than 500 Python libraries, making it easy to manage sensors and other accessories. On single-board computers (such as the Raspberry Pi), the Blinka library allows CircuitPython-specific code to run within a traditional Python environment.  
- 📂 Filesystem and Write Modes (boot.py)  
The project uses a special boot.py file to determine which device has write access to the internal storage: the computer (via USB) or the running code.py program.  
Switching between modes: The mode is selected based on the state of the IO39 pin during system startup (Hard Reset or Power-on).  
Developer mode (default)  
Status: IO39 pin is floating (NOT connected to GND)  
Operation: The CIRCUITPY drive appears on your computer. You can edit and copy files to the device, but the running code cannot save or modify data (e.g., settings, logs) on the storage.  
User mode (data saving enabled)  
Status: IO39 pin is connected to GND (via switch or jumper)  
Operation: The CIRCUITPY drive is disabled on the computer (it will not appear as a USB mass storage device). In this mode, the program gains full write access to the filesystem, allowing it to save settings and log data.  
Note: The USB-serial REPL remains active and accessible for debugging in both modes!
  
*Magyar:*
- Alapkoncepció és célcsoport: A CircuitPython egy kezdőbarát, nyílt forráskódú programozási nyelv, amelyet kifejezetten alacsony költségű mikrokontroller kártyákra terveztek a kódolás tanításának és a prototípusgyártásnak az egyszerűsítésére.
- Fejlesztési folyamat: A nyelv egyik legnagyobb előnye az egyszerűség. Nincs szükség fordításra (compiling) vagy speciális asztali szoftverek telepítésére. A kártyát USB-n, Wi-Fi-n vagy Bluetooth-on keresztül csatlakoztatva az egy CIRCUITPY nevű meghajtóként jelenik meg, ahol a code.py fájl mentése után a program azonnal lefut.
- Hardver- és szoftvertámogatás: Jelenleg több mint 600 különböző mikrokontroller kártyát támogat. Az ökoszisztéma része több mint 500 Python könyvtár, amelyek megkönnyítik a szenzorok és egyéb kiegészítők kezelését. Az egylapos számítógépeken (például Raspberry Pi) a Blinka könyvtár teszi lehetővé a CircuitPython-specifikus kódok futtatását a hagyományos Python környezetben.
- 📂 Fájlrendszer és írási módok (boot.py)  
A projekt egy speciális boot.py fájlt használ, amely meghatározza, hogy ki írhatja a belső memóriát (a számítógép vagy a futó code.py program)  
Váltás a módok között: a mód választása az IO39-es láb állapotától függ a rendszer indulásakor (Hard Reset vagy bekapcsolás)  
Fejlesztői mód (alapértelmezett):
Állapot: IO39 láb szabadon van (NINCS a GND-re kötve)  
Működés: A CIRCUITPY meghajtó megjelenik a számítógépen. Te tudsz rá másolni, de a kódod nem tud adatokat menteni (pl. beállításokat)  
Felhasználói mód (adatmentés engedélyezve):  
Állapot: IO39 láb a GND-re van zárva (kapcsolóval vagy jumperrel).  
Működés: A CIRCUITPY meghajtó eltűnik a számítógépről (nem látszik USB-meghajtóként). Cserébe a programod képes írni a fájlrendszert (mentés, logolás). A REPL (soros monitor) továbbra is elérhető marad!

Fontos szabályok:
    A módváltáshoz a kapcsoló állítása után mindig meg kell nyomni a RESET gombot.
    Ha módosítani akarod a kódot, állítsd vissza Fejlesztői módba (kapcsoló nyitva), és resetelj.
    A boot.py fájlt soha ne töröld le, mert az vezérli ezt a logikát!

> ⚠️ Az instrukció forrásai:
> - https://docs.circuitpython.org/en/latest/README.html
> - https://learn.adafruit.com/circuitpython-essentials
> - https://github.com/topics/circuit-python
> - https://github.com/adafruit/Adafruit_Learning_System_Guides/tree/main/CircuitPython_Essentials

---
## NECESSARY DATA FOR THE AGENT

**1. Pin Definitions & Hardware Access / Lábak és hardver elérés:**
- Always use the `board` module for pin definitions (e.g., `board.SCL`, `board.D5`, `board.GP0`). **Never** use raw integers for pin identification. Use `microcontroller.pin` only if dynamically mapping is strictly required.

**2. Interrupts & Polling (CRITICAL) / Megszakítások és Polling (KRITIKUS):**
- CircuitPython **deliberately lacks support for user-defined hardware interrupts (ISRs)**. Do not generate code using `IRQ`, `machine.Pin.irq`, or traditional hardware interrupts. Instead, utilize native background modules (like `keypad`, `rotaryio`, `countio`) or write non-blocking polling loops.

**3. Timing & Concurrency / Időzítés és Párhuzamosság:**
- Avoid `time.sleep()` in main or continuous loops as it blocks all execution. Use `time.monotonic()` for state-machine timing and non-blocking delays. For complex multitasking, prefer the native `asyncio` library.

**4. Core Libraries / Alapvető könyvtárak használata:**
- Rely on standard CircuitPython core modules: `digitalio` for GPIO, `analogio` for ADC/DAC, `pwmio` for PWM, and `busio` for I2C/SPI/UART. Do not use `bitbangio` unless explicitly requested. Always prefer official `adafruit_...` libraries for external sensors.

**5. Structure & Execution / Felépítés és Futás:**
- Ensure the code is structured to run directly as `code.py`. It must contain a continuous `while True:` loop (or an `asyncio.run()` equivalent) to keep the microcontroller running after initialization.

**6. Displays:**
- Always use the native displayio module for screen graphics and UI. Never try to use framebuffers or direct pixel manipulation unless strictly necessary.

**7. Filesystem Access & Write Permissions (boot.py Integration):**
- The project implements a boot-time hardware switch (IO39) to toggle filesystem write permissions.  
- Developer Mode (IO39 HIGH): The PC has write access; the microcontroller (code.py) is read-only.  
- User Mode (IO39 LOW): The USB drive is disabled; the microcontroller has full write access.  
- Code implementation: Always wrap file write operations (e.g., open(file, "w"), os.remove(), or storage.remount()) in try...except OSError blocks. This ensures the program doesn't crash when executed in Developer Mode.

> **🤖 SYSTEM NOTES FOR THE AI AGENT:**  
> When writing CircuitPython code, strictly adhere to the absence of hardware interrupts (no ISRs) and rely completely on the `board` module for pin routing. Prioritize Adafruit's standard library ecosystem over writing low-level bit-banging functions. Remember that memory management is crucial on microcontrollers; keep variable scope clean and logic efficient.  
Memory management: Avoid large memory allocations inside the while True: loop. Import the gc module and use gc.collect() periodically if handling large data buffers or strings.  

> CRITICAL - Filesystem management: This device uses a boot.py logic. Storage is only writable in User Mode (IO39 LOW). Must wrap all file writes in try/except OSError to handle read-only locks gracefully.  
Performance: Use time.monotonic() for non-blocking timing; avoid allocations in loops; use gc.collect() for memory management.
