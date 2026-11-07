"""Szenario: Buchten für das Pre-Marshalling. Eine Bucht ist ein Tupel von Stapeln (von unten nach oben) mit den Abrufnummern 1 bis N."""

import random


def container_count(stacks: int, height: int, free: int) -> int:
    """Zahl der Container bei `free` freien Plätzen; mindestens 1."""
    return max(1, stacks * height - free)


def make_bay(stacks: int, height: int, n: int, seed: int) -> tuple:
    """Zufallsbucht: `n` Container mit den Nummern 1 bis n, jeder auf einen zufällig gewählten Stapel mit Platz (Höchsthöhe `height`).
    Deterministisch aus (stacks, height, n, seed). Die Stapel sind danach ungleich hoch; es bleiben stacks * height - n Plätze frei."""
    if not 1 <= n <= stacks * height:
        raise ValueError("n muss zwischen 1 und Stapel * Höchsthöhe liegen")
    rng = random.Random(seed)
    perm = list(range(1, n + 1))
    rng.shuffle(perm)
    st = [[] for _ in range(stacks)]
    for c in perm:
        free = [i for i in range(stacks) if len(st[i]) < height]
        st[rng.choice(free)].append(c)
    return tuple(tuple(s) for s in st)


def free_slots(bay: tuple, height: int) -> int:
    """Zahl der freien Plätze einer Bucht bei Höchsthöhe `height`."""
    return sum(height - len(s) for s in bay)
