"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import pytest

import vso_algorithm as A
import vso_constants as C
import vso_evaluation as ev


def test_a_bay_of_one_container_and_the_extremes_of_the_sliders():
    one = ev.analyse(ev.Settings(3, 3, 8, 0))
    assert one.containers == 1 and one.free == 8 and one.lb1 == 0 and one.solved.optimum == 0 and one.reloc.optimum == 0
    assert ev.verdict_bay(one) == ("info", "Die Bucht ist schon sortiert: 0 Hübe.")
    assert ev.analyse(ev.Settings(3, 3, 8, 5)).containers == 1 and ev.analyse(ev.Settings(5, 5, 8, 0)).containers == 17      # 25 Plätze, 8 frei
    assert ev.analyse(ev.Settings(3, 3, 1, 0)).containers == 8 and ev.analyse(ev.Settings(3, 3, 1, 0)).free == 1


def test_a_full_bay_has_no_moves_and_is_unsolvable_unless_sorted():
    a = ev.analyse(ev.Settings(3, 3, 1, 0))
    assert a.solved.status == "unloesbar" and a.solved.states == 6 and a.free == 1                  # Hand-Bucht (Seed 0): 6 erreichbare Zustände
    assert a.bay == C.HAND_BAY and a.lb1 == 4
    kind, text = ev.verdict_bay(a)
    assert kind == "warning" and text == "Unlösbar: Von dieser Bucht sind 6 Zustände erreichbar, keiner ist sortiert. Frei ist 1 Platz bei Höchsthöhe 3: weniger als eine Stapelhöhe."


def test_unsolvable_with_a_full_stack_height_of_room_is_worded_differently(monkeypatch):
    a = ev.analyse(ev.Settings(3, 3, 1, 0))
    free3 = ev.Analysis(a.bay, 3, 8, 3, a.lb1, a.solved, a.reloc)                                   # künstlich: drei freie Plätze gemeldet
    assert ev.verdict_bay(free3)[1].endswith("Frei sind 3 Plätze bei Höchsthöhe 3: mindestens eine Stapelhöhe.")


def test_limit_and_no_relocation_result_are_reported_without_a_value(monkeypatch):
    monkeypatch.setattr(C, "LIVE_CAP", 50)
    monkeypatch.setattr(C, "RELOC_CAP", 3)
    a = ev.analyse(ev.Settings(4, 3, 3, 0))
    assert a.solved.status == "limit" and a.solved.optimum is None and a.reloc.optimum is None and a.reloc.capped
    assert ev.verdict_bay(a) == ("info", "Nicht entschieden: Die Breitensuche bricht nach 51 Zuständen ab (Limit 50).")
    rows = ev.result_rows(a)
    assert rows[0] == {"name": "Pre-Marshalling (sortieren)", "value": "nicht entschieden", "effort": "Limit 50 Zustände"} and rows[2]["value"] == "kein Ergebnis" and rows[2]["effort"] == "Limit 3 Knoten"


def test_solvable_verdict_wording_without_a_relocation_result(monkeypatch):
    monkeypatch.setattr(C, "RELOC_CAP", 2)
    kind, text = ev.verdict_bay(ev.analyse(ev.Settings(4, 3, 3, 0)))
    assert kind == "info" and "Umlagern beim Abruf: kein Ergebnis (am Limit oder ohne Platz für die Blocker)." in text


def test_stats_on_given_rows():
    rows = [{"seed": 0, "lb1": 0, "opt": 0, "status": "optimal", "states": 1}, {"seed": 1, "lb1": 2, "opt": 6, "status": "optimal", "states": 453},
            {"seed": 2, "lb1": 3, "opt": None, "status": "unloesbar", "states": 7200}, {"seed": 3, "lb1": 4, "opt": None, "status": "limit", "states": 600001}]
    s = ev.pmp_stats(rows)
    assert (s["n"], s["solved"], s["unsolvable"], s["limit"], s["sorted0"], s["max_states"]) == (4, 2, 1, 1, 1, 600001)
    assert s["opt"] == 3 and s["lb1"] == 1 and s["ratio"] == 3 and s["opt_eq_lb1"] == 1                # Mittel über die gelösten: 0 und 6, LB1 0 und 2
    none = ev.pmp_stats([rows[2], rows[3]])
    assert none["solved"] == 0 and none["opt"] is None and none["lb1"] is None and none["ratio"] is None and none["opt_eq_lb1"] == 0
    zero = ev.pmp_stats([rows[0]])
    assert zero["ratio"] is None and zero["opt"] == 0                                                   # Untergrenze 0: kein Verhältnis


def test_ida_and_vs_stats_on_given_rows():
    rows = [{"seed": 0, "lb1": 4, "opt": 8, "nodes": 100}, {"seed": 1, "lb1": 3, "opt": 3, "nodes": 10}, {"seed": 2, "lb1": 5, "opt": None, "nodes": 300000}, {"seed": 3, "lb1": 5, "opt": 9, "nodes": 50}]
    s = ev.ida_stats(rows)
    assert s["n"] == 4 and s["solved"] == 3 and s["opt"] == pytest.approx(20 / 3) and s["lb1"] == 4 and s["ratio"] == pytest.approx(20 / 12) and s["opt_eq_lb1"] == 1
    assert s["nodes_median"] == 50 and s["nodes_max"] == 100                                           # nur die gelösten Läufe zählen
    v = ev.vs_stats([{"seed": 0, "p": 7, "r": 4, "lb1": 4}, {"seed": 1, "p": 3, "r": 3, "lb1": 2}, {"seed": 2, "p": 2, "r": 4, "lb1": 2}])
    assert v["n"] == 3 and v["p"] == 4 and v["r"] == pytest.approx(11 / 3) and v["ratio"] == pytest.approx(12 / 11) and (v["smaller"], v["equal"], v["larger"]) == (1, 1, 1)


def test_number_formats():
    assert ev.num(5) == "5" and ev.num(60234) == "60 234"
    assert ev.dec(5.0) == "5" and ev.dec(3.375) == "3,38" and ev.dec(0.665) == "0,67" and ev.dec(4.999999999) == "5" and ev.dec(1234.5) == "1 234,50"
    assert ev.ratio_text(1.65) == "1,7" and ev.ratio_text(2.0) == "2,0" and ev.ratio_text(1.25) == "1,3"
    assert ev.key(4, 3, 2) == "4,3,2"
