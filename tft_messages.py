# tft_messages.py
# A FANOE tesztműszer TFT kijelzőjének futásidejű üzenetei.
#
# Két típusú bejegyzés van itt:
#
# 1) Egysoros sablonok - a RESULT lapozható listájához (FEL/LE lapozás,
#    ugyanazzal a csúszóablakos/kiemelt megjelenítéssel, mint a menü
#    böngészés). Max. kb. 22 karakter a végleges, behelyettesített
#    szöveggel. A "{value}" placeholder-t code.py tölti ki .format()-tal.
#
# 2) Kétsoros (sor1, sor2) tuple-ök - önálló, megállító képernyők
#    (hibaüzenetek, megszakítás), NEM részei semmilyen lapozható listának.
#
# A menüfa statikus feliratai a menu_data.py-ban élnek, NEM itt - ez a
# fájl kizárólag a FanoeMeasurementCycle eseményeihez/eredményeihez
# tartozó, futásidejű szövegeket tartalmazza.

TFT_MESSAGES = {

    # --- RESULT lista elemei (egysoros sablonok) ---
    "result_t_be": " Kontakt BE: {value} ms",
    "result_t_ki": " Kontakt KI: {value} ms",
    "result_fanoe_ell": " Ellenállás: {value} Ω",
    "result_r_be": " Ω küszöb BE: {value} ms",
    "result_r_ki": " Ω küszöb KI: {value} ms",

    # --- Hiányzó / speciális értékek a fenti sablonokba behelyettesítve ---
    "value_na": " N/A",
    "value_szakadt": " szakadt",

    # --- Hibaüzenetek (kétsoros, önálló megállító képernyők) ---
    "err_premature_pullin": (" HIBA: váratlan", " behúzás előidő alatt"),
    "err_no_pullin": (" HIBA: FÁNOE nem", " húzott be időben"),
    "err_no_dropout": (" HIBA: FÁNOE nem", " ejtett el időben"),
    "err_fanoe_szakadt": (" HIBA: ellenállás", " szakadt (> 500 Ω)"),
    
    # --- Kétsoros önálló hibaüzenetek ---
    "err_already_closed": (" HIBA: a kontakt", " alapból zárva van!"),
    "err_premature": (" HIBA: váratlan", " elengedés T_BENT alatt"),

    # --- Egysoros hibajelzés a RESULT lapozható listájában (NEM állítja
    #     meg a ciklust, csak extra sor a lista elején, ha volt hiba) ---
    "result_err_premature_pullin": " HIBA: korai behúzás",
    "result_err_no_pullin": " HIBA: nem húzott be",
    "result_err_no_dropout": " HIBA: nem ejtett el",
    "result_err_already_closed": " HIBA: alapból zárva",
    "result_err_premature": " HIBA: korai elengedés",

    # --- Megszakítás (ESC aktív állapotban) ---
    "aborted_by_user": (" A mérés megszakítva", " visszalépés ▶"),

    # --- Ohm-mérő mód (folyamatosan frissülő, IO14) ---
    "ohm_meter_high": " > 500 Ω",
    "ohm_meter_open": " - - -",

    # --- Beállítás-mentés visszajelzése (settings.toml) ---
    "save_ok": (" Sikeres mentés", ""),
    "save_fail": (" Sikertelen mentés", ""),

    # --- Navigáció: (LEFT/rövid ESC no-op) ---
    "already_at_root": (" Már a főmenüben vagy", "      ⏎  ↑  ↓  ▶"),
}