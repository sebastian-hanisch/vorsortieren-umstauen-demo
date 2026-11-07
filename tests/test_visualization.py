"""Abbildungen an synthetischen Daten: Werte, Farben, gesperrte Achsen (DEMO-PLAYBOOK §12)."""

import plotly.graph_objects as go
import pytest

import vso_constants as C
import vso_evaluation as ev
import vso_visualization as V


def _locked(fig):
    return fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


def test_blocker_cells_by_hand():
    assert V.blocker_cells(((1, 4, 7), (5, 2, 6), (3, 8))) == {(0, 1), (0, 2), (1, 2), (2, 1)}
    assert V.blocker_cells(((7, 5, 2), (), (6,))) == set() and V.blocker_cells(((1, 2, 3),)) == {(0, 1), (0, 2)}


def test_bay_chart_with_free_slots_colours_and_height_line():
    fig = V.build_bay(((1, 4, 7), (5, 2, 6), (3, 8)), 3)
    assert _locked(fig) and len(fig.data) == 3 and list(fig.layout.yaxis.range) == [0, 3.35]
    assert list(fig.data[0].marker.color) == [C.COLOR_CELL] * 3 and list(fig.data[1].marker.color) == [C.COLOR_BLOCK, C.COLOR_CELL, C.COLOR_BLOCK]
    assert list(fig.data[2].y) == [1, 1, 0] and list(fig.data[2].text) == ["7", "6", ""]              # der dritte Stapel hat in der obersten Lage einen freien Platz
    assert [s.y0 for s in fig.layout.shapes] == [3] and list(fig.layout.xaxis.ticktext) == ["Stapel 1", "Stapel 2", "Stapel 3"]


def _loesbar():
    out = {}
    for s, h in C.SOLVE_CELLS:
        for f in range(1, C.SOLVE_FREE_MAX + 1):
            solved = 60 if f >= h else 10 * f
            out[ev.key(s, h, f)] = {"n": 60, "solved": solved, "ratio": None if solved < 10 else 4.0 / f if solved else None}
    return out


def test_solvable_chart_shows_shares_in_percent_for_each_cell():
    fig = V.build_solvable(_loesbar())
    assert _locked(fig) and list(fig.layout.yaxis.range) == [0, 105] and not fig.layout.shapes and len(fig.data) == 3
    assert [t.name for t in fig.data] == ["3 Stapel, Höhe 3", "4 Stapel, Höhe 3", "3 Stapel, Höhe 4"]
    assert list(fig.data[0].y) == pytest.approx([100 * 10 / 60, 100 * 20 / 60, 100.0, 100.0, 100.0, 100.0]) and list(fig.data[2].y)[3] == 100.0 and list(fig.data[2].y)[2] == pytest.approx(50.0)
    assert list(fig.data[0].x) == [1, 2, 3, 4, 5, 6] and [t.line.color for t in fig.data] == [C.COLOR_LINES[3], C.COLOR_LINES[3], C.COLOR_LINES[4]]


def test_ratio_chart_leaves_out_rows_with_fewer_than_ten_solved_bays_or_no_ratio():
    loes = _loesbar()
    loes[ev.key(3, 3, 6)]["ratio"] = None                                                              # keine Untergrenze: Zeile fehlt
    fig = V.build_ratio(loes)
    assert _locked(fig) and fig.layout.yaxis.rangemode == "tozero"
    assert list(fig.data[0].x) == [1, 2, 3, 4, 5] and list(fig.data[1].x) == [1, 2, 3, 4, 5, 6] and list(fig.data[0].y)[0] == pytest.approx(4.0)


def test_vs_chart_is_ordered_and_has_three_bars_per_cell():
    vs = {"4,3,3": {"p": 5.03, "r": 3.25, "lb1": 2.78}, "3,3,4": {"p": 1.9, "r": 1.45, "lb1": 1.25}, "3,4,4": {"p": 7.12, "r": 4.27, "lb1": 3.02}}
    fig = V.build_vs(vs)
    assert _locked(fig) and list(fig.data[0].x) == ["3 × 3, 4 frei", "3 × 4, 4 frei", "4 × 3, 3 frei"]
    assert [t.name for t in fig.data] == ["Pre-Marshalling", "Relocation beim Abruf", "Untergrenze (Blocker)"] and list(fig.data[0].y) == [1.9, 7.12, 5.03]
    assert [t.marker.color for t in fig.data] == [C.COLOR_PMP, C.COLOR_RELOC, C.COLOR_LB]


def test_all_figures_are_plotly_figures():
    assert all(isinstance(f, go.Figure) for f in (V.build_bay(((1,),), 2), V.build_solvable(_loesbar()), V.build_ratio(_loesbar())))
