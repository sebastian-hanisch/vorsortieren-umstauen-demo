"""Orakel-Test vorsortieren-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): Optimum und Lösbarkeit gegen ANDERE Rechenwege.

Eigene, unabhängige Umsetzungen im Test: (a) das Pre-Marshalling-Optimum per Breitensuche über **beschriftete** Zustände (Stapel nicht sortiert, keine Kanonisierung, eigene Hubfunktion),
(b) die Untergrenze per Zählung, (c) das Optimum des Relocation beim Abruf per vollständiger Rekursion ohne Untergrenze. Vorher an den Handzahlen geprüft: Hand-Bucht unlösbar mit
6 erreichbaren Zuständen, LB1 4; (1, 2), (), (): Optimum 1."""

import functools
from collections import deque

import pytest

import vso_algorithm as A
from vso_scenario import make_bay

INF = 10 ** 9


def sorted_bay(state):
    return all(all(s[i] > s[i + 1] for i in range(len(s) - 1)) for s in state)           # streng fallend von unten nach oben (die Nummern sind verschieden)


def ref_lb1(state):
    n = 0
    for s in state:
        for i, c in enumerate(s):
            if any(x < c for x in s[:i]):
                n += 1
    return n


def hubs(state, height):
    out = []
    for i, s in enumerate(state):
        if not s:
            continue
        for j, t in enumerate(state):
            if j != i and len(t) < height:
                new = [list(x) for x in state]
                new[j].append(new[i].pop())
                out.append(tuple(tuple(x) for x in new))
    return out


def ref_pmp(bay, height, cap=400_000):
    """Breitensuche über beschriftete Zustände. Gibt (Optimum | None, 'optimal' | 'unloesbar' | 'limit') zurück."""
    start = tuple(tuple(s) for s in bay)
    if sorted_bay(start):
        return 0, "optimal"
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        st, d = queue.popleft()
        for nb in hubs(st, height):
            if nb in seen:
                continue
            if sorted_bay(nb):
                return d + 1, "optimal"
            seen.add(nb)
            if len(seen) > cap:
                return None, "limit"
            queue.append((nb, d + 1))
    return None, "unloesbar"


def ref_reloc(bay, height):
    """Relocation beim Abruf per vollständiger Rekursion (ohne Untergrenze); INF, wenn ein Blocker nirgends Platz findet."""
    @functools.lru_cache(maxsize=None)
    def rec(state):
        st = [list(s) for s in state]
        while True:                                                                         # abrufen, was oben liegt
            nums = [c for s in st for c in s]
            if not nums:
                return 0
            t = min(nums)
            k = next(i for i, s in enumerate(st) if t in s)
            if st[k][-1] != t:
                break
            st[k].pop()
        best = INF
        for j in range(len(st)):
            if j != k and len(st[j]) < height:
                new = [list(s) for s in st]
                new[j].append(new[k].pop())
                best = min(best, 1 + rec(tuple(sorted(tuple(s) for s in new))))
        return best
    return rec(tuple(sorted(tuple(s) for s in bay)))


def test_lb1_equals_the_independent_count_on_many_bays():
    for stacks, height, free in ((3, 3, 2), (4, 3, 3), (3, 4, 4), (5, 3, 4), (4, 4, 5)):
        for sd in range(40):
            bay = make_bay(stacks, height, stacks * height - free, sd)
            assert A.lb1(bay) == ref_lb1(bay) and A.is_sorted(bay) == sorted_bay(bay)


@pytest.mark.parametrize("stacks,height,free", [(3, 3, 1), (3, 3, 2), (3, 3, 3), (3, 3, 4), (4, 3, 1), (4, 3, 2), (4, 3, 4), (3, 4, 3), (3, 4, 4), (3, 4, 5)])
def test_the_search_equals_the_labelled_breadth_first_search_in_optimum_and_solvability(stacks, height, free):
    n = stacks * height - free
    bays = 25 if (stacks, height, free) in ((4, 3, 2), (3, 4, 3)) else 40
    for sd in range(bays):
        bay = make_bay(stacks, height, n, sd)
        s = A.solve(bay, height)
        assert (s.optimum, s.status) == ref_pmp(bay, height), (stacks, height, free, sd)
        if s.optimum is not None:
            assert s.optimum >= A.lb1(bay)                                                   # die Untergrenze ist zulässig


def test_the_threshold_one_stack_height_of_free_slots_in_the_labelled_search():
    """Die Kernmessung in klein: 3 x 3 mit 3 freien Plätzen (eine Stapelhöhe) war in jeder Bucht lösbar, mit 1 in fast keiner (unabhängig gerechnet)."""
    assert all(ref_pmp(make_bay(3, 3, 6, sd), 3)[1] == "optimal" for sd in range(40))
    assert sum(1 for sd in range(40) if ref_pmp(make_bay(3, 3, 8, sd), 3)[1] == "optimal") <= 4


def test_the_relocation_search_equals_the_independent_recursion():
    n = 0
    for stacks, height, free in ((3, 3, 3), (4, 3, 3), (3, 4, 4), (3, 3, 2), (4, 3, 4)):
        for sd in range(30):
            bay = make_bay(stacks, height, stacks * height - free, sd)
            ref = ref_reloc(bay, height)
            r = A.reloc_search(bay, height, cap=200_000)
            if ref >= INF:
                assert r.optimum is None                                                       # kein Platz für einen Blocker: kein Ergebnis
            else:
                assert r.optimum == ref, (stacks, height, free, sd)
            n += 1
    assert n == 150


def test_ida_equals_the_labelled_search_where_both_finish():
    for sd in range(25):
        bay = make_bay(4, 3, 8, sd)
        opt, status = ref_pmp(bay, 3)
        assert status == "optimal" and A.ida(bay, 3, cap=300_000).optimum == opt


def test_a_sorted_bay_costs_nothing_and_a_move_cannot_unsort_a_sorted_bay_for_free():
    bay = ((7, 5, 2), (6, 3), (9, 8, 4, 1))
    assert A.lb1(bay) == 0 and A.solve(bay, 4).optimum == 0 and ref_pmp(bay, 4) == (0, "optimal")
    assert A.reloc_search(bay, 4).optimum == 0 and ref_reloc(bay, 4) == 0
