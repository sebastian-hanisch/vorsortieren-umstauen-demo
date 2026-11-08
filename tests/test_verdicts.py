"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import vso_algorithm as A
import vso_constants as C
import vso_evaluation as ev


def _a(status="optimal", opt=7, lb1=4, states=5364, free=3, height=3, reloc=4):
    return ev.Analysis(((1,),), height, 9, free, lb1, A.Solved(opt if status == "optimal" else None, states, status), A.RelocResult(reloc, 5, False))


def test_bay_verdict_states_and_numbers():
    kind, text = ev.verdict_bay(_a())
    assert kind == "info" and text == "Lösbar mit 7 Hüben (Untergrenze 4, nach 5 364 Zuständen); Umlagern beim Abruf: 4 Hübe. Die Untergrenze liegt 3 Hübe unter dem Optimum."
    kind, text = ev.verdict_bay(_a(opt=4, lb1=4))
    assert kind == "success" and text.endswith("Die Zählung der Blocker trifft das Optimum.")
    kind, text = ev.verdict_bay(_a(opt=6, lb1=2, states=453, reloc=2))
    assert kind == "warning" and text.endswith("Die Untergrenze ist schwach: Das Optimum ist 3,0-mal so groß.")
    assert ev.verdict_bay(_a(opt=7, lb1=4))[0] == "info" and ev.verdict_bay(_a(opt=8, lb1=4))[0] == "warning" and C.LB_WEAK == 2.0     # genau das Doppelte zählt schon als schwach
    assert ev.verdict_bay(_a(opt=7, lb1=4, reloc=None))[1].count("kein Ergebnis") == 1
    assert ev.verdict_bay(_a(opt=0, lb1=0, states=1)) == ("info", "Die Bucht ist schon sortiert: 0 Hübe.")


def test_bay_verdict_unsolvable_and_limit_wording():
    kind, text = ev.verdict_bay(_a("unloesbar", free=2, states=7200))
    assert kind == "warning" and text == "Unlösbar: Von dieser Bucht sind 7 200 Zustände erreichbar, keiner ist sortiert. Frei sind 2 Plätze bei Höchsthöhe 3: weniger als eine Stapelhöhe."
    assert ev.verdict_bay(_a("unloesbar", free=3, states=9))[1].endswith("Frei sind 3 Plätze bei Höchsthöhe 3: mindestens eine Stapelhöhe.")
    assert ev.verdict_bay(_a("unloesbar", free=1, states=24))[1].count("Frei ist 1 Platz") == 1
    assert ev.verdict_bay(_a("limit", states=150001)) == ("info", "Nicht entschieden: Die Breitensuche bricht nach 150 001 Zuständen ab (Limit 150 000).")


def test_result_rows_by_hand():
    rows = ev.result_rows(_a())
    assert rows == [{"name": "Pre-Marshalling (sortieren)", "value": "7", "effort": "5 364 Zustände"}, {"name": "Untergrenze (Blocker zählen)", "value": "4", "effort": "–"},
                    {"name": "Relocation beim Abruf (Stück 9)", "value": "4", "effort": "5 Knoten"}]
    assert ev.result_rows(_a("unloesbar", states=24))[0] == {"name": "Pre-Marshalling (sortieren)", "value": "unlösbar", "effort": "24 Zustände erschöpft"}


def _loesbar(solved_by_f, n=60, height_cell=(4, 3)):
    s, h = height_cell
    return {ev.key(s, h, f): {"n": n, "solved": solved_by_f.get(f, n), "unsolvable": n - solved_by_f.get(f, n), "limit": 0} for f in range(1, C.SOLVE_FREE_MAX + 1)}


def test_free_verdict_three_states_and_numbers():
    kind, text = ev.verdict_free(_loesbar({1: 1, 2: 19}), 4, 3)
    assert kind == "success" and text == "4 Stapel, Höhe 3: Mit 3 oder mehr freien Plätzen waren alle 60 Buchten lösbar; mit 1 freien Platz nur 1 von 60, mit 2 nur 19 von 60. Die Grenze liegt bei einer Stapelhöhe (3)."
    kind, text = ev.verdict_free(_loesbar({1: 1}), 4, 3)
    assert kind == "info" and text.startswith("4 Stapel, Höhe 3: Mit 2 oder mehr freien Plätzen waren alle 60 Buchten lösbar; mit 1 freien Platz nur 1 von 60.") and text.endswith("Die Grenze liegt unter einer Stapelhöhe (3).")
    kind, text = ev.verdict_free(_loesbar({1: 0, 2: 1, 3: 16, 4: 40}), 4, 3)
    assert kind == "warning" and text.endswith("Die Grenze liegt über einer Stapelhöhe (3).") and "Mit 5 oder mehr freien Plätzen" in text
    kind, text = ev.verdict_free(_loesbar({6: 59}), 4, 3)
    assert kind == "warning" and text == "4 Stapel, Höhe 3: Auch mit 6 freien Plätzen waren nicht alle Buchten lösbar."
    assert ev.verdict_free(_loesbar({}), 4, 3)[1].count("Mit 1 oder mehr freien Plätzen") == 1 and ev.verdict_free(_loesbar({}), 4, 3)[0] == "info"     # alles lösbar: Grenze unter der Stapelhöhe


def test_threshold_ignores_a_gap_above_the_first_full_row():
    loes = _loesbar({1: 0, 2: 10, 3: 60, 4: 59, 5: 60, 6: 60})                              # bei 4 freien Plätzen fehlt eine Bucht: die Grenze liegt erst bei 5
    assert ev.threshold_free(loes, 4, 3) == 5


def _lb(ratio, opt=8.0, lb1=4.0, eq=2, solved=40):
    return {"ratio": ratio, "opt": opt, "lb1": lb1, "opt_eq_lb1": eq, "solved": solved}


def test_lb_verdict_three_states_and_numbers():
    kind, text = ev.verdict_lb(_lb(2.0), "4 × 4, 4 frei")
    assert kind == "warning" and text == ("4 × 4, 4 frei: Das Optimum ist im Mittel 8 Hübe, die Untergrenze (Blocker) 4: das 2,0-Fache; in 2 von 40 gelösten Buchten trifft die Untergrenze. "
                                          "Die Untergrenze ist hier schwach.")
    assert ev.verdict_lb(_lb(1.99), "x")[0] == "info" and ev.verdict_lb(_lb(1.5), "x")[0] == "info" and ev.verdict_lb(_lb(1.49), "x")[0] == "success" and C.LB_OK == 1.5
    assert ev.verdict_lb(_lb(1.3, 5.2, 4.0), "x")[1].endswith("Die Untergrenze liegt hier nahe am Optimum.")
    assert ev.verdict_lb(_lb(None), "x") == ("info", "x: Keine Zählung möglich (Untergrenze 0 oder keine gelöste Bucht).")


def _vs(p, r, smaller=0, equal=22, larger=38):
    return {"n": smaller + equal + larger, "p": p, "r": r, "ratio": p / r, "smaller": smaller, "equal": equal, "larger": larger}


def test_vs_verdict_three_states_and_numbers():
    kind, text = ev.verdict_vs(_vs(3.38, 2.05), "3 × 3, 3 frei")
    assert kind == "warning" and text == ("3 × 3, 3 frei: Vorsortieren braucht im Mittel 3,38 Hübe, das Umlagern beim Abruf 2,05: das 1,6-Fache; "
                                          "billiger ist das Vorsortieren in 0 von 60 Buchten, gleich teuer in 22, teurer in 38. Vorsortieren spart hier keine Hübe; es verschiebt sie vom Abruf in die Zeit davor (im Modell nicht gemessen).")
    assert ev.verdict_vs(_vs(1.5, 1.0), "x")[0] == "warning" and ev.verdict_vs(_vs(1.49, 1.0), "x")[0] == "info" and C.VS_BIG == 1.5
    kind, text = ev.verdict_vs(_vs(1.1, 1.0), "x")
    assert kind == "info" and text.endswith("Vorsortieren kostet hier etwas mehr Hübe als das Umlagern beim Abruf.") and C.VS_SMALL == 1.1
    kind, text = ev.verdict_vs(_vs(1.05, 1.0, 5, 50, 5), "x")
    assert kind == "success" and text.endswith("Vorsortieren kostet hier kaum mehr als das Umlagern beim Abruf.")
