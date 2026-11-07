"""Gemeinsame Fixtures: die Buchten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def hand():
    """Die Bucht von Hand: (1, 4, 7), (5, 2, 6), (3, 8), Höchsthöhe 3, ein freier Platz. Blocker: 4 und 7 über der 1, die 6 über der 2, die 8 über der 3: LB1 = 4. Nur der Stapel (3, 8) hat Platz:
    ein Hub setzt die 7, die 6 oder die 8 dorthin; es gibt genau sechs erreichbare Zustände (bis auf Vertauschen der Stapel), in keinem ist die Bucht sortiert: unlösbar."""
    return ((1, 4, 7), (5, 2, 6), (3, 8)), 3


@pytest.fixture
def easy():
    """Eine Bucht mit genug Platz: (1, 2), (), (), Höchsthöhe 2. Die 2 liegt über der 1 (ein Blocker): ein Hub auf einen leeren Stapel genügt, Optimum 1 = LB1."""
    return ((1, 2), (), ()), 2


@pytest.fixture
def tight():
    """Ohne freien Platz: (1, 3), (2, 4), Höchsthöhe 2. Zwei Blocker (3 und 4), aber kein Hub möglich (beide Stapel voll): der einzige erreichbare Zustand ist der Anfang, unlösbar."""
    return ((1, 3), (2, 4)), 2
