"""--layers 的漫畫頭貼軌：開幾條疊加軌、要匯入哪些素材、軌的上下順序。"""
import plan2concat_mcp as m


def test_avatar_only_opens_the_layer_lanes_and_imports_the_mov():
    n, need = m.layer_need({"avatar": {"clip": "/x/avatar_lane/avatar.mov", "start": 0}}, set())
    assert n == 4 and need == ["/x/avatar_lane/avatar.mov"]


def test_side_and_pills_keep_their_lanes_and_order():
    n, need = m.layer_need({"side": [{"clip": "/h.mp4"}], "pills": [{}]}, {"/h.mp4"})
    assert n == 4 and need == []            # one more (empty) lane than before: the avatar lane
    lanes = list(m.LAYER_LANES)
    assert lanes[0] == "avatar"             # top of the layers: over pills, under the subtitles
    assert lanes.index("pills") < lanes.index("side") < lanes.index("plate")


def test_no_layers():
    assert m.layer_need({}, set()) == (0, [])


def test_add_avatar_places_the_mov_at_zero():
    calls = []

    class C:
        def tool(self, name, **kw):
            calls.append((name, kw))
    m.add_avatar(C(), "/p", {"avatar": {"clip": "/a.mov", "start": 0}}, {"avatar": "T9"}, {"/a.mov": "M1"})
    assert calls == [("edit_apply", {"path": "/p", "command": {"op": "addClip", "mediaId": "M1", "trackId": "T9", "start": 0}})]
    calls.clear()
    m.add_avatar(C(), "/p", {}, {"avatar": "T9"}, {})
    assert calls == []


def test_missing_lane_stops_with_the_command(tmp_path, monkeypatch):
    import json, sys
    import pytest
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps({"media": [], "tracks": [], "width": 1920, "height": 1080, "fps": 30, "total": 1}))
    lay = tmp_path / "layers.json"
    lay.write_text(json.dumps({"avatar": {"clip": str(tmp_path / "avatar_lane/avatar.mov"), "start": 0}}))
    monkeypatch.setattr(sys, "argv", ["plan2concat_mcp.py", str(plan), str(tmp_path), "t", "--font", "F=/f.ttf", "--layers", str(lay)])
    with pytest.raises(SystemExit) as e:
        m.main()
    assert "--avatar-lane" in str(e.value)
