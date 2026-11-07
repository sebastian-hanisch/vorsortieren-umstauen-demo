"""Kern: Pre-Marshalling (Bucht sortieren) und zum Vergleich das Relocation beim Abruf (Stück 1 bis 10, verschlankt).

Eine Bucht besteht aus Stapeln (Tupel von unten nach oben) mit den Abrufnummern 1 bis N (kleiner = früher abzurufen).

Pre-Marshalling: Ziel ist eine sortierte Bucht (in jedem Stapel fallen die Nummern von unten nach oben: kein Container über einem früher abzurufenden). Erlaubt ist jeder Hub eines
obersten Containers auf einen anderen Stapel mit Platz; jeder Hub kostet 1.
  lb1      Untergrenze: Zahl der blockierenden Container (jeder muss mindestens einmal bewegt werden).
  solve    Breitensuche über kanonische Zustände (Stapel sortiert): das erste sortierte Ziel ist das Optimum; erschöpft sie den Zustandsraum, ist die Bucht unlösbar.
  ida      IDA* mit lb1 und Zustandsmerken: findet das Optimum, wenn es lösbar ist; bei unlösbaren Buchten läuft sie bis zum Knotenlimit.

Relocation beim Abruf (restricted, Stück 1 bis 9): die nächste Nummer wird abgerufen, liegt sie nicht oben, wird der oberste Container ihres Stapels auf einen anderen Stapel mit Platz gesetzt.
  reloc_search   IDA* mit Untergrenze (Blocker plus Blocker ohne sicheren Stapel, Stück 9) und Zustandsmerken.
"""

from dataclasses import dataclass

INF = 10 ** 9


# ---------------------------------------------------------------- gemeinsame Bausteine

def stack_blockers(stack):
    """Container in einem Stapel (unten nach oben), die über einem früher abzurufenden liegen."""
    total, lowest = 0, INF
    for c in stack:
        if c > lowest:
            total += 1
        else:
            lowest = c
    return total


def lb1(state):
    """Zahl der blockierenden Container (Untergrenze der Hubzahl, Stück 2)."""
    return sum(stack_blockers(s) for s in state)


def is_sorted(state):
    return lb1(state) == 0


def canon(state):
    """Kanonische Form: die Stapel sortiert."""
    return tuple(sorted(state))


def stack_min(stack):
    return min(stack) if stack else INF


# ---------------------------------------------------------------- Pre-Marshalling

def neighbours(state, height):
    """Alle Zustände nach einem Hub: oberster Container eines Stapels auf einen anderen Stapel mit Platz (gleiche Zielstapel nur einmal)."""
    for i, s in enumerate(state):
        if not s:
            continue
        c = s[-1]
        seen = set()
        for j, t in enumerate(state):
            if j == i or len(t) >= height or t in seen:
                continue
            seen.add(t)
            new = list(state)
            new[i] = s[:-1]
            new[j] = t + (c,)
            yield tuple(new)


@dataclass(frozen=True)
class Solved:
    optimum: int | None     # None bei unlösbar oder Limit
    states: int             # Zahl der gesehenen Zustände (bei Limit: das Limit überschritten)
    status: str             # "optimal", "unloesbar" (Zustandsraum erschöpft) oder "limit"


def solve(bay, height, cap=150_000) -> Solved:
    """Breitensuche mit kanonischen Zuständen. Das erste sortierte Ziel ist optimal; wird der Zustandsraum erschöpft, ist die Bucht unlösbar."""
    start = canon(bay)
    if is_sorted(start):
        return Solved(0, 1, "optimal")
    seen = {start}
    frontier = [start]
    depth = 0
    while frontier:
        depth += 1
        nxt = []
        for st in frontier:
            for nb in neighbours(st, height):
                c = canon(nb)
                if c in seen:
                    continue
                if is_sorted(c):
                    return Solved(depth, len(seen) + 1, "optimal")
                seen.add(c)
                nxt.append(c)
                if len(seen) > cap:
                    return Solved(None, len(seen), "limit")
        frontier = nxt
    return Solved(None, len(seen), "unloesbar")


@dataclass(frozen=True)
class IdaResult:
    optimum: int | None     # None am Knotenlimit
    nodes: int
    capped: bool


class _Cap(Exception):
    pass


class _Found(Exception):
    pass


def ida(bay, height, cap=300_000) -> IdaResult:
    """IDA* mit lb1 und Zustandsmerken (kanonisch). Findet das Optimum einer lösbaren Bucht; bei einer unlösbaren läuft sie bis zum Limit (kein Unlösbarkeitsbeweis)."""
    start = canon(bay)
    budget = lb1(start)
    total = 0
    while True:
        b = budget
        nodes = [0]
        table = {}

        def rec(st, g):
            nodes[0] += 1
            if total + nodes[0] > cap:
                raise _Cap
            f = lb1(st)
            if f == 0:
                raise _Found(g)
            if g + f > b:
                return
            if table.get(st, INF) <= g:
                return
            table[st] = g
            for nb in neighbours(st, height):
                rec(canon(nb), g + 1)

        try:
            rec(start, 0)
        except _Found as e:
            return IdaResult(e.args[0], total + nodes[0], False)
        except _Cap:
            return IdaResult(None, cap, True)
        total += nodes[0]
        budget += 1


# ---------------------------------------------------------------- Relocation beim Abruf (restricted)

def autopop(stacks):
    """Ruft ab, was oben liegt und gerade dran ist. Gibt (neue Stapel, abgerufene Nummern in Reihenfolge) zurück."""
    st = [list(s) for s in stacks]
    popped = []
    while True:
        present = [c for s in st for c in s]
        if not present:
            return tuple(tuple(s) for s in st), popped
        t = min(present)
        for s in st:
            if s and s[-1] == t:
                s.pop()
                popped.append(t)
                break
        else:
            return tuple(tuple(s) for s in st), popped


def target_stack(stacks):
    """(nächste Abrufnummer, Index ihres Stapels). Die Bucht darf nicht leer sein."""
    t = min(c for s in stacks for c in s)
    for i, s in enumerate(stacks):
        if t in s:
            return t, i


def reloc_lb(stacks):
    """Untergrenze des Relocation (Stück 9, LB2): Blocker plus Blocker über dem Ziel ohne sicheren Stapel."""
    if not any(stacks):
        return 0
    t, i = target_stack(stacks)
    s = stacks[i]
    above = s[s.index(t) + 1:]
    others = [stack_min(x) for k, x in enumerate(stacks) if k != i]
    top = max(others) if others else -1
    return lb1(stacks) + sum(1 for c in above if c > top)


def _fit_key(stacks, j, c):
    m = stack_min(stacks[j])
    return (0, m) if m > c else (1, -m)


def child_targets(stacks, src, height, c):
    """Zielstapel für den Blocker c in der Reihenfolge der engsten Passung (Stück 1); nur Stapel mit Platz."""
    dests = [j for j in range(len(stacks)) if j != src and len(stacks[j]) < height]
    dests.sort(key=lambda j: (_fit_key(stacks, j, c), j))
    return dests


@dataclass(frozen=True)
class RelocResult:
    optimum: int | None     # None bei Knotenlimit (auch wenn kein Blocker je Platz findet)
    nodes: int
    capped: bool


def reloc_search(bay, height, cap=50_000) -> RelocResult:
    """IDA* für das Relocation beim Abruf (Stück 5 bis 9); bei einer Bucht, in der ein Blocker nirgends Platz findet, läuft sie bis zum Knotenlimit."""
    start = tuple(tuple(s) for s in bay)
    budget = reloc_lb(autopop(start)[0])
    total = 0
    while True:
        b = budget
        nodes = [0]
        table = {}
        found = []

        def rec(state, g):
            nodes[0] += 1
            if total + nodes[0] > cap:
                raise _Cap
            st, _ = autopop(state)
            if not any(st):
                found.append(g)
                raise _Found
            if g + reloc_lb(st) > b:
                return
            key = canon(st)
            if table.get(key, INF) <= g:
                return
            table[key] = g
            _, i = target_stack(st)
            lst = [list(s) for s in st]
            c = lst[i].pop()
            base = tuple(tuple(s) for s in lst)
            for j in child_targets(base, i, height, c):
                nxt = [list(s) for s in lst]
                nxt[j].append(c)
                rec(tuple(tuple(s) for s in nxt), g + 1)

        try:
            rec(start, 0)
        except _Found:
            pass
        except _Cap:
            return RelocResult(None, cap, True)
        total += nodes[0]
        if found:
            return RelocResult(found[0], total, False)
        budget += 1


def reachable_states(bay, height, cap=1_000_000):
    """Alle von der Bucht aus durch Hübe erreichbaren Zustände (kanonisch); bricht beim Limit mit None ab."""
    start = canon(bay)
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for st in frontier:
            for nb in neighbours(st, height):
                c = canon(nb)
                if c not in seen:
                    seen.add(c)
                    nxt.append(c)
                    if len(seen) > cap:
                        return None
        frontier = nxt
    return seen
