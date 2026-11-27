"""doc_voice pinned(): voice.pick names the take a line uses, whatever its score."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_voice  # noqa: E402


def take(score, name):
    return (score, Path("tts_lines") / name, [], 0, 1.0, None, 0.0, None)


ROW = [take(0.81, "a_11.wav"), take(0.80, "a_12.wav"), take(0.81, "a_13.wav")]


def test_pick_returns_the_named_take_even_with_a_lower_score():
    assert doc_voice.pinned(ROW, 5, {"5": "a_12.wav"})[1].name == "a_12.wav"


def test_no_pick_for_the_line():
    assert doc_voice.pinned(ROW, 4, {"5": "a_12.wav"}) is None
    assert doc_voice.pinned(ROW, 5, None) is None
    assert doc_voice.pinned(ROW, 5, {}) is None


def test_a_take_that_is_gone_stops_the_run():
    with pytest.raises(SystemExit) as e:
        doc_voice.pinned(ROW, 5, {"5": "a_99.wav"})
    assert "a_99.wav" in str(e.value) and "a_12.wav" in str(e.value)
