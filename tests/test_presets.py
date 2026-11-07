"""Presets: jede Einstellung hat die Eigenschaft, für die sie steht (DEMO-PLAYBOOK §12), und die Hilfetexte nennen nur gemessene Zahlen."""

import pytest

import vso_constants as C
import vso_evaluation as ev
import vso_presets as P


def _analyse(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["height"], p["free"], p["seed"]))


def test_every_preset_is_inside_the_slider_bounds_and_has_help():
    for name, p in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            lo, hi = P.bounds(state_key)
            assert lo <= p[key] <= hi, (name, key)
    assert set(C.PRESET_HELP) == set(C.PRESETS) and all(C.PRESET_HELP.values())


def test_enough_room_bay():
    a = _analyse("Genug Platz (4 Stapel, Höhe 3, 3 frei)")
    assert a.bay == ((1,), (2, 4, 3), (6, 5, 7), (8, 9)) and a.containers == 9 and a.free == 3
    assert (a.solved.optimum, a.solved.states, a.lb1, a.reloc.optimum) == (7, 5364, 4, 4)


def test_one_free_slot_bay_is_unsolvable_with_24_states():
    a = _analyse("Ein freier Platz (4 Stapel, Höhe 3)")
    assert a.containers == 11 and a.free == 1 and a.solved.status == "unloesbar" and a.solved.states == 24 and a.lb1 == 5 and a.reloc.optimum == 7


def test_two_free_slots_one_solvable_one_not():
    ok = _analyse("Zwei frei: lösbar (4 Stapel, Höhe 3)")
    assert (ok.solved.optimum, ok.solved.states, ok.lb1, ok.reloc.optimum) == (6, 453, 2, 2) and ev.verdict_bay(ok)[0] == "warning"
    bad = _analyse("Zwei frei: unlösbar (4 Stapel, Höhe 3)")
    assert bad.solved.status == "unloesbar" and bad.solved.states == 7200 and bad.lb1 == 3 and bad.reloc.optimum == 3 and bad.free == 2


def test_lots_of_room_bay():
    a = _analyse("Viel Platz (4 Stapel, Höhe 3, 6 frei)")
    assert a.containers == 6 and (a.solved.optimum, a.solved.states, a.lb1, a.reloc.optimum) == (3, 59, 2, 2)


def test_presorting_does_not_pay_bay():
    a = _analyse("Vorsortieren lohnt nicht (3 Stapel, Höhe 4)")
    assert a.containers == 8 and (a.solved.optimum, a.lb1, a.reloc.optimum) == (8, 3, 4) and a.solved.optimum == 2 * a.reloc.optimum


def test_the_hand_bay_is_the_one_free_slot_cell_with_seed_0():
    assert C.HAND_BAY == ((1, 4, 7), (5, 2, 6), (3, 8)) and C.HAND_HEIGHT == 3
    assert ev.analyse(ev.Settings(3, 3, 1, 0)).bay == C.HAND_BAY


def test_the_default_settings_are_the_first_preset():
    assert {s: P.SETTING_SPECS[s].default for s in P.SETTING_SPECS} == {"stacks_slider": 4, "height_slider": 3, "free_slider": 3, "seed_input": 0}
    assert C.PRESETS["Genug Platz (4 Stapel, Höhe 3, 3 frei)"] == {"stacks": 4, "height": 3, "free": 3, "seed": 0}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_apply_preset_writes_every_setting(name, monkeypatch):
    state = {}
    monkeypatch.setattr(P.st, "session_state", state)
    P.apply_preset(name)
    assert {k: state[sk] for k, sk in P.PRESET_KEYS.items()} == {k: C.PRESETS[name][k] for k in P.PRESET_KEYS}
    assert P.aktives_preset() == name
