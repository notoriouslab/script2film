"""pytest for doc_avatar (comic avatar host): pack / check, geometry, timing."""
import json
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

DOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOC / "scripts"))
import doc_avatar as A  # noqa: E402


def fake_sheet(path, cols=2, rows=1, pw=500, ph=600):
    """White sheet with black-framed panels, a grey blob in each."""
    W, H = cols * (pw + 40) + 40, rows * (ph + 40) + 40
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    for r in range(rows):
        for c in range(cols):
            x, y = 40 + c * (pw + 40), 40 + r * (ph + 40)
            d.rectangle([x, y, x + pw, y + ph], outline="black", width=8)
            d.ellipse([x + 150, y + 150, x + 350, y + 350], fill=(150, 150, 150))
    im.save(path)


def test_pack_cuts_panels(tmp_path):
    fake_sheet(tmp_path / "s.png")
    faces = A.pack_sheet(tmp_path / "s.png", "2x1", ["a", "b"], tmp_path / "p")
    assert list(faces) == ["a", "b"]
    assert faces["a"] == {"file": "01-a.png", "cx": 0.5, "cy": 0.42}
    for f in ("01-a.png", "02-b.png"):
        w, h = Image.open(tmp_path / "p" / f).size
        assert 462 <= w <= 472 and 562 <= h <= 572          # 501 - 2 x 8 frame - 2 x 9 inset ≈ 467
        px = Image.open(tmp_path / "p" / f).convert("L")
        assert min(px.getpixel((0, y)) for y in range(0, h, 10)) > 200   # no frame line left at the edge
    assert json.loads((tmp_path / "p/faces.json").read_text()) == faces
    assert (tmp_path / "p/faces_check.png").is_file()


def test_pack_names_must_match_grid(tmp_path):
    fake_sheet(tmp_path / "s.png")
    with pytest.raises(SystemExit):
        A.pack_sheet(tmp_path / "s.png", "2x1", ["a"], tmp_path / "p")


def test_pack_check_reports(tmp_path):
    fake_sheet(tmp_path / "s.png")
    A.pack_sheet(tmp_path / "s.png", "2x1", ["a", "b"], tmp_path / "p")
    assert A.check_pack(tmp_path / "p") == []
    (tmp_path / "p/02-b.png").unlink()
    fj = json.loads((tmp_path / "p/faces.json").read_text())
    fj["a"]["cx"] = 1.4
    (tmp_path / "p/faces.json").write_text(json.dumps(fj))
    bad = A.check_pack(tmp_path / "p")
    assert any("b: file" in x for x in bad) and any("a: cx / cy" in x for x in bad)


def test_pack_check_cli_exits_nonzero(tmp_path, monkeypatch):
    (tmp_path / "p").mkdir()
    monkeypatch.setattr(sys, "argv", ["doc_avatar.py", "check", str(tmp_path / "p")])
    with pytest.raises(SystemExit) as e:
        A.main()
    assert e.value.code not in (0, None)


def test_pack_check_width(tmp_path):
    (tmp_path / "p").mkdir()
    Image.new("RGB", (300, 400), "white").save(tmp_path / "p/01-a.png")
    (tmp_path / "p/faces.json").write_text(json.dumps({"a": {"file": "01-a.png", "cx": 0.5, "cy": 0.4}}))
    assert any("needs at least 400" in x for x in A.check_pack(tmp_path / "p"))


# ---------- geometry ----------

FACE = {"w": 491, "h": 586, "cx": 0.5, "cy": 0.4}


def test_geometry_lower_corner_peek_stays_off_the_subtitles():
    for pos in ("lower-left", "lower-right"):
        g = A.peek_geometry(FACE, pos)
        assert g["w"] == 367
        inner = g["x"] + g["w"] if pos == "lower-left" else 1920 - g["x"]
        assert inner <= 400


def test_geometry_lower_peek_depth_follows_the_face():
    for cy, share in ((0.62, 0.96), (0.40, 0.8)):
        g = A.peek_geometry({**FACE, "cy": cy}, "lower-right")
        assert abs((1080 - g["y"]) / g["h"] - share) < 0.01


def test_geometry_side_peek_depth_follows_the_face():
    g = A.peek_geometry({**FACE, "cx": 0.45}, "right")
    assert abs((1920 - g["x"]) / g["w"] - 0.69) < 0.01
    g = A.peek_geometry({**FACE, "cx": 0.45}, "left")
    assert abs((g["x"] + g["w"]) / g["w"] - 0.79) < 0.01
    assert g["dx"] < 0 < A.peek_geometry(FACE, "right")["dx"]


def test_geometry_panel_above_the_mist():
    for pos in ("left", "center", "right"):
        g = A.panel_geometry(FACE, pos)
        assert g["h"] == 691 and g["y"] == 96 and g["y"] + g["h"] <= A.MIST_TOP
        assert 0 <= g["x"] and g["x"] + g["w"] <= 1920


def test_geometry_badge_inside_corner_band():
    for pos in A.BADGE_POS:
        g = A.badge_geometry(pos)
        inner = g["x"] + g["w"] if pos.endswith("left") else 1920 - g["x"]
        assert inner <= 400 and g["y"] + g["h"] <= 1080


# ---------- resolve ----------

FACES = {"shock": FACE, "think": FACE, "wave": FACE}


def beats():
    return [{"id": "B1", "start": 0.0, "duration": 5.0, "tokens": [["hello", 0.0], ["world", 1.0]]},
            {"id": "B2", "start": 5.0, "duration": 5.0, "tokens": [["wait", 0.5], ["what", 2.0]]},
            {"id": "B3", "start": 10.0, "duration": 5.0, "tokens": [["bye", 1.0]]}]


def phrase_time(doc, b, phrase):
    return next((t for w, t in b["tokens"] if w == phrase), None)


def test_resolve_phrase_missing_stops_with_beat_and_phrase():
    doc = {"avatar": {"moments": [{"beat": "B2", "at": "nope", "face": "think", "show": "peek", "pos": "right"},
                                  {"beat": "B1", "at": "hello", "face": "nobody", "show": "panel"}]}}
    with pytest.raises(SystemExit) as e:
        A.resolve(doc, beats(), FACES, phrase_time)
    msg = str(e.value)
    assert 'B2 "nope"' in msg and "nobody" in msg      # both problems in one stop


def test_resolve_bad_pos_and_show():
    doc = {"avatar": {"moments": [{"beat": "B1", "at": "hello", "face": "shock", "show": "peek", "pos": "lower-center"},
                                  {"beat": "B1", "at": "world", "face": "shock", "show": "pop"}]}}
    with pytest.raises(SystemExit) as e:
        A.resolve(doc, beats(), FACES, phrase_time)
    assert "lower-center" in str(e.value) and "'pop'" in str(e.value)


def test_resolve_sorted_and_badge_hides_during_panel_and_peek():
    doc = {"avatar": {"badge": {"pos": "lower-right"},
                      "moments": [{"beat": "B3", "at": "bye", "face": "wave", "show": "peek", "pos": "lower-left"},
                                  {"beat": "B1", "at": "hello", "face": "shock", "show": "panel"},
                                  {"beat": "B2", "at": "what", "face": "think", "show": "badge"}]}}
    ev = A.resolve(doc, beats(), FACES, phrase_time)
    ts = [e["t"] for e in ev]
    assert ts == sorted(ts)
    panel = next(e for e in ev if e["kind"] == "panel")
    assert panel["t"] == 0 and panel["end"] == pytest.approx(0.45 + 1.8 + 0.5)
    on = [e for e in ev if e["kind"] == "badge-on"]
    assert on[0]["t"] == panel["end"] and on[0]["face"] == "shock"      # badge starts when the panel docks
    peek = next(e for e in ev if e["kind"] == "peek")
    offs = [e for e in ev if e["kind"] == "badge-off"]
    assert [e["t"] for e in offs] == [peek["t"]]
    assert any(e["kind"] == "badge-on" and e["t"] == peek["end"] for e in ev)
    flip = next(e for e in ev if e["kind"] == "flip")
    assert flip["t"] == 7.0 and flip["face"] == "think"


def test_resolve_no_avatar():
    assert A.resolve({}, beats(), FACES, phrase_time) == []


# ---------- markup ----------

def events():
    doc = {"avatar": {"badge": {"pos": "lower-right"},
                      "moments": [{"beat": "B1", "at": "hello", "face": "shock", "show": "panel"},
                                  {"beat": "B2", "at": "what", "face": "think", "show": "badge"},
                                  {"beat": "B3", "at": "bye", "face": "wave", "show": "peek", "pos": "right"}]}}
    return A.resolve(doc, beats(), {k: {**v, "file": f"{k}.png"} for k, v in FACES.items()}, phrase_time)


def test_markup_every_event_time_is_a_position():
    ev = events()
    css, dom, js = A.avatar_markup(ev, {k: {**v, "file": f"{k}.png"} for k, v in FACES.items()})
    lines = js.splitlines()
    for e in ev:
        assert any(l.strip().endswith(f", {e['t']});") for l in lines), e
    panel = next(e for e in ev if e["kind"] == "panel")
    dock = [l for l in lines if "scale: 0.25" in l]       # the panel docks into the badge, not slides away
    assert len(dock) == 1 and dock[0].strip().endswith(f", {round(panel['end'] - A.PANEL_OUT, 3)});")
    assert js.count("main.") == len(lines)       # shell mode adds to the shell page's timeline


def test_markup_z_between_mist_and_subtitles():
    css, _, _ = A.avatar_markup(events(), {k: {**v, "file": f"{k}.png"} for k, v in FACES.items()})
    z = int(css.split("z-index:")[1].split(";")[0])
    assert 95 < z < 100


def test_markup_alpha_page_is_transparent():
    page = A.alpha_page(events(), {k: {**v, "file": f"{k}.png"} for k, v in FACES.items()}, 15.0)
    assert "body { margin: 0; background: transparent" in page
    assert 'data-composition-id="main"' in page and 'data-duration="15.0"' in page
    assert "url(avatar/shock.png)" in page and "http" not in page


# ---------- doc_cut ----------

def test_check_layers_avatar_and_host():
    import doc_cut
    beats_ = [{"id": "B1"}, {"id": "B2", "source": "clip", "clip": "host/tp_host.mp4"}]
    av = {"pack": "x", "moments": []}
    for doc, who in (({"beats": beats_[:1], "avatar": av, "pip": {"clip": "h.mp4", "beats": ["B1"]}}, "pip"),
                     ({"beats": beats_[:1], "avatar": av, "side": {"clip": "h.mp4", "beats": ["B1"]}}, "side"),
                     ({"beats": beats_, "avatar": av}, "B2")):
        with pytest.raises(SystemExit) as e:
            doc_cut.check_layers(doc)
        assert "avatar and a talking host" in str(e.value) and who in str(e.value)
    doc_cut.check_layers({"beats": beats_[:1], "avatar": av})          # avatar alone is fine
    doc_cut.check_layers({"beats": [{"id": "B3", "source": "clip", "clip": "broll/street.mp4"}], "avatar": av})   # not a host


def test_check_layers_avatar_only_film_gets_layers(tmp_path, monkeypatch):
    """A film whose only layer is the avatar still writes layers.json with the avatar lane (rendering faked)."""
    import doc_cut
    calls = []

    def fake_hf(cmd, d, *args, stdout=None):
        calls.append((cmd, Path(d), args))
        Path(args[args.index("-o") + 1]).write_bytes(b"mov")
        return type("R", (), {"returncode": 0})()
    monkeypatch.setattr(doc_cut, "hyperframes", fake_hf)
    pack = tmp_path / "pack"
    pack.mkdir()
    faces = {}
    for k in FACES:
        Image.new("RGB", (491, 586), "white").save(pack / f"{k}.png")
        faces[k] = {**FACE, "file": f"{k}.png"}
    doc = {"lang": "en", "beats": [], "avatar": {"moments": [{"beat": "B1", "at": "hello", "face": "shock", "show": "panel"}]}}
    ev = A.resolve(doc, beats(), faces, phrase_time)
    (tmp_path / "cut").mkdir()
    doc_cut.concat_layers(tmp_path, doc, beats(), "cut", "collage", {"second": None}, (ev, faces, pack), 15.5)
    assert calls == []                                              # no --avatar-lane: page and entry only, no render
    assert json.loads((tmp_path / "cut/layers.json").read_text())["avatar"]["clip"].endswith("avatar_lane/avatar.mov")
    assert 'data-duration="15.5"' in (tmp_path / "cut/avatar_lane/index.html").read_text()   # the film's length
    doc_cut.concat_layers(tmp_path, doc, beats(), "cut", "collage", {"second": None}, (ev, faces, pack), 15.5, True)
    L = json.loads((tmp_path / "cut/layers.json").read_text())
    assert L["avatar"]["start"] == 0 and L["avatar"]["clip"].endswith("avatar_lane/avatar.mov")
    page = (tmp_path / "cut/avatar_lane/index.html").read_text()
    assert "background: transparent" in page and (tmp_path / "cut/avatar_lane/avatar/shock.png").is_file()
    assert calls[0][0] == "render" and "--format" in calls[0][2] and "mov" in calls[0][2]
    # and main() reaches concat_layers for an avatar-only doc
    src = (DOC / "scripts/doc_cut.py").read_text()
    assert '"en", "zh", "avatar")' in src


def test_shell_draws_the_avatar(tmp_path):
    """The burned-in path: shell() puts the avatar's css, dom and timeline lines on the page and copies the pngs."""
    import doc_cut
    from test_cut_audio import synthetic_shell_input
    P, doc, bts, total, theme, hits = synthetic_shell_input(tmp_path / "p")
    pack = tmp_path / "pack"
    pack.mkdir()
    faces = {}
    for k in FACES:
        Image.new("RGB", (491, 586), "white").save(pack / f"{k}.png")
        faces[k] = {**FACE, "file": f"{k}.png"}
    ev = [{"t": 0.5, "kind": "peek", "face": "think", "pos": "right", "end": 2.55}]
    S = doc_cut.shell(P, doc, bts, total, theme, hits, doc_cut.subtitle_plan(doc, None), (ev, faces, pack))
    page = (S / "index.html").read_text(encoding="utf-8")
    assert 'id="av0"' in page and "z-index: 97" in page and 'main.fromTo("#av0"' in page
    assert page.index("main.fromTo") < page.index('window.__timelines["main"]')
    assert (S / "avatar/think.png").is_file()


# ---------- doc_lint ----------

def _m(beat, face, show, pos=None):
    return {"beat": beat, "at": "x", "face": face, "show": show, **({"pos": pos} if pos else {})}


def test_lint_too_many_panels():
    from doc_lint import avatar_mix
    doc = {"avatar": {"moments": [_m("B1", "shock", "panel"), _m("B2", "think", "panel"), _m("B3", "wave", "panel")]}}
    w = avatar_mix(doc)
    assert len(w) == 1 and "3 whole panels" in w[0]


def test_lint_same_edge_twice():
    from doc_lint import avatar_mix
    doc = {"avatar": {"moments": [_m("B1", "shock", "peek", "right"), _m("B2", "think", "peek", "right")]}}
    w = avatar_mix(doc)
    assert len(w) == 1 and "both peek from right" in w[0]


def test_lint_same_face_twice():
    from doc_lint import avatar_mix
    doc = {"avatar": {"moments": [_m("B1", "think", "peek", "left"), _m("B2", "think", "peek", "right")]}}
    w = avatar_mix(doc)
    assert len(w) == 1 and "both use think" in w[0]


def test_lint_reports_but_does_not_stop(capsys):
    """check() prints the avatar_mix lines and returns; an unknown moment beat is a lint failure."""
    import doc_lint
    beats_ = [{"id": "B1", "lines": [], "source": "code"}, {"id": "B2", "lines": [], "source": "code"}]
    doc = {"lang": "en", "lines": [], "beats": beats_,
           "avatar": {"moments": [_m("B1", "think", "peek", "left"), _m("B2", "think", "peek", "left")]}}
    doc_lint.check(doc, {"ids_exist": ["avatar.moments[].beat"]})
    out = capsys.readouterr().out
    assert "⚠ avatar_mix: B1 and B2 both peek from left" in out and "both use think" in out
    doc["avatar"]["moments"][1]["beat"] = "B9"
    assert any("B9 in avatar.moments[].beat" in x for x in doc_lint.lint(doc, {"ids_exist": ["avatar.moments[].beat"]}))
    assert doc_lint.avatar_mix({}) == []


def test_resolve_badge_waits_for_a_panel_it_would_cover():
    """badge.from inside the opening panel: the badge starts when the panel has left, not over it."""
    doc = {"avatar": {"badge": {"pos": "lower-right", "from": "B2"},     # B2 starts at 5.0, inside the panel (1.0-6.95)
                      "moments": [{"beat": "B1", "at": "world", "face": "shock", "show": "panel", "hold": 5}]}}
    ev = A.resolve(doc, beats(), FACES, phrase_time)
    panel = next(e for e in ev if e["kind"] == "panel")
    on = [e for e in ev if e["kind"] == "badge-on"]
    assert on[0]["t"] == panel["end"] and not [e for e in ev if e["kind"] == "badge-off"]


# ---------- talking mouth ----------

def _faces_pair(tmp_path, n=2):
    """A pack of n closed faces and a sheet of the same faces with a dark 'open mouth' blob; noisy backgrounds differ."""
    import numpy as np
    rng = np.random.default_rng(1)
    pack = tmp_path / "pack"
    pack.mkdir()
    faces, cells = {}, []
    for k in range(n):
        base = np.full((600, 500, 3), 235, np.uint8)
        base[100:400, 120:380] = (200 + 20 * k, 170, 150)          # the face, a different tone per face
        closed = base.copy()
        closed[330:338, 220:280] = 40                                 # closed mouth: a line
        opened = base.copy()
        opened[315:355, 225:275] = 30                                 # open mouth: a block
        noise = rng.integers(0, 40, (600, 500, 1), dtype=np.uint8)
        opened[:80] = np.clip(opened[:80].astype(int) - noise[:80], 0, 255)   # the redraw's background differs
        Image.fromarray(closed).save(pack / f"0{k + 1}-f{k}.png")
        faces[f"f{k}"] = {"file": f"0{k + 1}-f{k}.png", "cx": 0.5, "cy": 0.42}
        cells.append(opened)
    (pack / "faces.json").write_text(json.dumps(faces))
    W = n * 540 + 40
    sheet = Image.new("RGB", (W, 680), "white")
    d = ImageDraw.Draw(sheet)
    for k, c in enumerate(cells):
        x = 40 + k * 540
        sheet.paste(Image.fromarray(c), (x + 17, 57))
        d.rectangle([x, 40, x + 534, 674], outline="black", width=8)
    sheet.save(tmp_path / "open.png")
    return pack, tmp_path / "open.png"


def test_mouth_found_and_only_the_mouth_changes(tmp_path):
    import numpy as np
    pack, sheet = _faces_pair(tmp_path)
    faces = A.open_sheet(pack, sheet, "2x1")
    for f in faces.values():
        assert abs(f["mx"] - 0.5) < 0.03 and abs(f["my"] - 335 / 600) < 0.03
        c = np.asarray(Image.open(pack / f["file"]).convert("RGB"), int)
        o = np.asarray(Image.open(pack / f["open"]).convert("RGB"), int)
        assert c.shape == o.shape
        yy, xx = np.mgrid[:c.shape[0], :c.shape[1]]
        w = c.shape[1]
        far = ((xx - f["mx"] * w) / (A.MOUTH_RX * w + 30)) ** 2 + ((yy - f["my"] * c.shape[0]) / (A.MOUTH_RY * w + 30)) ** 2 > 1
        assert (np.abs(c - o)[far] == 0).all()                          # outside the feathered ellipse: untouched
        assert np.abs(c - o).max() > 100                                # the mouth did change
    assert A.check_pack(pack) == []


def test_mouth_sheet_in_the_wrong_order_stops(tmp_path):
    pack, sheet = _faces_pair(tmp_path)
    im = Image.open(sheet)
    a, b = im.crop((40, 40, 575, 675)), im.crop((580, 40, 1115, 675))
    im.paste(b, (40, 40)); im.paste(a, (580, 40)); im.save(sheet)   # swap the two cells
    fj = json.loads((pack / "faces.json").read_text())
    # make the faces clearly different so a swap is visible
    for k, name in enumerate(fj):
        p = pack / fj[name]["file"]
        x = Image.open(p)
        ImageDraw.Draw(x).rectangle([0, 0, 499, 599] if k else [0, 0, 10, 10], outline="black", width=60 if k else 1)
        x.save(p)
    with pytest.raises(SystemExit) as e:
        A.open_sheet(pack, sheet, "2x1")
    assert "cell" in str(e.value)


def test_mouth_check_reports(tmp_path):
    pack, sheet = _faces_pair(tmp_path)
    A.open_sheet(pack, sheet, "2x1")
    fj = json.loads((pack / "faces.json").read_text())
    (pack / fj["f0"]["open"]).unlink()
    Image.new("RGB", (10, 10)).save(pack / fj["f1"]["open"])
    bad = A.check_pack(pack)
    assert any("f0: open" in x and "missing" in x for x in bad) and any("f1: open is (10, 10)" in x for x in bad)


def test_flaps_silence_and_long_vowel():
    import numpy as np
    assert A.flaps(np.zeros(90)) == []
    env = np.r_[np.zeros(15), np.ones(60), np.zeros(15)]                # 2 s of steady loud voice
    fl = A.flaps(env)
    assert fl and all(round((z - a) * 30) <= A.MAX_OPEN for a, z in fl)
    assert all(round((b[0] - a[1]) * 30) >= A.MIN_RUN for a, b in zip(fl, fl[1:]))
    ts = [t for a, z in fl for t in (a, z)]
    assert ts == sorted(ts)


def test_flaps_hysteresis_ignores_jitter():
    """Once open, a voice dipping between the two thresholds keeps the mouth open (until the long-vowel close), instead
    of snapping shut as soon as it falls under the open threshold."""
    import numpy as np
    env = np.r_[np.zeros(10), np.ones(2), np.tile([0.30, 0.28], 5), np.zeros(10)]   # P90 = 1: open 0.35, close 0.25
    first = A.flaps(env)[0]
    assert round((first[1] - first[0]) * 30) == A.MAX_OPEN


def _talk_faces():
    return {"shock": {**FACE, "file": "shock.png", "open": "shock_open.png", "mx": .5, "my": .6},
            "think": {**FACE, "file": "think.png"}, "wave": {**FACE, "file": "wave.png", "open": "wave_open.png", "mx": .5, "my": .6}}


def test_markup_mouth_layers_and_flaps():
    faces = _talk_faces()
    ev = [{"t": 0.5, "kind": "peek", "face": "shock", "pos": "right", "end": 2.55},
          {"t": 3.0, "kind": "peek", "face": "think", "pos": "left", "end": 5.05},
          {"t": 5.5, "kind": "badge-on", "face": "wave", "pos": "lower-right", "d": 170},
          {"t": 7.0, "kind": "flip", "face": "think"}, {"t": 9.0, "kind": "flip", "face": "shock"}]
    fl = [(0.6, 0.8), (1.0, 1.2)]
    css, dom, js = A.avatar_markup(ev, faces, mouth=fl)
    av0 = dom.split('id="av0"')[1].split('id="av1"')[0]
    av1 = dom.split('id="av1"')[1].split('id="avb"')[0]
    assert 'class="av-mouth"' in av0 and "shock_open.png" in av0 and "av-mouth" not in av1   # think has no open panel
    assert 'id="avbm"' in dom.split('id="avb"')[1]
    for a, z in fl:
        assert f'main.set(".av-mouth", {{opacity: 1}}, {a});' in js and f'main.set(".av-mouth", {{opacity: 0}}, {z});' in js
    assert 'main.set("#avbm", {"display": "none"}, 7.15);' in js
    assert 'main.set("#avbm", {"backgroundImage": "url(avatar/shock_open.png)", "display": "block"}, 9.15);' in js
    css0, dom0, js0 = A.avatar_markup(ev, faces)                                               # no flaps: no mouth at all
    assert "av-mouth" not in dom0 and ".av-mouth" not in js0


def test_shell_and_lane_talk(tmp_path, monkeypatch):
    import doc_cut
    from test_cut_audio import synthetic_shell_input
    P, doc, bts, total, theme, hits = synthetic_shell_input(tmp_path / "p")
    pack = tmp_path / "pack"
    pack.mkdir()
    faces = _talk_faces()
    for f in faces.values():
        for k in ("file", "open"):
            if f.get(k):
                Image.new("RGB", (491, 586), "white").save(pack / f[k])
    ev = [{"t": 0.5, "kind": "peek", "face": "shock", "pos": "right", "end": 2.55}]
    fl = [(0.6, 0.8)]
    S = doc_cut.shell(P, doc, bts, total, theme, hits, doc_cut.subtitle_plan(doc, None), (ev, faces, pack, fl))
    page = (S / "index.html").read_text(encoding="utf-8")
    assert 'main.set(".av-mouth", {opacity: 1}, 0.6);' in page and (S / "avatar/shock_open.png").is_file()
    (tmp_path / "cut").mkdir()
    doc_cut.concat_layers(tmp_path, {"lang": "en", "beats": []}, beats(), "cut", "collage", {"second": None},
                          (ev, faces, pack, fl), 15.0)
    lane = (tmp_path / "cut/avatar_lane/index.html").read_text()
    assert 'main.set(".av-mouth", {opacity: 1}, 0.6);' in lane and (tmp_path / "cut/avatar_lane/avatar/shock_open.png").is_file()


def test_badge_crop_keeps_the_mouth():
    """A face looking down (mouth far below the face centre) is framed lower in the badge than one without a mouth."""
    plain = {**FACE, "file": "a.png", "cy": 0.36}
    talking = {**plain, "my": 0.53}
    y = lambda f: float(A._crop(f, 170)["backgroundPosition"].split()[1][:-2])
    assert y(talking) < y(plain)                                   # the picture moves up: the circle shows lower down
    H = 170 * 1.6 * FACE["h"] / FACE["w"]
    assert abs((85 - y(talking)) / H - (0.36 + 0.53) / 2) < 1e-3   # the circle's centre sits halfway to the mouth


# ---------- shut: a closed frame for a face drawn mid-laugh ----------

SKIN = (254, 215, 194)


def laughing(path, line_to_jaw=False):
    """A 500 x 600 skin panel with a big open mouth (black outline, red inside, white teeth) under the face centre;
    line_to_jaw joins the mouth to the bottom edge with a black stroke (a jaw or a hand that touches it)."""
    im = Image.new("RGB", (500, 600), SKIN)
    d = ImageDraw.Draw(im)
    d.ellipse([200, 320, 300, 390], fill=(200, 80, 90), outline="black", width=5)
    d.rectangle([215, 326, 285, 340], fill="white")
    if line_to_jaw:
        d.line([250, 390, 250, 600], fill="black", width=6)
    im.save(path)
    return im


def mouth_height(im):
    import numpy as np
    a = np.asarray(im.convert("RGB"), float)
    rows = np.where((np.sqrt(((a - SKIN) ** 2).sum(2)) > A.SHUT_SKIN)[:, 150:350].any(1))[0]
    return rows.max() - rows.min()


def test_shut_squeezes_the_mouth_and_leaves_skin_below(tmp_path):
    im = laughing(tmp_path / "f.png")
    out = A.shut_face(im, .5, 355 / 600)
    assert mouth_height(out) <= mouth_height(im) * A.SHUT_KEEP + 6
    assert out.getpixel((250, 385)) == SKIN                  # where the lower lip was: skin now
    assert out.getpixel((60, 60)) == SKIN and out.size == im.size


def test_shut_refuses_a_mouth_joined_to_other_lines(tmp_path):
    assert A.shut_face(laughing(tmp_path / "f.png", line_to_jaw=True), .5, 355 / 600) is None


def test_shut_faces_writes_the_frame_and_check_follows_it(tmp_path):
    p = tmp_path / "p"
    p.mkdir()
    laughing(p / "01-cheer.png")
    (p / "faces.json").write_text(json.dumps({"cheer": {"file": "01-cheer.png", "cx": .5, "cy": .4, "mx": .5, "my": 355 / 600}}))
    faces = A.shut_faces(p, ["cheer"])
    assert faces["cheer"]["shut"] == "01-cheer_shut.png" and (p / "01-cheer_shut.png").is_file()
    assert A.check_pack(p) == []
    (p / "01-cheer_shut.png").unlink()
    assert any("shut" in b for b in A.check_pack(p))


def test_shut_faces_stops_before_writing_anything(tmp_path):
    p = tmp_path / "p"
    p.mkdir()
    laughing(p / "01-cheer.png")
    laughing(p / "02-cool.png", line_to_jaw=True)
    (p / "faces.json").write_text(json.dumps({k: {"file": f, "cx": .5, "cy": .4, "mx": .5, "my": 355 / 600}
                                              for k, f in (("cheer", "01-cheer.png"), ("cool", "02-cool.png"))}))
    with pytest.raises(SystemExit) as e:
        A.shut_faces(p, ["cheer", "cool"])
    assert "cool" in str(e.value) and "cheer" not in str(e.value)
    assert not (p / "01-cheer_shut.png").exists()


def test_talking_rests_on_the_shut_frame_and_copies_it(tmp_path):
    faces = {"cheer": {"file": "a.png", "open": "a_open.png", "shut": "a_shut.png"}, "think": {"file": "b.png"}}
    t = A.talking(faces)
    assert t["cheer"]["file"] == "a_shut.png" and t["think"]["file"] == "b.png" and faces["cheer"]["file"] == "a.png"
    for n in ("a.png", "a_open.png", "a_shut.png", "b.png"):
        Image.new("RGB", (4, 4)).save(tmp_path / n)
    A.copy_pack(tmp_path, faces, tmp_path / "page")
    assert (tmp_path / "page/avatar/a_shut.png").is_file()


@pytest.mark.parametrize("keep", [0.0, -1, 1.5])
def test_shut_keep_outside_its_range_stops(tmp_path, keep):
    with pytest.raises(SystemExit, match="--keep must be between"):
        A.shut_faces(tmp_path, ["cheer"], keep)
