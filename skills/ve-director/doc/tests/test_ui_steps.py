"""ui_steps (scenes/ui_steps.js, doc_code.ui_params): a drawn app panel whose parts change state on the spoken word.
The parameter checks stop a beat that would show the wrong thing; the page tests check where the panel sits (clear of the
subtitles and of an avatar peek) and that every action lands on its word, never before its part is on screen."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_code  # noqa: E402

LINE = "Click Code at the top of the sidebar, pick Local, then Open folder, and choose an empty one."
TOKENS = [[w, round(.05 + k * .36, 2)] for k, w in enumerate(doc_code.tokens(LINE, "en"))]
BEAT = {"id": "B6", "duration": 7.0, "tokens": TOKENS}
DOC = {"lang": "en"}
B6 = [{"kind": "menu", "label": "Chat", "items": ["Chat", "Code"], "pick": "Code", "pick_at": "Click Code"},
      {"kind": "toggle", "options": ["Cloud", "Local"], "picks": [{"pick": "Local", "at": "pick Local"}]},
      {"kind": "button", "text": "Open folder…", "press_at": "Open folder"},
      {"kind": "check", "text": "an empty folder", "check_at": "empty one"}]
WORD = {w: t for w, t in TOKENS}


def stop(params, doc=DOC):
    with pytest.raises(SystemExit) as e:
        doc_code.ui_params(None, BEAT, params, doc)
    return str(e.value)


# ---------- parameters ----------

def test_a_good_panel_passes_and_gets_its_scale_cap():
    assert doc_code.ui_params(None, BEAT, {"widgets": B6}, DOC)["_scale_max"] == 1.35


def test_unknown_kind_stops():
    assert "kind must be one of" in stop({"widgets": [{"kind": "slider", "text": "x"}]})


@pytest.mark.parametrize("n", [0, 6])
def test_widget_count_outside_one_to_five_stops(n):
    assert "1-5 widgets" in stop({"widgets": [{"kind": "card", "text": "x"}] * n})


def test_missing_field_stops():
    assert "needs check_at" in stop({"widgets": [{"kind": "check", "text": "x"}]})


def test_toggle_pick_not_an_option_stops():
    assert "not among its options" in stop({"widgets": [{"kind": "toggle", "options": ["Cloud", "Local"], "picks": [{"pick": "SSH", "at": 1}]}]})


def test_menu_pick_not_an_item_stops():
    assert "is not one of its items" in stop({"widgets": [{"kind": "menu", "label": "Chat", "items": ["Chat", "Code"], "pick": "SSH", "pick_at": 1}]})


def test_a_part_whose_own_at_is_after_its_action_stops():
    w = {"kind": "button", "text": "Open folder…", "press_at": "Open folder", "at": "empty one"}
    assert "after its own action" in stop({"widgets": [w]})


def test_a_part_without_at_is_not_stopped_for_an_early_action():
    doc_code.ui_params(None, BEAT, {"widgets": [{"kind": "button", "text": "Code", "press_at": "Click Code"}]}, DOC)


def test_a_panel_too_tall_stops():
    assert "split it into two beats" in stop({"widgets": [{"kind": "input", "text": "x", "type_at": 1, "send_at": 2}] * 5})


def test_five_short_parts_fit():
    doc_code.ui_params(None, BEAT, {"widgets": [{"kind": "button", "text": "x"}] * 4 + [{"kind": "check", "text": "x", "check_at": 2}]}, DOC)


def test_a_menu_opening_into_the_subtitles_stops():
    W = [{"kind": "button", "text": "x"}] * 3 + [{"kind": "menu", "label": "a", "items": list("abcde"), "pick": "a", "pick_at": 2}]
    assert "opens down into the subtitles" in stop({"widgets": W})


def test_an_avatar_peek_on_the_beat_keeps_the_panel_at_its_own_size():
    doc = {"lang": "en", "avatar": {"moments": [{"beat": "B6", "show": "peek", "at": "Local", "face": "x"}]}}
    assert doc_code.ui_params(None, BEAT, {"widgets": B6}, doc)["_scale_max"] == 1.0


def test_the_new_time_keys_are_checked_against_the_narration():
    bad = doc_code.missing_triggers({"widgets": [{"kind": "button", "text": "x", "press_at": "Sign in"}]}, BEAT, "en")
    assert bad == ["press_at='Sign in'"]


# ---------- the page ----------

PAGE = """({ui: window.__ui, uit: window.__uit, sfx: window.__sfx,
  scale: gsap.getProperty(document.querySelector('.uis-panel'), 'scale'),
  panel: (() => { const r = document.querySelector('.uis-panel').getBoundingClientRect(); return [r.left, r.right]; })()})"""


def page(tmp_path, params, doc=DOC):
    o, _ = doc_code.build(tmp_path, doc, BEAT, {"scene": "ui_steps", "params": params}, "lecture-tech")
    return doc_code.page_value(o, PAGE)


def test_b6_actions_land_on_their_words_and_never_before_their_part(tmp_path):
    v = page(tmp_path, {"widgets": B6})
    t = {x["what"]: x["t"] for x in v["uit"]}
    show = [u["show"] for u in v["ui"]]
    assert t["0:open"] >= show[0] + .35                      # "Click" is the line's first word: the click waits for the menu
    assert t["0:pick"] >= max(WORD["click"], t["0:open"] + .35)
    assert t["1:pick0"] == pytest.approx(WORD["pick"], abs=.01)
    assert t["2:press"] == pytest.approx(WORD["open"], abs=.01)
    assert t["3:check"] == pytest.approx(TOKENS[-2][1], abs=.01)   # "empty"
    for k, s in enumerate(show):
        assert all(x["t"] >= s + .35 - 1e-6 for x in v["uit"] if x["what"].startswith(f"{k}:") and "show" not in x["what"])
    kinds = {(x["kind"], x["t"]) for x in v["sfx"]}
    assert ("click", t["2:press"]) in kinds and ("tick", t["3:check"]) in kinds


def test_b6_panel_sits_above_the_subtitles_and_inside_the_frame(tmp_path):
    v = page(tmp_path, {"widgets": B6})
    assert v["scale"] > 1                                     # four parts: enlarged
    assert max(u["bottom"] for u in v["ui"]) <= 860
    assert min(u["top"] for u in v["ui"]) >= 150
    assert 100 <= v["panel"][0] and v["panel"][1] <= 1702 + 1   # clear of the lower-right badge (x from 1726)


def test_a_short_panel_grows_to_the_cap(tmp_path):
    v = page(tmp_path, {"widgets": [{"kind": "toggle", "options": ["Auto", "Manual"], "picks": [{"pick": "Manual", "at": "pick Local"}]}]})
    assert v["scale"] == pytest.approx(1.35)
    assert v["panel"][1] <= 1702 + 1


def test_a_peek_beat_keeps_the_panel_out_of_the_side_strips(tmp_path):
    doc = {"lang": "en", "avatar": {"moments": [{"beat": "B6", "show": "peek", "at": "Local", "face": "x"}]}}
    v = page(tmp_path, {"widgets": B6[1:3]}, doc)
    assert v["scale"] == pytest.approx(1.0)
    assert v["panel"][0] >= 400 and v["panel"][1] <= 1920 - 400


def test_input_sends_after_it_finishes_typing(tmp_path):
    text = "Clone the repo into this folder and follow the install guide to set everything up for me."
    v = page(tmp_path, {"widgets": [{"kind": "input", "text": text, "type_at": "Click Code", "send_at": "the top"}]})
    t = {x["what"]: x["t"] for x in v["uit"]}
    assert t["0:send"] >= t["0:type"] + .6 + .2 - 1e-6         # typing takes at least 0.6 s, the send waits 0.2 s more
