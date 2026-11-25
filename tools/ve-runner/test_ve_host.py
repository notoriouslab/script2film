"""ve_host.py: which parts are sent, the language stop, the prompt, and the check on a downloaded take."""
import json
import subprocess

import pytest

import ve_host as vh


def tone(path, seconds, video=False):
    ins = ["-f", "lavfi", "-i", f"sine=f=440:d={seconds}"]
    if video:
        ins = ["-f", "lavfi", "-i", f"color=c=gray:s=320x180:r=25:d={seconds}"] + ins
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, *(["-shortest"] if video else []), str(path)], check=True)
    return path


def project(tmp, lengths):
    (tmp / "host/parts").mkdir(parents=True)
    parts, t = [], 0.0
    for k, d in enumerate(lengths, 1):
        tone(tmp / f"host/parts/part{k}.mp3", d)
        parts.append({"k": k, "start": t, "end": t + d, "tail": 0.0})
        t += d
    (tmp / "host/parts.json").write_text(json.dumps(parts))
    return tmp


@pytest.mark.parametrize("doc, any_lang, stops", [
    ({"lang": "en"}, False, False),
    ({"lang": "en-US"}, False, False),
    ({"lang": "zh"}, False, True),
    ({"lang": "zh-Hant"}, False, True),
    ({}, False, True),                      # no lang: doc_common reads it as Chinese
    ({"lang": "zh"}, True, False),
])
def test_language_stop(doc, any_lang, stops):
    msg = vh.lang_stop(doc, any_lang)
    assert (msg is not None) == stops
    if stops:
        assert "tp_host.py" in msg and "--any-lang" in msg


def test_full_screen_stop():
    pip_only = {"beats": [{"id": "B1", "source": "code"}], "pip": {"clip": "host/tp_host.mp4"}}
    assert vh.full_screen_stop(pip_only, False) is None
    big = {"beats": [{"id": "B1", "source": "code"},
                     {"id": "B7", "source": "clip", "clip": "host/tp_host.mp4", "clip_sync": True}]}
    msg = vh.full_screen_stop(big, False)
    assert "B7" in msg and "tp_host.py" in msg and "--any-size" in msg
    assert vh.full_screen_stop(big, True) is None
    footage = {"beats": [{"id": "B2", "source": "clip", "clip": "clips/street.mp4", "clip_sync": True}]}
    assert vh.full_screen_stop(footage, False) is None       # a synced clip that is not the host


def test_prompt_keeps_the_rewrite_safe_wording():
    p = vh.prompt_for("A man in a grey blazer.")
    assert p.startswith("A man in a grey blazer talks to the camera")
    assert "No text, no captions, no subtitles." in p
    assert vh.prompt_for(None).startswith(vh.DEFAULT_WHO)
    assert ("auto_enhance_prompt", False) in vh.BOXES      # on, the hands froze for the whole clip


def test_wanted_parts(tmp_path):
    P = project(tmp_path, [3, 2])
    got = vh.wanted_parts(P, None)
    assert [p["k"] for p in got] == [1, 2] and abs(got[0]["seconds"] - 3) < 0.1
    assert [p["k"] for p in vh.wanted_parts(P, [2])] == [2]
    with pytest.raises(SystemExit, match="not in"):
        vh.wanted_parts(P, [5])


def test_wanted_parts_stops_on_a_missing_split_or_file(tmp_path):
    with pytest.raises(SystemExit, match="--max 290"):
        vh.wanted_parts(tmp_path, None)
    P = project(tmp_path, [2])
    (P / "host/parts/part1.mp3").unlink()
    with pytest.raises(SystemExit, match="split again"):
        vh.wanted_parts(P, None)


def test_wanted_parts_stops_over_the_ve_cap(tmp_path, monkeypatch):
    P = project(tmp_path, [2])
    monkeypatch.setattr(vh, "VE_MAX", 1.5)
    with pytest.raises(SystemExit, match="at most 1.5s"):
        vh.wanted_parts(P, None)


def test_check_take(tmp_path):
    good = tone(tmp_path / "good.mp4", 4, video=True)
    assert vh.check_take(good, 4.0, 0.3) is None
    assert "more than 0.3s apart" in vh.check_take(good, 5.0, 0.3)
    silent = tmp_path / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=gray:s=320x180:r=25:d=4", str(silent)], check=True)
    assert "needs video and audio" in vh.check_take(silent, 4.0, 0.3)
    assert "needs video and audio" in vh.check_take(tmp_path / "missing.mp4", 4.0, 0.3)


def test_place_keeps_the_older_take(tmp_path):
    dst = tmp_path / "part1.mp4"
    dst.write_text("old")
    src = tmp_path / "new.mp4"
    src.write_text("new")
    vh.place(src, dst)
    assert dst.read_text() == "new" and (tmp_path / "part1.bak.mp4").read_text() == "old" and not src.exists()
