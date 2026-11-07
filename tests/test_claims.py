"""Aussagen der Demo und des READMEs gegen die vorberechneten Bänder und gegen eine frische Nachrechnung kleiner Zellen (DEMO-PLAYBOOK §5, §12).

Alle Größen sind deterministisch (feste Seeds, Zustands- und Knotenzahlen, keine Zeiten) und müssen bei der Nachrechnung gleich sein."""

import pytest

import vso_constants as C
import vso_evaluation as ev


def K(s, h, f):
    return ev.key(s, h, f)


def _bands():
    return ev.load_bands()


def test_the_stored_cells_cover_exactly_the_cells_of_the_constants():
    b = _bands()
    assert set(b["loesbar"]) == {K(s, h, f) for s, h in C.SOLVE_CELLS for f in range(1, C.SOLVE_FREE_MAX + 1)} and all(c["n"] == C.SOLVE_BAYS for c in b["loesbar"].values())
    assert set(b["ida"]) == {K(s, h, f) for s, h, fs in C.IDA_CELLS for f in fs} and all(c["n"] == C.IDA_BAYS for c in b["ida"].values())
    assert set(b["vs"]) == {K(s, h, f) for s, h, fs in C.VS_CELLS for f in fs} and all(c["n"] <= C.VS_BAYS for c in b["vs"].values())


def test_every_bay_is_solved_unsolvable_or_at_the_limit_and_no_bay_is_at_the_limit_in_the_breadth_first_cells():
    for c in _bands()["loesbar"].values():
        assert c["solved"] + c["unsolvable"] + c["limit"] == c["n"] and c["limit"] == 0


def test_solvability_jumps_at_one_stack_height_of_free_slots():
    b = _bands()["loesbar"]
    for (s, h) in C.SOLVE_CELLS:
        for f in range(1, C.SOLVE_FREE_MAX + 1):
            if f >= h:
                assert b[K(s, h, f)]["solved"] == 60, (s, h, f)                                 # ab einer Stapelhöhe freier Plätze: alle lösbar
            else:
                assert b[K(s, h, f)]["solved"] < 60
        assert ev.threshold_free(b, s, h) == h
    assert [b[K(3, 3, f)]["solved"] for f in (1, 2, 3)] == [3, 23, 60] and [b[K(4, 3, f)]["solved"] for f in (1, 2, 3)] == [1, 19, 60]
    assert [b[K(3, 4, f)]["solved"] for f in (1, 2, 3, 4)] == [0, 1, 16, 60]
    assert sum(b[K(s, h, h)]["solved"] for s, h in C.SOLVE_CELLS) == 180


def test_the_optimum_and_the_lower_bound_numbers_the_readme_quotes():
    b = _bands()["loesbar"]
    assert round(b[K(4, 3, 2)]["opt"], 2) == 5.63 and round(b[K(4, 3, 2)]["lb1"], 2) == 2.26 and round(b[K(4, 3, 3)]["opt"], 2) == 5.03 and round(b[K(3, 4, 4)]["opt"], 2) == 7.12
    assert [round(b[K(4, 3, f)]["ratio"], 1) for f in (2, 3, 4, 6)] == [2.5, 1.8, 1.6, 1.3]
    assert [b[K(4, 3, f)]["opt_eq_lb1"] for f in (3, 4)] == [10, 11] and b[K(3, 4, 4)]["opt_eq_lb1"] == 4 and b[K(4, 3, 3)]["max_states"] == 60234 and b[K(3, 3, 5)]["sorted0"] == 25
    for c in b.values():
        if c["lb1"] is not None:
            assert c["opt"] >= c["lb1"] - 1e-9                                                    # die Untergrenze liegt nie über dem Optimum


def test_the_larger_cells_with_ida_the_readme_quotes():
    ida = _bands()["ida"]
    assert [ida[K(4, 4, f)]["solved"] for f in (4, 5, 6)] == [36, 38, 40] and round(ida[K(4, 4, 4)]["opt"], 2) == 8.64 and round(ida[K(4, 4, 4)]["lb1"], 2) == 4.53
    assert [ida[K(5, 4, f)]["solved"] for f in (4, 5)] == [14, 21] and ida[K(6, 3, 3)]["solved"] == 34 and ida[K(5, 3, 3)]["nodes_max"] == 86621
    assert all(c["opt"] >= c["lb1"] for c in ida.values())


def test_presorting_costs_more_than_relocating_at_the_abruf():
    vs = _bands()["vs"]
    assert all(c["p"] > c["r"] for c in vs.values()) and all(c["smaller"] <= 2 and c["smaller"] + c["equal"] + c["larger"] == c["n"] == 60 for c in vs.values())
    ratios = sorted(round(c["ratio"], 2) for c in vs.values())
    assert ratios[0] == 1.16 and ratios[-1] == 1.69 and round(vs[K(3, 3, 3)]["p"], 2) == 3.38 and round(vs[K(3, 3, 3)]["r"], 2) == 2.05
    assert (vs[K(3, 4, 4)]["smaller"], vs[K(3, 4, 4)]["equal"], vs[K(3, 4, 4)]["larger"]) == (2, 7, 51)


@pytest.mark.parametrize("stacks,height,free", [(3, 3, 1), (3, 3, 2), (3, 3, 3), (4, 3, 2), (3, 4, 3)])
def test_a_fresh_recomputation_of_a_breadth_first_cell_reproduces_the_stored_band(stacks, height, free):
    stored = _bands()["loesbar"][K(stacks, height, free)]
    fresh = ev.pmp_stats(ev.pmp_rows(stacks, height, free, range(C.SOLVE_BAYS)))
    assert fresh == stored


def test_a_fresh_recomputation_of_an_ida_cell_and_a_vs_cell_reproduces_the_stored_bands():
    stored = _bands()["ida"][K(5, 3, 5)]
    assert ev.ida_stats(ev.ida_rows(5, 3, 5, range(C.IDA_BAYS))) == stored
    stored = _bands()["vs"][K(3, 3, 4)]
    assert ev.vs_stats(ev.vs_rows(3, 3, 4, range(C.VS_BAYS))) == stored
