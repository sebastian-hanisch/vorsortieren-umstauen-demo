"""Kennzahlen, Verdikt-Logik, vorberechnete Tabellen. Reine Funktionen: die App ruft st.<Art>(Text), die Tests prüfen jede Zahl und jede Schwelle."""

import json
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from statistics import mean, median

import vso_algorithm as A
import vso_constants as C
from vso_scenario import container_count, make_bay

BANDS_FILE = Path(__file__).resolve().parent / "vso_bands.json"


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    height: int = C.DEFAULT_HEIGHT
    free: int = C.DEFAULT_FREE
    seed: int = 0


@dataclass(frozen=True)
class Analysis:
    bay: tuple
    height: int
    containers: int
    free: int               # tatsächlich freie Plätze der Bucht
    lb1: int
    solved: A.Solved
    reloc: A.RelocResult


def analyse(settings: Settings) -> Analysis:
    n = container_count(settings.stacks, settings.height, settings.free)
    bay = make_bay(settings.stacks, settings.height, n, settings.seed)
    return Analysis(bay, settings.height, n, settings.stacks * settings.height - n, A.lb1(bay), A.solve(bay, settings.height, C.LIVE_CAP), A.reloc_search(bay, settings.height, C.RELOC_CAP))


# ---------------------------------------------------------------- Formate

def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def _half_up(x: float, digits: int) -> str:
    """Kaufmännisch gerundet (…5 rundet auf) mit `digits` Nachkommastellen (vermeidet die Binärdarstellung: 1,635 als 1,63)."""
    d = Decimal(repr(round(float(x), 9))).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    return f"{d:.{digits}f}"


def dec(x: float, digits: int = 2) -> str:
    """Dezimalzahl mit Komma und Leerzeichen als Tausendertrenner; ganzzahlige Werte ohne Nachkommastellen."""
    x = round(float(x), 6)
    if x.is_integer():
        return num(int(x))
    whole, frac = _half_up(x, digits).split(".")
    return f"{num(int(whole))},{frac}"


def ratio_text(x: float) -> str:
    """Verhältnis mit einer Nachkommastelle (Komma)."""
    return _half_up(x, 1).replace(".", ",")


# ---------------------------------------------------------------- Verdikt einer Bucht

def verdict_bay(a: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage: ist die Bucht sortierbar, und wie weit liegt die Untergrenze vom Optimum?"""
    s = a.solved
    if s.status == "optimal" and s.optimum == 0:
        return "info", "Die Bucht ist schon sortiert: 0 Hübe."
    if s.status == "unloesbar":
        more = ("weniger als eine Stapelhöhe" if a.free < a.height else "mindestens eine Stapelhöhe")
        return "warning", (f"Unlösbar: Von dieser Bucht sind {num(s.states)} Zustände erreichbar, keiner ist sortiert. Frei {'ist' if a.free == 1 else 'sind'} {a.free} {'Platz' if a.free == 1 else 'Plätze'} bei Höchsthöhe {a.height}: {more}.")
    if s.status == "limit":
        return "info", f"Nicht entschieden: Die Breitensuche bricht nach {num(s.states)} Zuständen ab (Limit {num(C.LIVE_CAP)})."
    reloc = f"{a.reloc.optimum} Hübe" if a.reloc.optimum is not None else "kein Ergebnis (am Limit oder ohne Platz für die Blocker)"
    text = f"Lösbar mit {s.optimum} Hüben (Untergrenze {a.lb1}, nach {num(s.states)} Zuständen); Umlagern beim Abruf: {reloc}."
    if s.optimum == a.lb1:
        return "success", text + " Die Zählung der Blocker trifft das Optimum."
    if s.optimum >= C.LB_WEAK * a.lb1:
        return "warning", text + f" Die Untergrenze ist schwach: Das Optimum ist {ratio_text(s.optimum / a.lb1)}-mal so groß."
    return "info", text + f" Die Untergrenze liegt {s.optimum - a.lb1} Hübe unter dem Optimum."


def result_rows(a: Analysis) -> list[dict]:
    """Zeilen der Ergebnistabelle."""
    s, r = a.solved, a.reloc
    if s.status == "optimal":
        pmp = (str(s.optimum), f"{num(s.states)} Zustände")
    elif s.status == "unloesbar":
        pmp = ("unlösbar", f"{num(s.states)} Zustände erschöpft")
    else:
        pmp = ("nicht entschieden", f"Limit {num(C.LIVE_CAP)} Zustände")
    rel = (str(r.optimum), f"{num(r.nodes)} Knoten") if r.optimum is not None else ("kein Ergebnis", f"Limit {num(C.RELOC_CAP)} Knoten")
    return [{"name": "Pre-Marshalling (sortieren)", "value": pmp[0], "effort": pmp[1]},
            {"name": "Untergrenze (Blocker zählen)", "value": str(a.lb1), "effort": "–"},
            {"name": "Relocation beim Abruf (Stück 9)", "value": rel[0], "effort": rel[1]}]


# ---------------------------------------------------------------- Stichproben (vorberechnet)

def key(stacks: int, height: int, free: int) -> str:
    return f"{stacks},{height},{free}"


def pmp_rows(stacks: int, height: int, free: int, seeds, cap: int = C.BAND_CAP) -> list[dict]:
    """Je Bucht: LB1, Ergebnis der Breitensuche (Optimum, Status, Zustände)."""
    n = container_count(stacks, height, free)
    out = []
    for sd in seeds:
        bay = make_bay(stacks, height, n, sd)
        r = A.solve(bay, height, cap)
        out.append({"seed": sd, "lb1": A.lb1(bay), "opt": r.optimum, "status": r.status, "states": r.states})
    return out


def pmp_stats(rows: list[dict]) -> dict:
    """Je Zelle: Zahl der Buchten, gelöst, bewiesen unlösbar, am Limit, schon sortiert; Mittel von Optimum und LB1 über die gelösten, Treffer der Untergrenze, größte Zustandszahl."""
    solved = [r for r in rows if r["status"] == "optimal"]
    out = {"n": len(rows), "solved": len(solved), "unsolvable": sum(1 for r in rows if r["status"] == "unloesbar"), "limit": sum(1 for r in rows if r["status"] == "limit"),
           "sorted0": sum(1 for r in solved if r["opt"] == 0), "max_states": max(r["states"] for r in rows), "opt": None, "lb1": None, "ratio": None, "opt_eq_lb1": 0}
    if solved:
        out["opt"], out["lb1"] = mean(r["opt"] for r in solved), mean(r["lb1"] for r in solved)
        out["ratio"] = out["opt"] / out["lb1"] if out["lb1"] else None
        out["opt_eq_lb1"] = sum(1 for r in solved if r["opt"] == r["lb1"])
    return out


def ida_rows(stacks: int, height: int, free: int, seeds, cap: int = C.IDA_CAP) -> list[dict]:
    """Je Bucht: LB1 und das Optimum aus IDA* (None am Knotenlimit)."""
    n = container_count(stacks, height, free)
    out = []
    for sd in seeds:
        bay = make_bay(stacks, height, n, sd)
        r = A.ida(bay, height, cap)
        out.append({"seed": sd, "lb1": A.lb1(bay), "opt": r.optimum, "nodes": r.nodes})
    return out


def ida_stats(rows: list[dict]) -> dict:
    solved = [r for r in rows if r["opt"] is not None]
    out = {"n": len(rows), "solved": len(solved), "opt": mean(r["opt"] for r in solved), "lb1": mean(r["lb1"] for r in solved), "opt_eq_lb1": sum(1 for r in solved if r["opt"] == r["lb1"]),
           "nodes_median": float(median(r["nodes"] for r in solved)), "nodes_max": max(r["nodes"] for r in solved)}
    out["ratio"] = out["opt"] / out["lb1"] if out["lb1"] else None
    return out


def vs_rows(stacks: int, height: int, free: int, seeds) -> list[dict]:
    """Je Bucht, die beide Verfahren lösen: Optimum des Pre-Marshalling, Optimum des Relocation beim Abruf, LB1."""
    n = container_count(stacks, height, free)
    out = []
    for sd in seeds:
        bay = make_bay(stacks, height, n, sd)
        p = A.solve(bay, height, C.BAND_CAP)
        r = A.reloc_search(bay, height, 1_000_000)
        if p.optimum is None or r.optimum is None:
            continue
        out.append({"seed": sd, "p": p.optimum, "r": r.optimum, "lb1": A.lb1(bay)})
    return out


def vs_stats(rows: list[dict]) -> dict:
    p, r = mean(x["p"] for x in rows), mean(x["r"] for x in rows)
    return {"n": len(rows), "p": p, "r": r, "lb1": mean(x["lb1"] for x in rows), "ratio": p / r if r else None,
            "smaller": sum(1 for x in rows if x["p"] < x["r"]), "equal": sum(1 for x in rows if x["p"] == x["r"]), "larger": sum(1 for x in rows if x["p"] > x["r"])}


def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"loesbar": {"s,h,f": pmp_stats}, "ida": {"s,h,f": ida_stats}, "vs": {"s,h,f": vs_stats}}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- Verdikte der Tabellen

def threshold_free(loesbar: dict, stacks: int, height: int) -> int | None:
    """Kleinste Zahl freier Plätze, ab der (bis SOLVE_FREE_MAX) alle Buchten der Zelle gelöst sind; None, wenn selbst bei SOLVE_FREE_MAX nicht alle."""
    result = None
    for f in range(C.SOLVE_FREE_MAX, 0, -1):
        c = loesbar[key(stacks, height, f)]
        if c["solved"] == c["n"]:
            result = f
        else:
            break
    return result


def verdict_free(loesbar: dict, stacks: int, height: int) -> tuple[str, str]:
    """Verdikt „Lösbarkeit nach freien Plätzen“ für eine Zelle."""
    name = f"{stacks} Stapel, Höhe {height}"
    f0 = threshold_free(loesbar, stacks, height)
    if f0 is None:
        return "warning", f"{name}: Auch mit {C.SOLVE_FREE_MAX} freien Plätzen waren nicht alle Buchten lösbar."
    one = loesbar[key(stacks, height, 1)]
    n = one["n"]
    text = f"{name}: Mit {f0} oder mehr freien Plätzen waren alle {n} Buchten lösbar; mit 1 freien Platz nur {one['solved']} von {n}"
    if f0 > 2:                                                          # bei f0 = 2 ist „mit f0 − 1“ schon der Fall „mit 1 freien Platz“
        prev = loesbar[key(stacks, height, f0 - 1)]
        text += f", mit {f0 - 1} nur {prev['solved']} von {n}"
    text += "."
    if f0 == height:
        return "success", text + f" Die Grenze liegt bei einer Stapelhöhe ({height})."
    if f0 < height:
        return "info", text + f" Die Grenze liegt unter einer Stapelhöhe ({height})."
    return "warning", text + f" Die Grenze liegt über einer Stapelhöhe ({height})."


def verdict_lb(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „wie nah ist die Untergrenze?“ für eine Zeile mit Mittelwerten (pmp_stats oder ida_stats)."""
    if stats["ratio"] is None:
        return "info", f"{name}: Keine Zählung möglich (Untergrenze 0 oder keine gelöste Bucht)."
    r = stats["ratio"]
    text = (f"{name}: Das Optimum ist im Mittel {dec(stats['opt'])} Hübe, die Untergrenze (Blocker) {dec(stats['lb1'])}: das {ratio_text(r)}-Fache; "
            f"in {stats['opt_eq_lb1']} von {stats['solved']} gelösten Buchten trifft die Untergrenze.")
    if r >= C.LB_WEAK:
        return "warning", text + " Die Untergrenze ist hier schwach."
    if r >= C.LB_OK:
        return "info", text + " Die Untergrenze ist hier mäßig."
    return "success", text + " Die Untergrenze liegt hier nahe am Optimum."


def verdict_vs(stats: dict, name: str) -> tuple[str, str]:
    """Verdikt „Vorsortieren gegen Umlagern beim Abruf“ für eine Zelle."""
    r = stats["ratio"]
    text = (f"{name}: Vorsortieren braucht im Mittel {dec(stats['p'])} Hübe, das Umlagern beim Abruf {dec(stats['r'])}: das {ratio_text(r)}-Fache; "
            f"billiger ist das Vorsortieren in {stats['smaller']} von {stats['n']} Buchten, gleich teuer in {stats['equal']}, teurer in {stats['larger']}.")
    if r >= C.VS_BIG:
        return "warning", text + " Vorsortieren spart hier keine Hübe, es verschiebt sie nur in die ruhige Zeit."
    if r >= C.VS_SMALL:
        return "info", text + " Vorsortieren kostet hier etwas mehr Hübe als das Umlagern beim Abruf."
    return "success", text + " Vorsortieren kostet hier kaum mehr als das Umlagern beim Abruf."
