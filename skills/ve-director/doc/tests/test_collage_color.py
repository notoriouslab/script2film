"""doc_themes.ve_theme collage_color (2026-11-22): the colour law replaces the plain and the era palette law; other looks refuse it."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from doc_themes import COLLAGE_COLOR_LAW, VE_THEMES, ve_theme  # noqa: E402


def test_colour_law_replaces_plain_and_era_law():
    for pal in (None, "彌賽亞降臨", "出埃及與曠野"):
        s = ve_theme("collage", pal, True)["style"]
        assert COLLAGE_COLOR_LAW in s and "desaturated" not in s
    assert "ash-rose" in ve_theme("collage", "彌賽亞降臨")["style"]


def test_default_is_unchanged_and_table_not_mutated():
    before = VE_THEMES["collage"]["style"]
    ve_theme("collage", None, True)
    assert VE_THEMES["collage"]["style"] == before == ve_theme("collage")["style"]


def test_other_looks_refuse():
    with pytest.raises(ValueError):
        ve_theme("live", None, True)
