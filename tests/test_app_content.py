"""Inhalt der App an festen Fällen (DEMO-PLAYBOOK §12): was im Ergebnis, in den Tabellen und in den Verdikten steht."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(preset=None):
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    if preset:
        at.sidebar.button(key=f"preset_{preset}").click().run()
        assert not at.exception, [str(e) for e in at.exception]
    return at


def _text(at):
    return "\n".join(e.value for kind in (at.markdown, at.caption, at.info, at.success, at.warning) for e in kind)


def _metrics(at):
    return {m.label: (m.value, m.delta) for m in at.metric}


def test_default_page_has_the_sections_and_the_default_result():
    at = _run()
    subs = [s.value for s in at.subheader]
    assert [s for s in subs if s.startswith("🔬")] == ["🔬 Experiment: Eine Bucht, die sich nicht sortieren lässt", "🔬 Experiment: Ab wie vielen freien Plätzen geht es?",
                                                       "🔬 Experiment: Wie schwach ist die Untergrenze?", "🔬 Experiment: Vorsortieren gegen Umlagern beim Abruf"]
    assert "🚧 Wo die Annahmen enden" in subs
    m = _metrics(at)
    assert m["Container"] == ("9", "3 frei bei Höchsthöhe 3") and m["Pre-Marshalling"] == ("7", "5 364 Zustände") and m["Untergrenze"][0] == "4" and m["Umlagern beim Abruf"][0] == "4"
    assert any(i.value.startswith("Lösbar mit 7 Hüben (Untergrenze 4, nach 5 364 Zuständen); Umlagern beim Abruf: 4 Hübe.") for i in at.info)


def test_default_page_tables_and_verdicts_quote_the_stored_numbers():
    text = _text(_run())
    assert "| 3 × 3, 2 frei | 23 | 37 | 0 | 7 | 3,35 | 1,35 | 11 | 144 |" in text and "| 4 × 3, 3 frei | 60 | 0 | 0 | 2 | 5,03 | 2,78 | 10 | 60 234 |" in text
    assert "| 3 × 4, 1 frei | 0 | 60 | 0 | 0 | – | – | 0 | 6 |" in text
    assert "| 4 × 4, 4 frei | 36 von 40 | 8,64 | 4,53 | 1,9 | 0 | 15 255 / 291 277 |" in text
    assert "| 3 × 3, 3 frei | 60 | 3,38 | 2,05 | 1,65 | 1,7 | 0 / 22 / 38 |" in text
    assert "4 Stapel, Höhe 3: Mit 3 oder mehr freien Plätzen waren alle 60 Buchten lösbar; mit 1 freien Platz nur 1 von 60, mit 2 nur 19 von 60. Die Grenze liegt bei einer Stapelhöhe (3)." in text
    assert "4 × 3, 3 frei: Das Optimum ist im Mittel 5,03 Hübe, die Untergrenze (Blocker) 2,78: das 1,8-Fache; in 10 von 60 gelösten Buchten trifft die Untergrenze. Die Untergrenze ist hier mäßig." in text
    assert "4 × 3, 3 frei: Vorsortieren braucht im Mittel 5,03 Hübe, das Umlagern beim Abruf 3,25: das 1,5-Fache;" in text


def test_hand_section_lists_the_six_states_and_says_unsolvable():
    text = _text(_run())
    assert "Das gibt nur **6 erreichbare Zustände**" in text and "**unlösbar**" in text and "hätte hier 4 gesagt" in text
    assert "| (1, 4), (3, 8, 6), (5, 2, 7) | 4 |" in text and "| (1, 4, 7), (3, 8, 6), (5, 2) | 4 |" in text           # in allen sechs Zuständen bleiben vier Blocker


def test_one_free_slot_preset_shows_the_unsolvable_warning():
    at = _run("Ein freier Platz (4 Stapel, Höhe 3)")
    assert _metrics(at)["Pre-Marshalling"] == ("unlösbar", "24 Zustände") and _metrics(at)["Umlagern beim Abruf"][0] == "7"
    assert any(w.value == "Unlösbar: Von dieser Bucht sind 24 Zustände erreichbar, keiner ist sortiert. Frei ist 1 Platz bei Höchsthöhe 3: weniger als eine Stapelhöhe." for w in at.warning)


def test_presorting_does_not_pay_preset_shows_the_vs_warning():
    at = _run("Vorsortieren lohnt nicht (3 Stapel, Höhe 4)")
    assert _metrics(at)["Pre-Marshalling"][0] == "8" and _metrics(at)["Umlagern beim Abruf"][0] == "4"
    assert any("Vorsortieren spart hier keine Hübe" in w.value for w in at.warning)


@pytest.mark.parametrize("stacks,height,free", [(5, 5, 8), (3, 5, 2)])
def test_settings_without_stored_bands_do_not_crash(stacks, height, free):
    at = _run()
    at.sidebar.slider(key="stacks_slider").set_value(stacks).run()
    at.sidebar.slider(key="height_slider").set_value(height).run()
    at.sidebar.slider(key="free_slider").set_value(free).run()
    assert not at.exception
    text = _text(at)
    assert "wurde die Lösbarkeit nicht vorberechnet" in text and "wurde das Optimum nicht vorberechnet" in text and "wurde der Vergleich nicht vorberechnet" in text
