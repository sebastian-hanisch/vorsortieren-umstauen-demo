"""Erzeugt vso_bands.json: Kennzahlen der festen Buchten (Seeds ab 0) für drei Auswertungen.

    python generate_precomputed.py

"loesbar": je Zelle (SOLVE_CELLS) und freie Plätze 1 bis SOLVE_FREE_MAX die Breitensuche (SOLVE_BAYS Buchten): gelöst, bewiesen unlösbar, am Limit, Optimum, LB1.
"ida":     je Zelle aus IDA_CELLS und freien Plätzen IDA* (IDA_BAYS Buchten, Knotenlimit IDA_CAP): Optimum, LB1, Knoten.
"vs":      je Zelle aus VS_CELLS Pre-Marshalling gegen Relocation beim Abruf (VS_BAYS Buchten).

Rechenzeit einige Minuten (3 x 4 mit 3 freien Plätzen und die IDA*-Zellen 5 x 4 und 6 x 3 sind die langsamsten; die Zellen laufen in getrennten Prozessen). Dieselben Funktionen wie die
Tests (`vso_evaluation.pmp_rows`, `pmp_stats`, `ida_rows`, `ida_stats`, `vs_rows`, `vs_stats`); die Datei speichert nur Kennzahlen, keine Zeilen."""

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import vso_constants as C
import vso_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def job(kind, stacks, height, free):
    k = ev.key(stacks, height, free)
    if kind == "loesbar":
        return "loesbar", k, ev.pmp_stats(ev.pmp_rows(stacks, height, free, range(C.SOLVE_BAYS)))
    if kind == "ida":
        return "ida", k, ev.ida_stats(ev.ida_rows(stacks, height, free, range(C.IDA_BAYS)))
    return "vs", k, ev.vs_stats(ev.vs_rows(stacks, height, free, range(C.VS_BAYS)))


def main():
    tasks = [("ida", s, h, f) for s, h, fs in C.IDA_CELLS for f in fs]
    tasks += [("loesbar", s, h, f) for s, h in C.SOLVE_CELLS for f in range(C.SOLVE_FREE_MAX, 0, -1)]
    tasks += [("vs", s, h, f) for s, h, fs in C.VS_CELLS for f in fs]
    out = {"loesbar": {}, "ida": {}, "vs": {}}
    with ProcessPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) - 2)) as pool:
        futures = {pool.submit(job, *t): t for t in tasks}
        for fut in as_completed(futures):
            kind, k, stats = fut.result()
            out[kind][k] = stats
            print(kind, k, "fertig", flush=True)
    with open("vso_bands.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("geschrieben: vso_bands.json", flush=True)


if __name__ == "__main__":
    main()
