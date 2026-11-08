"""Vorsortieren: Pre-Marshalling und freie Plätze - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 11 der Reihe „Umstauen: Untergrenze und Suche“. Bisher wurde beim Abruf umgelagert; hier wird die Bucht vorher sortiert (Pre-Marshalling). Die Demo rechnet das live auf kleinen
Buchten und misst vorberechnet, ab wie vielen freien Plätzen eine Bucht überhaupt sortierbar ist, wie schwach die Untergrenze (Blocker zählen) hier ist und ob Vorsortieren gegenüber
dem Umlagern beim Abruf Hübe spart.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import vso_algorithm as A
import vso_constants as C
from vso_evaluation import (
    Settings,
    analyse,
    dec,
    key,
    load_bands,
    num,
    ratio_text,
    result_rows,
    verdict_bay,
    verdict_free,
    verdict_lb,
    verdict_vs,
)
from vso_layout import dunkles_design, kopf_css
from vso_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from vso_visualization import build_bay, build_ratio, build_solvable, build_vs

st.set_page_config(page_title="Vorsortieren – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


@st.cache_data(show_spinner=False)
def _hand_states():
    return sorted(A.reachable_states(C.HAND_BAY, C.HAND_HEIGHT))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in vso_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗂️ Vorsortieren: sortieren statt abrufen")
st.markdown(
    """
Bisher wurde **beim Abruf** umgelagert (Stück 1 bis 10). Beim **Pre-Marshalling** wird die Bucht **vorher sortiert**: kein Container darf über einem früher abzurufenden liegen, dann kostet der Abruf keinen Hub mehr. Erlaubt ist **jeder** Hub eines obersten Containers auf einen anderen Stapel mit Platz. Die Demo **rechnet das live** auf kleinen Buchten und misst vorberechnet, **ab wie vielen freien Plätzen** eine Bucht überhaupt sortierbar ist, **wie schwach die Untergrenze** (Blocker zählen) hier ist und **ob Vorsortieren Hübe spart** gegenüber dem Umlagern beim Abruf.

Wer zuerst ohne Fachbegriffe verstehen will, worum es geht, öffnet „💬 In einfachen Worten“. Weiter unten: die Abschnitte **🔬 Experiment** (die Bucht von Hand, Lösbarkeit nach freien Plätzen, die Untergrenze, Vorsortieren gegen Umlagern), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das elfte Stück der Reihe „Umstauen: Untergrenze und Suche“.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/vorsortieren-umstauen-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Auf einem Lagerplatz stehen Container in Stapeln und werden in bekannter Reihenfolge abgeholt. Liegt der gesuchte nicht oben, müssen die darüber umgestapelt werden. Die Demo fragt, ob es sich lohnt, die Stapel schon vorher zu ordnen, damit beim Abholen nichts mehr im Weg liegt. Sie rechnet kleine Plätze mit einem Suchverfahren vollständig durch und zeigt zwei Haken. Erstens lässt sich bei zu wenig freien Plätzen ein großer Teil der Plätze gar nicht ordnen. Zweitens braucht das Ordnen im Mittel mehr Handgriffe als das Umstapeln erst beim Abholen. Es verlegt die Arbeit nur in die Zeit davor. Die Plätze sind zufällig gefüllt, und gezählt werden nur Handgriffe, keine Zeit.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/vorsortieren-umstauen-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So wird gemessen", expanded=True):
    st.markdown(
        """
1. **Bucht:** *Stapel* Stapel der Höchsthöhe *H*, *N* = Stapel · *H* − *F* Container mit den Abrufnummern 1 bis *N* zufällig verteilt; *F* ist die Zahl der **freien Plätze** (feste Seeds).
2. **Ziel:** jeder Stapel **sortiert** (von unten nach oben fallende Nummern), das heißt kein **Blocker** (Container über einem früher abzurufenden).
3. **Untergrenze:** Zahl der Blocker; jeder muss mindestens einmal bewegt werden.
4. **Exakt:** Breitensuche über alle erreichbaren Zustände (Stapel sortiert, gleiche Zustände zusammengefasst). Das erste sortierte Ziel ist optimal; erschöpft die Suche den Zustandsraum ohne Ziel, ist die Bucht **bewiesen unlösbar**. Größere Zellen: IDA\\* mit der Untergrenze (findet das Optimum nur, wenn es lösbar ist).
5. **Vergleich:** dasselbe Optimum beim **Umlagern beim Abruf** (Stück 9: nur Container über dem nächsten Abruf werden bewegt).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    height = st.slider("Höchsthöhe", *bounds("height_slider"), key="height_slider", help="So viele Container passen auf einen Stapel.")
    free = st.slider("Freie Plätze", *bounds("free_slider"), key="free_slider", help="Container = Stapel · Höchsthöhe − freie Plätze (mindestens 1).")
    seed = st.number_input("Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Nummer bestimmt, wie die Abrufnummern auf die Stapel verteilt sind.")
    st.button("🎲 Neue Bucht würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"stacks_slider": int(stacks), "height_slider": int(height), "free_slider": int(free), "seed_input": int(seed)})

settings = Settings(int(stacks), int(height), int(free), int(seed))
with st.spinner(f"Durchsuche den Zustandsraum (höchstens {num(C.LIVE_CAP)} Zustände) und rechne das Umlagern beim Abruf …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
s = a.solved
m1, m2, m3, m4 = st.columns(4)
m1.metric("Container", a.containers, delta=f"{a.free} frei bei Höchsthöhe {a.height}", delta_color="off", help="Stapel · Höchsthöhe − freie Plätze, mindestens 1.")
m2.metric("Pre-Marshalling", str(s.optimum) if s.status == "optimal" else "unlösbar" if s.status == "unloesbar" else "offen", delta=f"{num(s.states)} Zustände", delta_color="off",
          help="Kleinste Hubzahl bis zur sortierten Bucht.")
m3.metric("Untergrenze", a.lb1, delta="Blocker", delta_color="off", help="Zahl der blockierenden Container.")
m4.metric("Umlagern beim Abruf", "kein Ergebnis" if a.reloc.optimum is None else a.reloc.optimum, delta="Stück 9", delta_color="off", help="Optimum des Relocation derselben Bucht (restricted).")
st.plotly_chart(build_bay(a.bay, a.height), width="stretch", key="chart_bay")
st.caption("Rot: Blocker (liegen über einem früher abzurufenden), grau-blau: alle übrigen. Die gestrichelte Linie ist die Höchsthöhe.")
table = ["| Verfahren | Wert | Aufwand |", "|---|---|---|"]
for r in result_rows(a):
    table.append(f"| {r['name']} | {r['value']} | {r['effort']} |")
st.markdown("\n".join(table))

st.markdown("## ❓ Kernfrage: Ist die Bucht sortierbar, und was kostet es?")
kind, text = verdict_bay(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: die Bucht von Hand --------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Eine Bucht, die sich nicht sortieren lässt")
hs = _hand_states()
st.caption("3 Stapel der Höchsthöhe 3, 8 Container, **ein** freier Platz; von unten nach oben (1, 4, 7), (5, 2, 6), (3, 8). Die 1 liegt unter der 4 und der 7, die 2 unter der 6, die 3 unter der 8: "
           "Alle drei Stapel enthalten Blocker.")
st.plotly_chart(build_bay(C.HAND_BAY, C.HAND_HEIGHT), width="stretch", key="chart_hand")
ht = ["| Erreichbarer Zustand | Blocker |", "|---|---|"]
for stt in hs:
    ht.append(f"| {', '.join('(' + ', '.join(str(c) for c in x) + ')' for x in stt)} | {A.lb1(stt)} |")
st.markdown("\n".join(ht))
st.warning(f"Mit einem freien Platz kann nur auf den einen Stapel mit Platz gesetzt werden. Das gibt nur **{len(hs)} erreichbare Zustände** (Stapel ohne Reihenfolge gezählt), und in **keinem** ist die Bucht sortiert: "
           f"Sie ist **unlösbar**. Die Untergrenze (Blocker) hätte hier {A.lb1(C.HAND_BAY)} gesagt, ohne zu merken, dass es nicht geht.")

st.markdown("---")

# --- Experiment: Lösbarkeit nach freien Plätzen --------------------------------------------------------------------------------------------------

bands = _bands()
loesbar, ida, vs = bands["loesbar"], bands["ida"], bands["vs"]
st.subheader("🔬 Experiment: Ab wie vielen freien Plätzen geht es?")
st.caption(f"Je Zeile {C.SOLVE_BAYS} feste Buchten (Zufallsbuchten, Seeds ab 0), vorberechnet (`generate_precomputed.py`); Breitensuche mit Zustandslimit {num(C.BAND_CAP)}. „Unlösbar“ ist bewiesen (Zustandsraum erschöpft).")
ta = ["| Zelle, freie Plätze | gelöst | bewiesen unlösbar | am Limit | schon sortiert | Optimum | Untergrenze | Optimum = Untergrenze | größte Zustandszahl |", "|---|---|---|---|---|---|---|---|---|"]
for s_, h_ in C.SOLVE_CELLS:
    for f_ in range(1, C.SOLVE_FREE_MAX + 1):
        c = loesbar[key(s_, h_, f_)]
        ta.append(f"| {s_} × {h_}, {f_} frei | {c['solved']} | {c['unsolvable']} | {c['limit']} | {c['sorted0']} | {dec(c['opt']) if c['opt'] is not None else '–'} | "
                  f"{dec(c['lb1']) if c['lb1'] is not None else '–'} | {c['opt_eq_lb1']} | {num(c['max_states'])} |")
st.markdown("\n".join(ta))
st.plotly_chart(build_solvable(loesbar), width="stretch", key="chart_solvable")
cell_here = (settings.stacks, settings.height) if (settings.stacks, settings.height) in C.SOLVE_CELLS else None
if cell_here:
    st.markdown(f"**Zelle {settings.stacks} × {settings.height} (Ihre Einstellung):**")
    kind, text = verdict_free(loesbar, *cell_here)
    getattr(st, kind)(text)
else:
    st.info(f"Für {settings.stacks} × {settings.height} wurde die Lösbarkeit nicht vorberechnet; die Tabelle zeigt 3 × 3, 4 × 3 und 3 × 4.")

st.markdown("---")

# --- Experiment: die Untergrenze -------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie schwach ist die Untergrenze?")
st.caption(f"Optimum gegen die Zahl der Blocker, Mittel über die gelösten Buchten. Oben die Breitensuche aus der Tabelle davor (Zeilen mit mindestens 10 gelösten Buchten), unten größere Zellen mit IDA\\* "
           f"({C.IDA_BAYS} Buchten, Knotenlimit {num(C.IDA_CAP)}); „gelöst“ heißt: in der Knotengrenze gelöst, ungelöste sind nicht bewiesen unlösbar.")
tb = ["| Zelle, freie Plätze | gelöst | Optimum | Untergrenze | Optimum / Untergrenze | Optimum = Untergrenze | Knoten Median / Maximum |", "|---|---|---|---|---|---|---|"]
for s_, h_, fs_ in C.IDA_CELLS:
    for f_ in fs_:
        c = ida[key(s_, h_, f_)]
        tb.append(f"| {s_} × {h_}, {f_} frei | {c['solved']} von {c['n']} | {dec(c['opt'])} | {dec(c['lb1'])} | {ratio_text(c['ratio'])} | {c['opt_eq_lb1']} | {num(round(c['nodes_median']))} / {num(c['nodes_max'])} |")
st.markdown("\n".join(tb))
st.plotly_chart(build_ratio(loesbar), width="stretch", key="chart_ratio")
lb_key = key(settings.stacks, settings.height, settings.free)
lb_stats = loesbar.get(lb_key) if loesbar.get(lb_key, {}).get("ratio") is not None else ida.get(lb_key)
st.markdown(f"**{settings.stacks} × {settings.height} mit {settings.free} freien Plätzen (Ihre Einstellung):**")
if lb_stats is None or lb_stats.get("ratio") is None:
    st.info("Für diese Einstellung wurde das Optimum nicht vorberechnet; die Tabellen zeigen die gerechneten Zellen.")
else:
    kind, text = verdict_lb(lb_stats, f"{settings.stacks} × {settings.height}, {settings.free} frei")
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Vorsortieren gegen Umlagern -----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Vorsortieren gegen Umlagern beim Abruf")
st.caption(f"Dieselben Buchten ({C.VS_BAYS} je Zeile), die beide Verfahren lösen; Mittel der kleinsten Hubzahl; Relocation restricted (Stück 9). Gezeigt sind Zellen mit genug Platz (3 bis 6 freie Plätze).")
tc = ["| Zelle, freie Plätze | Buchten | Pre-Marshalling | Umlagern beim Abruf | Untergrenze | Verhältnis | Vorsortieren billiger / gleich / teurer |", "|---|---|---|---|---|---|---|"]
for k_ in sorted(vs, key=lambda k: tuple(int(x) for x in k.split(","))):
    c = vs[k_]
    s_, h_, f_ = k_.split(",")
    tc.append(f"| {s_} × {h_}, {f_} frei | {c['n']} | {dec(c['p'])} | {dec(c['r'])} | {dec(c['lb1'])} | {ratio_text(c['ratio'])} | {c['smaller']} / {c['equal']} / {c['larger']} |")
st.markdown("\n".join(tc))
st.plotly_chart(build_vs(vs), width="stretch", key="chart_vs")
vs_stats = vs.get(lb_key)
st.markdown(f"**{settings.stacks} × {settings.height} mit {settings.free} freien Plätzen (Ihre Einstellung):**")
if vs_stats is None:
    st.info("Für diese Einstellung wurde der Vergleich nicht vorberechnet; die Tabelle zeigt 3 × 3, 4 × 3 und 3 × 4.")
else:
    kind, text = verdict_vs(vs_stats, f"{settings.stacks} × {settings.height}, {settings.free} frei")
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Messung, kein Satz** | „Ab einer Stapelhöhe freier Plätze lösbar“ ist an drei Zellen gemessen (je 60 Buchten, 180 Buchten mit genug Platz alle lösbar); kein Beweis. Größere Zellen nur mit IDA\\*: ungelöste Buchten sind dort am Limit, nicht bewiesen unlösbar. | – |
| **Zufallsbuchten** | Jeder Container landet auf einem zufälligen Stapel mit Platz; die Stapel sind ungleich hoch (andere Familie als die vollen Buchten der Stücke davor). Echte Buchten sind oft schon teilweise sortiert. | – |
| **Eine einzige Prioritätsordnung** | Alle Container haben verschiedene Nummern; mit Gruppen gleicher Priorität (üblich in der Literatur) dürfte das Sortieren leichter sein (nicht gemessen). | – |
| **Nur die Hubzahl** | Kranzeit, Fahrwege und Zeitfenster zählen nicht; Vorsortieren kann Arbeit vom Abruf in die Zeit davor verschieben (im Modell nicht gemessen), was die Hubzahl nicht abbildet. | Zielfunktionsdesign (Linie „Zielfunktion“) |
| **Relocation restricted** | Der Vergleich nutzt das restricted Relocation (nur Container über dem Ziel); im unrestricted Relocation wäre das Umlagern nicht teurer. | Stück 3 |
| **Stärkere Untergrenzen nicht gebaut** | Die Untergrenze hier zählt nur Blocker; für das Pre-Marshalling gibt es stärkere (Bortfeldt und Forster, Tierney u. a.), aus dem Gedächtnis zitiert und nicht gelesen. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/vorsortieren-umstauen-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind $S$ Stapel der Höchsthöhe $H$ und $N$ Container mit den Nummern $1, \dots, N$ (kleiner heißt früher abzurufen), dazu $F$ freie Plätze. Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit freiem Platz. Gesucht ist die kleinste Hubzahl bis zu einer sortierten Bucht, in der in jedem Stapel die Nummern von unten nach oben fallen.

| Symbol | Bedeutung |
|---|---|
| $S$, $H$ | Zahl der Stapel und Höchsthöhe eines Stapels |
| $N$ | Zahl der Container (Nummern $1, \dots, N$, kleiner = früher abzurufen) |
| $F$ | Zahl der freien Plätze, $F = S\,H - N$ |
| Blocker | Container, unter dem im selben Stapel ein Container mit kleinerer Nummer liegt |
| $\text{LB1}$ | Untergrenze: Zahl der Blocker |
| $\text{OPT}$ | kleinste Hubzahl bis zu einer sortierten Bucht |
| $d$ | Tiefe der Breitensuche, in der der erste sortierte Zustand auftaucht |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/vorsortieren-umstauen-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Gegeben:** $S$ Stapel mit Höchsthöhe $H$, $N$ Container mit den Nummern $1, \dots, N$ (kleiner = früher abzurufen), $F = S\,H - N$ freie Plätze.

**Ziel.** Eine Bucht heißt **sortiert**, wenn in jedem Stapel die Nummern von unten nach oben fallen, also kein Container über einem kleineren liegt. Ein **Hub** setzt den obersten Container eines Stapels auf einen anderen Stapel mit freiem Platz. Gesucht: die kleinste Hubzahl bis zu einer sortierten Bucht.

**Untergrenze.** Ein Container $c$ ist ein **Blocker**, wenn im selben Stapel unter ihm ein Container mit kleinerer Nummer liegt. Ein Blocker muss mindestens einmal bewegt werden: Der kleinere Container unter ihm kann sich erst bewegen, wenn $c$ weg ist, und ein sortierter Zustand hat keinen Blocker. Also $\text{OPT} \ge \text{LB1} := |\text{Blocker}|$.

**Exakte Suche.** Zustände = Bucht bis auf Vertauschen der Stapel. Die Breitensuche vom Anfangszustand über alle Hübe findet in Tiefe $d$ den ersten sortierten Zustand: $d = \text{OPT}$. Erschöpft sie den erreichbaren Zustandsraum ohne sortierten Zustand, ist die Bucht **unlösbar**.

**Freie Plätze.** Mit $F = 0$ ist kein Hub möglich; mit $F = 1$ kann nur auf den einen Stapel mit Platz gesetzt werden (so entsteht der kleine Zustandsraum der Hand-Bucht). Die Messung zeigt: Ist $F$ kleiner als eine Stapelhöhe $H$, ist ein großer Teil der Buchten unlösbar; ab $F = H$ waren in den drei vollständig durchgerechneten Zellen alle lösbar (kein Beweis).

**Relocation beim Abruf.** Zum Vergleich das Optimum des restricted Relocation derselben Bucht (Stück 5 bis 9): bei jedem Abruf werden nur die Container über dem Ziel bewegt. Das Vorsortieren muss alle Blocker bewegen **und** dabei eine ganze sortierte Anordnung herstellen; das Umlagern bewegt nur, was beim Abruf im Weg liegt.

**Literatur.** Pre-Marshalling nach Bortfeldt und Forster, Tierney u. a.; Branch and Price für das Pre-Marshalling bei van Brink und van der Zwaan (Stück 8 der Reihe, Volltext gelesen). Die hier genannten Zahlen sind eigene Messungen an Zufallsbuchten; die Literatur wurde nicht nachgebaut.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
