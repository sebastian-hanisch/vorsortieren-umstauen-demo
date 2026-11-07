"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 5, 4          # Zahl der Stapel
HEIGHT_MIN, HEIGHT_MAX, DEFAULT_HEIGHT = 3, 5, 3          # Höchsthöhe eines Stapels
FREE_MIN, FREE_MAX, DEFAULT_FREE = 1, 8, 3                # freie Plätze der Bucht; Container = Stapel * Höchsthöhe - freie Plätze (mindestens 1)
SEED_MAX = 999999

LIVE_CAP = 150_000                                        # Zustandslimit der Breitensuche (live)
RELOC_CAP = 50_000                                        # Knotenlimit der Suche für das Relocation beim Abruf (live)
BAND_CAP = 600_000                                        # Zustandslimit der Breitensuche in der Vorberechnung
IDA_CAP = 300_000                                         # Knotenlimit der IDA*-Läufe in der Vorberechnung

# Zellen der vorberechneten Tabellen: (Stapel, Höchsthöhe, [freie Plätze]); Seeds ab 0.
SOLVE_CELLS = ((3, 3), (4, 3), (3, 4))                    # A: Breitensuche, freie Plätze 1 bis SOLVE_FREE_MAX
SOLVE_FREE_MAX = 6
SOLVE_BAYS = 60
IDA_CELLS = ((4, 4, (4, 5, 6)), (5, 3, (3, 4, 5)), (3, 5, (5, 6, 7)), (5, 4, (4, 5)), (6, 3, (3, 4)))     # B: IDA* für größere Zellen
IDA_BAYS = 40
VS_CELLS = ((3, 3, (3, 4, 5)), (4, 3, (3, 4, 5, 6)), (3, 4, (4, 5, 6)))      # C: Vorsortieren gegen Umlagern beim Abruf
VS_BAYS = 60

# Schwellen der Verdikte
LB_WEAK = 2.0                                             # Untergrenze „schwach“: Optimum / LB1 mindestens so groß
LB_OK = 1.5                                               # darunter „mäßig“, unter LB_OK „nahe“
VS_BIG = 1.5                                              # „Vorsortieren deutlich teurer“: Optimum des Pre-Marshalling / Optimum des Relocation mindestens so groß
VS_SMALL = 1.1                                            # darunter „kaum teurer“

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzurufenden)
COLOR_SORTED = "#2F6B65"       # sortiert (nicht blockierend)
COLOR_LINES = {3: "#2F6B65", 4: "#d9822b", 5: "#4c78a8"}   # je Höchsthöhe
COLOR_PMP, COLOR_RELOC, COLOR_LB = "#d9822b", "#2F6B65", "#7a8fa6"

# Sonderbuchten und Presets (Eigenschaften in tests/test_presets.py)
HAND_BAY = ((1, 4, 7), (5, 2, 6), (3, 8))                 # 3 Stapel, Höchsthöhe 3, ein freier Platz: 6 erreichbare Zustände, keiner sortiert
HAND_HEIGHT = 3
PRESETS = {
    "Genug Platz (4 Stapel, Höhe 3, 3 frei)": {"stacks": 4, "height": 3, "free": 3, "seed": 0},
    "Ein freier Platz (4 Stapel, Höhe 3)": {"stacks": 4, "height": 3, "free": 1, "seed": 0},
    "Zwei frei: lösbar (4 Stapel, Höhe 3)": {"stacks": 4, "height": 3, "free": 2, "seed": 2},
    "Zwei frei: unlösbar (4 Stapel, Höhe 3)": {"stacks": 4, "height": 3, "free": 2, "seed": 0},
    "Viel Platz (4 Stapel, Höhe 3, 6 frei)": {"stacks": 4, "height": 3, "free": 6, "seed": 1},
    "Vorsortieren lohnt nicht (3 Stapel, Höhe 4)": {"stacks": 3, "height": 4, "free": 4, "seed": 4},
}
PRESET_HELP = {
    "Genug Platz (4 Stapel, Höhe 3, 3 frei)": "9 Container, 3 freie Plätze (eine Stapelhöhe): lösbar mit 7 Hüben, die Untergrenze (Blocker) liegt bei 4, das Umlagern beim Abruf braucht 4.",
    "Ein freier Platz (4 Stapel, Höhe 3)": "11 Container, ein freier Platz: nur 24 Zustände erreichbar, keiner ist sortiert: unlösbar.",
    "Zwei frei: lösbar (4 Stapel, Höhe 3)": "10 Container, zwei freie Plätze: lösbar, aber mit 6 Hüben gegen eine Untergrenze von 2.",
    "Zwei frei: unlösbar (4 Stapel, Höhe 3)": "10 Container, zwei freie Plätze: 7 200 erreichbare Zustände, keiner sortiert: unlösbar, obwohl es zwei freie Plätze gibt.",
    "Viel Platz (4 Stapel, Höhe 3, 6 frei)": "6 Container, 6 freie Plätze: lösbar mit 3 Hüben, die Untergrenze liegt bei 2.",
    "Vorsortieren lohnt nicht (3 Stapel, Höhe 4)": "8 Container, 4 freie Plätze: Vorsortieren braucht 8 Hübe, das Umlagern beim Abruf nur 4.",
}
