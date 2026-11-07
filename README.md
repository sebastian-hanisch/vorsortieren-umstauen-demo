# Vorsortieren: sortieren statt abrufen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-vorsortieren-umstauen-demo.streamlit.app/)** -->

Elftes Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Bisher wurde **beim Abruf** umgelagert (Stück 1 bis 10). Beim **Pre-Marshalling** wird die Bucht **vorher sortiert**: Kein Container darf über einem früher abzurufenden liegen, dann kostet der Abruf keinen Hub mehr. Erlaubt ist **jeder** Hub eines obersten Containers auf einen anderen Stapel mit Platz. Die Demo **rechnet das live** auf kleinen Buchten und misst vorberechnet, **ab wie vielen freien Plätzen** eine Bucht überhaupt sortierbar ist, **wie schwach die Untergrenze** (Blocker zählen) hier ist und **ob Vorsortieren Hübe spart** gegenüber dem Umlagern beim Abruf.

## Warum dieses Problem

Vorsortieren klingt nach einer sicheren Sache: einmal sortieren, danach nie wieder umlagern. Zwei Messungen bremsen das. **Erstens** geht es nicht immer: Mit **weniger freien Plätzen als eine Stapelhöhe** ist ein großer Teil der Buchten **unlösbar** (3 × 3 mit 2 freien Plätzen: 23 von 60 Buchten lösbar, mit 1 freien Platz 3 von 60); ab einer Stapelhöhe freier Plätze waren in allen gemessenen Zellen alle Buchten lösbar. **Zweitens** ist es **teurer** als Umlagern beim Abruf: Das Optimum des Pre-Marshalling ist 1,2- bis 1,7-fach so groß wie das des Relocation und nur in 0 bis 2 von 60 Buchten kleiner. Vorsortieren spart keine Hübe, es **verschiebt** sie in die ruhige Zeit. Und die einfache Untergrenze (Zahl der Blocker) ist hier **schwach**: Bei wenigen freien Plätzen liegt das Optimum beim Zwei- bis Zweieinhalbfachen.

## Modell

**Eigene Umsetzung** an Zufallsbuchten; Pre-Marshalling nach Bortfeldt und Forster, Tierney u. a. (Stand der Technik aus dem Gedächtnis, **nicht gelesen**); Branch and Price für das Pre-Marshalling bei van Brink und van der Zwaan wurde in Stück 8 gelesen, hier nur als Verweis.

- **Bucht:** *S* Stapel der Höchsthöhe *H*, *N* = *S* · *H* − *F* Container mit den Nummern 1 bis *N* (kleiner = früher abzurufen), jeder auf einen zufälligen Stapel mit Platz; *F* freie Plätze.
- **Ziel:** jeder Stapel **sortiert**: von unten nach oben fallende Nummern, also kein **Blocker** (Container über einem früher abzurufenden).
- **Hub:** der oberste Container eines Stapels auf einen anderen Stapel mit freiem Platz; Kosten 1.
- **Untergrenze:** Zahl der Blocker (jeder muss mindestens einmal bewegt werden).
- **Exakt:** Breitensuche über kanonische Zustände (Stapel sortiert). Das erste sortierte Ziel ist optimal; erschöpft die Suche den Zustandsraum ohne Ziel, ist die Bucht **bewiesen unlösbar**. Größere Zellen: IDA\* mit der Untergrenze und Zustandsmerken (findet das Optimum, wenn es lösbar ist).
- **Vergleich:** Optimum des Relocation beim Abruf derselben Bucht (restricted, Stück 5 bis 9).

## Methodik

- **Live:** Breitensuche mit Zustandslimit 150 000 (bei Limit „nicht entschieden“, kein Wert), Untergrenze und das Relocation-Optimum (Knotenlimit 50 000; ohne Platz für einen Blocker bricht diese Suche am Limit ab: „kein Ergebnis“).
- **Vorberechnet** (`vso_bands.json`, erzeugt von `generate_precomputed.py`, einige Minuten in mehreren Prozessen): Lösbarkeit in drei Zellen mit je 1 bis 6 freien Plätzen (60 Buchten, Breitensuche, Zustandslimit 600 000, **nie am Limit**), größere Zellen mit IDA\* (40 Buchten, Knotenlimit 300 000), Vorsortieren gegen Umlagern in drei Zellen (60 Buchten).
- Alle Kennzahlen sind **Zählungen** an festen Seeds (Zustände, Knoten, Hübe); es gibt keine Zeitmessung.
- **Abschnitte der App:** Ergebnis (live); eine Bucht, die sich nicht sortieren lässt (Hand-Bucht mit allen sechs erreichbaren Zuständen); ab wie vielen freien Plätzen es geht; wie schwach die Untergrenze ist; Vorsortieren gegen Umlagern; Grenzen; mathematische Formulierung.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Zufallsbuchten, nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_vorsortieren_umstauen.py`.

**A: Lösbarkeit und Hubzahl nach freien Plätzen** (60 Buchten je Zeile, Breitensuche; Optimum und Untergrenze Mittel über die gelösten Buchten)

| Zelle, freie Plätze | gelöst | bewiesen unlösbar | schon sortiert | Optimum | Untergrenze | Optimum = Untergrenze | größte Zustandszahl |
|---|---|---|---|---|---|---|---|
| 3 × 3, 1 frei | 3 | 57 | 1 | 0,67 | 0,67 | 3 | 6 |
| 3 × 3, 2 frei | 23 | 37 | 7 | 3,35 | 1,35 | 11 | 144 |
| 3 × 3, 3 frei | **60** | 0 | 8 | 3,38 | 1,65 | 18 | 399 |
| 3 × 3, 4 frei | 60 | 0 | 11 | 1,90 | 1,25 | 35 | 80 |
| 3 × 3, 5 frei | 60 | 0 | 25 | 0,95 | 0,77 | 49 | 18 |
| 3 × 3, 6 frei | 60 | 0 | 38 | 0,43 | 0,42 | 59 | 3 |
| 4 × 3, 1 frei | 1 | 59 | 1 | 0 | 0 | 1 | 24 |
| 4 × 3, 2 frei | 19 | 41 | 0 | 5,63 | 2,26 | 4 | 7 200 |
| 4 × 3, 3 frei | **60** | 0 | 2 | 5,03 | 2,78 | 10 | 60 234 |
| 4 × 3, 4 frei | 60 | 0 | 3 | 3,72 | 2,37 | 11 | 5 897 |
| 4 × 3, 5 frei | 60 | 0 | 7 | 2,27 | 1,62 | 30 | 810 |
| 4 × 3, 6 frei | 60 | 0 | 16 | 1,40 | 1,10 | 44 | 136 |
| 3 × 4, 1 frei | 0 | 60 | 0 | – | – | – | 6 |
| 3 × 4, 2 frei | 1 | 59 | 0 | 10 | 2 | 0 | 144 |
| 3 × 4, 3 frei | 16 | 44 | 0 | 8 | 2,50 | 2 | 7 200 |
| 3 × 4, 4 frei | **60** | 0 | 0 | 7,12 | 3,02 | 4 | 16 334 |
| 3 × 4, 5 frei | 60 | 0 | 6 | 4,72 | 2,23 | 14 | 3 476 |
| 3 × 4, 6 frei | 60 | 0 | 8 | 3,22 | 1,77 | 16 | 634 |

Die Lösbarkeit **springt**: unterhalb von *F* = *H* (3 × 3: 3, 4 × 3: 3, 3 × 4: 4) ist ein großer Teil der Buchten unlösbar, ab *F* = *H* sind **alle 180 Buchten** der drei Zellen lösbar. Das ist eine **Messung an drei Zellen, kein Satz**. Die Untergrenze trifft das Optimum bei *F* = *H* nur in 10 von 60 (4 × 3) und 4 von 60 (3 × 4); das Verhältnis Optimum / Untergrenze sinkt mit mehr freien Plätzen (4 × 3: 2,5 bei 2, 1,8 bei 3, 1,6 bei 4, 1,3 bei 6).

**B: Größere Zellen mit IDA\*** (40 Buchten, Knotenlimit 300 000; „gelöst“ = in der Knotengrenze gelöst, die übrigen sind nicht bewiesen unlösbar, nur am Limit)

| Zelle, freie Plätze | gelöst | Optimum | Untergrenze | Optimum = Untergrenze | Knoten Median / Maximum |
|---|---|---|---|---|---|
| 4 × 4, 4 frei | 36 | 8,64 | 4,53 | 0 | 15 255 / 291 277 |
| 4 × 4, 5 frei | 38 | 6,61 | 3,89 | 2 | 2 468 / 55 697 |
| 4 × 4, 6 frei | 40 | 5,83 | 3,40 | 1 | 1 457 / 52 248 |
| 5 × 3, 3 frei | 40 | 6,10 | 3,62 | 1 | 2 488 / 86 621 |
| 5 × 3, 4 frei | 40 | 4,65 | 3,27 | 9 | 473 / 35 649 |
| 5 × 3, 5 frei | 40 | 3,67 | 2,60 | 11 | 238 / 4 548 |
| 3 × 5, 5 frei | 38 | 10,29 | 4,24 | 1 | 14 087 / 171 178 |
| 3 × 5, 6 frei | 40 | 8,75 | 3,80 | 1 | 7 290 / 129 403 |
| 3 × 5, 7 frei | 40 | 6,55 | 3,12 | 4 | 1 562 / 31 295 |
| 5 × 4, 4 frei | 14 | 9,93 | 5,93 | 0 | 59 215 / 291 275 |
| 5 × 4, 5 frei | 21 | 8,33 | 5,38 | 0 | 22 542 / 195 578 |
| 6 × 3, 3 frei | 34 | 7,59 | 4,59 | 0 | 19 213 / 270 790 |
| 6 × 3, 4 frei | 40 | 6,28 | 4,05 | 1 | 7 358 / 149 610 |

**C: Vorsortieren gegen Umlagern beim Abruf** (dieselben Buchten, die beide Verfahren lösen; Relocation restricted; 60 Buchten je Zeile)

| Zelle, freie Plätze | Pre-Marshalling | Umlagern beim Abruf | Untergrenze | Verhältnis | Vorsortieren billiger / gleich / teurer |
|---|---|---|---|---|---|
| 3 × 3, 3 frei | 3,38 | 2,05 | 1,65 | 1,7 | 0 / 22 / 38 |
| 3 × 3, 4 frei | 1,90 | 1,45 | 1,25 | 1,3 | 0 / 42 / 18 |
| 3 × 3, 5 frei | 0,95 | 0,82 | 0,77 | 1,2 | 0 / 52 / 8 |
| 4 × 3, 3 frei | 5,03 | 3,25 | 2,78 | 1,5 | 1 / 10 / 49 |
| 4 × 3, 4 frei | 3,72 | 2,73 | 2,37 | 1,4 | 1 / 19 / 40 |
| 4 × 3, 5 frei | 2,27 | 1,82 | 1,62 | 1,2 | 0 / 41 / 19 |
| 4 × 3, 6 frei | 1,40 | 1,17 | 1,10 | 1,2 | 1 / 46 / 13 |
| 3 × 4, 4 frei | 7,12 | 4,27 | 3,02 | 1,7 | 2 / 7 / 51 |
| 3 × 4, 5 frei | 4,72 | 2,78 | 2,23 | 1,7 | 0 / 16 / 44 |
| 3 × 4, 6 frei | 3,22 | 2,20 | 1,77 | 1,5 | 0 / 22 / 38 |

| Frage | Befund |
|---|---|
| **Geht das Sortieren immer?** | Nein. Mit weniger freien Plätzen als eine Stapelhöhe sind die meisten Buchten unlösbar (bewiesen: der erreichbare Zustandsraum enthält keine sortierte Bucht), ab einer Stapelhöhe waren alle 180 Buchten der drei durchgerechneten Zellen lösbar. |
| **Das kleinste Beispiel?** | Die Hand-Bucht (1, 4, 7), (5, 2, 6), (3, 8) mit Höchsthöhe 3 und **einem** freien Platz: nur sechs erreichbare Zustände, in allen sechs bleiben vier Blocker. Die Untergrenze hätte „4“ gesagt, ohne zu merken, dass es nicht geht. |
| **Wie schwach ist die Untergrenze?** | Bei wenigen freien Plätzen das Zwei- bis Zweieinhalbfache vom Optimum (4 × 3 mit 2 freien Plätzen: 5,63 gegen 2,26), bei vielen freien Plätzen nahe (4 × 3 mit 6 frei: 1,40 gegen 1,10). Bei *F* = *H* trifft sie nur in 10 von 60 (4 × 3) und 4 von 60 (3 × 4) Buchten. |
| **Spart Vorsortieren Hübe?** | Nein: im Mittel 1,2- bis 1,7-fach so viele wie das Umlagern beim Abruf; billiger nur in 0 bis 2 von 60 Buchten. Es verschiebt die Hübe in die ruhige Zeit, was die Hubzahl nicht abbildet. |
| **Und größere Zellen?** | Bis 6 × 3 und 5 × 4 mit IDA\* gerechnet: Optimum / Untergrenze liegt zwischen 1,4 (5 × 3 mit 4 und 5 frei) und 2,4 (3 × 5 mit 5 frei); die Zellen mit der engsten Platzlage (5 × 4, 6 × 3 mit 3 frei) lösen nur 14 bis 34 von 40 in der Knotengrenze. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Genug Platz“ (4 × 3, 3 frei, Bucht 0: Optimum 7, Untergrenze 4, Umlagern 4), „Ein freier Platz“ (4 × 3, Bucht 0: unlösbar, 24 Zustände), „Zwei frei: lösbar“ (4 × 3, Bucht 2: 6 Hübe gegen Untergrenze 2), „Zwei frei: unlösbar“ (4 × 3, Bucht 0: 7 200 Zustände, keiner sortiert), „Viel Platz“ (4 × 3, 6 frei, Bucht 1: 3 Hübe), „Vorsortieren lohnt nicht“ (3 × 4, 4 frei, Bucht 4: 8 gegen 4).

**Korrektur gegenüber dem Plan:** Alle Zahlen stimmen mit der Vormessung überein (Zählungen, keine Zeiten).

## Ehrliche Grenzen

- **Messung, kein Satz.** „Ab einer Stapelhöhe freier Plätze lösbar“ ist an drei Zellen gemessen (je 60 Buchten); größere Zellen nur mit IDA\*, ungelöste Buchten dort sind am Limit, nicht bewiesen unlösbar.
- **Zufallsbuchten** (jeder Container auf einen zufälligen Stapel mit Platz, ungleich hohe Stapel); echte Buchten sind oft teilweise sortiert.
- **Eine Prioritätsordnung ohne Gruppen:** alle Nummern verschieden; mit Gruppen gleicher Priorität (üblich in der Literatur) ist das Sortieren leichter.
- **Nur die Hubzahl:** Kranzeit, Fahrwege und Zeitfenster zählen nicht (Brücke zur Linie „Zielfunktion“).
- **Relocation restricted** im Vergleich; im unrestricted Relocation wäre das Umlagern nicht teurer.
- **Stärkere Untergrenzen** (Bortfeldt und Forster, Tierney u. a.) nicht gebaut.

## Verifikation

- **Kern:** Blocker, Untergrenze und Sortiertheit von Hand, die Hübe einer Hand-Bucht (nur zwei Nachbarn), Hand-Bucht unlösbar mit sechs Zuständen, Bucht ohne freien Platz (ein Zustand), Handwerte für Optimum und Zustandszahl (4 × 3, Bucht 0: 7 Hübe, 5 364 Zustände), Zustandslimit, IDA\* gegen Breitensuche, Relocation von Hand.
- **Orakel:** Optimum **und Lösbarkeit** gegen eine **eigene Breitensuche über beschriftete Zustände** (ohne Kanonisierung) in über 300 Buchten aus zehn Zellen; das Relocation gegen eine **eigene vollständige Rekursion** in 150 Buchten; IDA\* gegen die Breitensuche; Untergrenze gegen eine zweite Zählung; die Schwelle in klein (3 × 3 mit 3 freien Plätzen: in jeder Bucht lösbar, mit 1 in höchstens 4 von 40).
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (gespeicherte Bänder, Sprung der Lösbarkeit bei *F* = *H* in allen drei Zellen); fünf Zellen der Breitensuche, eine IDA\*-Zelle und eine Vergleichszelle werden frisch nachgerechnet (Zählungen, keine Zeiten).
- **Verdikte:** reine Funktionen, jede Schwelle (Verhältnis 1,5 und 2,0 für die Untergrenze, 1,1 und 1,5 für den Vergleich) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`); dabei fiel eine doppelte Formulierung auf („mit 1 … , mit 1 …“), die behoben wurde.
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset, Tabellenzeilen, Hand-Bucht), Layout, Footer, Laufzeit-Importe, Abbildungen (Farben, gesperrte Achsen).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `vso_bands.json` (Lösbarkeit, IDA\*, Vergleich) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt): streamlit, plotly |
| `vso_algorithm.py` | Pre-Marshalling (Untergrenze, Breitensuche, IDA\*) und Relocation beim Abruf |
| `vso_bands.json` | vorberechnete Kennzahlen der festen Buchten je Zelle |
| `vso_constants.py` | Regler-Grenzen, Limits, Zellen, Schwellen, Farben, Presets |
| `vso_evaluation.py` | Analyse einer Bucht, Stichproben, Verdikte (reine Funktionen) |
| `vso_layout.py` | Fester Kopf (Stylesheet) |
| `vso_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `vso_scenario.py` | Zufallsbuchten mit freien Plätzen |
| `vso_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Stärkere Untergrenzen** und gelernte Verfahren für das Pre-Marshalling (Stück 14).
- **Gruppen gleicher Priorität** und teilweise sortierte Buchten als Familie.
- **Kranzeit statt Hubzahl.**
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

99 Tests, rund eine Minute.

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
