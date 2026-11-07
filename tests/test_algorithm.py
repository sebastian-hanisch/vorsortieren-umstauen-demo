"""Pre-Marshalling und Relocation beim Abruf gegen Handrechnung (DEMO-PLAYBOOK §1b und §12)."""

import pytest

import vso_algorithm as A
from vso_scenario import container_count, free_slots, make_bay


def test_blockers_lb1_and_sortedness_by_hand(hand, easy, tight):
    assert A.stack_blockers((1, 4, 7)) == 2 and A.stack_blockers((5, 2, 6)) == 1 and A.stack_blockers((3, 8)) == 1 and A.stack_blockers((7, 5, 2)) == 0
    assert A.lb1(hand[0]) == 4 and A.lb1(easy[0]) == 1 and A.lb1(tight[0]) == 2
    assert A.is_sorted(((7, 5, 2), (6, 3), ())) and not A.is_sorted(((1, 2),)) and A.is_sorted(()) and A.is_sorted(((),))
    assert A.canon(((3,), (1,), ())) == ((), (1,), (3,)) and A.stack_min(()) == A.INF and A.stack_min((5, 2, 6)) == 2


def test_neighbours_move_only_the_top_to_a_stack_with_room(hand, tight):
    # Hand-Bucht: nur Stapel 3 (3, 8) hat Platz; die 7 (oben auf Stapel 1) und die 6 (oben auf Stapel 2) können dorthin, die 8 findet keinen Platz (die anderen Stapel sind voll)
    assert set(A.neighbours(*hand)) == {((1, 4), (5, 2, 6), (3, 8, 7)), ((1, 4, 7), (5, 2), (3, 8, 6))}
    assert list(A.neighbours(*tight)) == []                                                # kein freier Platz: kein Hub
    assert list(A.neighbours(((1, 2), (), ()), 2)) == [((1,), (2,), ())]                   # zwei leere Stapel liefern nur einen Hub (gleiche Zielstapel zählen einmal)
    assert set(A.neighbours(((1, 2), (3,), ()), 2)) == {((1,), (3, 2), ()), ((1,), (3,), (2,)), ((1, 2), (), (3,))}


def test_solve_by_hand(hand, easy, tight):
    s = A.solve(*easy)
    assert (s.optimum, s.status) == (1, "optimal")
    s = A.solve(*tight)
    assert (s.optimum, s.status, s.states) == (None, "unloesbar", 1)
    s = A.solve(*hand)
    assert (s.optimum, s.status, s.states) == (None, "unloesbar", 6)
    assert A.solve(((7, 5, 2), (6, 3)), 3).optimum == 0 and A.solve(((7, 5, 2), (6, 3)), 3).states == 1      # schon sortiert


def test_reachable_states_of_the_hand_bay(hand):
    states = A.reachable_states(*hand)
    assert len(states) == 6 and not any(A.is_sorted(s) for s in states)
    assert A.canon(hand[0]) in states and A.reachable_states(*hand, cap=3) is None


def test_solve_reports_the_limit_and_a_solvable_bay_needs_the_whole_search():
    bay = make_bay(4, 3, 9, 0)                                                              # (1,), (2, 4, 3), (6, 5, 7), (8, 9): Optimum 7, Untergrenze 4
    assert bay == ((1,), (2, 4, 3), (6, 5, 7), (8, 9)) and A.lb1(bay) == 4
    s = A.solve(bay, 3)
    assert (s.optimum, s.status, s.states) == (7, "optimal", 5364)
    capped = A.solve(bay, 3, cap=100)
    assert capped.optimum is None and capped.status == "limit" and capped.states > 100


def test_ida_agrees_with_the_breadth_first_search_on_solvable_bays():
    for sd in range(15):
        bay = make_bay(3, 3, 6, sd)
        assert A.ida(bay, 3).optimum == A.solve(bay, 3).optimum, sd


def test_ida_hits_the_node_limit_on_an_unsolvable_bay(hand):
    r = A.ida(*hand, cap=200)
    assert r.optimum is None and r.capped and r.nodes == 200


def test_relocation_lb_and_search(hand, easy):
    assert A.reloc_lb(hand[0]) == A.reloc_lb(A.autopop(hand[0])[0]) and A.reloc_lb(()) == 0
    assert A.reloc_search(*easy).optimum == 1                                              # die 2 vom Ziel 1 weg: ein Hub
    assert A.reloc_search(((7, 5, 2), (6, 3)), 3).optimum == 0
    assert A.reloc_search(((1, 5), (2, 3)), 2, cap=40).optimum is None                     # ohne Platz läuft die Suche bis zum Limit
    assert A.reloc_search(make_bay(4, 3, 9, 0), 3).optimum == 4                            # Handwert: Relocation 4 gegen Pre-Marshalling 7


def test_autopop_and_targets():
    assert A.autopop(((1,), (2,))) == (((), ()), [1, 2]) and A.target_stack(((3, 1), (2,))) == (1, 0)
    assert A.child_targets(((), (2, 3), (4,), (5, 6, 7, 8)), 0, 4, 1) == [1, 2]


def test_scenario_by_hand():
    assert container_count(4, 3, 3) == 9 and container_count(3, 3, 8) == 1 and container_count(3, 3, 20) == 1
    bay = make_bay(4, 3, 9, 0)
    assert sorted(c for s in bay for c in s) == list(range(1, 10)) and free_slots(bay, 3) == 3 and all(len(s) <= 3 for s in bay)
    assert make_bay(4, 3, 9, 0) == bay and make_bay(4, 3, 9, 1) != bay                     # deterministisch in den Eingaben
    with pytest.raises(ValueError):
        make_bay(3, 3, 10, 0)
    with pytest.raises(ValueError):
        make_bay(3, 3, 0, 0)
