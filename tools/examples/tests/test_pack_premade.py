"""pack_premade.py: packs exactly the files the project needs, the same bytes every time, and its zip round-trips
through fetch_premade's unpack."""
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fetch_premade as F  # noqa: E402
import pack_premade as P  # noqa: E402


def write(path, data=b"x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())


def narrated(tmp_path, host=True):
    p = tmp_path / "tpl" / "zh"
    write(p / "doc.json", "{}")
    write(p / "tts" / "voice.wav", b"wav")
    write(p / "tts" / "lines.json", "[]")
    write(p / "tts" / "asr_cache.json", "{}")   # made by the run, not packed
    if host:
        write(p / "host" / "parts.json", json.dumps([{"k": 1}, {"k": 2}]))
        write(p / "host" / "parts" / "part1.mp4")
        write(p / "host" / "parts" / "part2.mp4")
        write(p / "host" / "parts" / "part1.mp3")   # the upload audio, not packed
    return p


def drama(tmp_path):
    p = tmp_path / "king" / "en"
    cut = {"music": {"file": "music.wav", "db": -31},
           "shots": [{"id": "S0", "card": "x", "dur": 2}, {"id": "S1", "src": "clips/shot1.mp4"},
                     {"id": "S2", "src": "clips/shot2.mp4", "pics": [{"src": "clips/shot2.mp4"}, {"src": "clips/r.mp4"}]}]}
    write(p / "cut.json", json.dumps(cut))
    for f in ("clips/shot1.mp4", "clips/shot2.mp4", "clips/r.mp4", "clips/collect.json", "music.wav"):
        write(p / f)
    return p


def test_narrated_project_packs_voice_and_listed_host_parts_only(tmp_path):
    assert P.members(narrated(tmp_path)) == ["host/parts.json", "host/parts/part1.mp4", "host/parts/part2.mp4",
                                             "tts/lines.json", "tts/voice.wav"]
    assert P.members(narrated(tmp_path / "b", host=False)) == ["tts/lines.json", "tts/voice.wav"]


def test_drama_packs_every_clip_the_timeline_uses_and_the_music(tmp_path):
    assert P.members(drama(tmp_path)) == ["clips/r.mp4", "clips/shot1.mp4", "clips/shot2.mp4", "music.wav"]


def test_missing_file_is_named(tmp_path):
    p = drama(tmp_path)
    (p / "clips" / "r.mp4").unlink()
    with pytest.raises(FileNotFoundError, match="r.mp4"):
        P.members(p)


def test_path_outside_the_project_is_refused(tmp_path):
    p = drama(tmp_path)
    write(p / "cut.json", json.dumps({"shots": [{"id": "S1", "src": "../other.mp4"}]}))
    with pytest.raises(ValueError):
        P.members(p)


def test_same_files_same_bytes_and_premade_json(tmp_path):
    p = drama(tmp_path)
    P.main([str(p), "--out", str(tmp_path / "out1")])
    meta1 = json.loads((p / "premade.json").read_text())
    P.main([str(p), "--out", str(tmp_path / "out2")])
    meta2 = json.loads((p / "premade.json").read_text())
    assert meta1 == meta2
    assert meta1["url"] == "https://github.com/notoriouslab/script2film/releases/download/v1.2.0/king-en.zip"
    assert meta1["bytes"] == (tmp_path / "out1" / "king-en.zip").stat().st_size


def test_zip_round_trips_through_fetch_unpack(tmp_path):
    p = narrated(tmp_path)
    z = P.pack(p, tmp_path / "t.zip")
    F.unpack(z, tmp_path / "premade")
    assert (tmp_path / "premade" / "host" / "parts" / "part2.mp4").read_bytes() == b"x"
    assert sorted(zipfile.ZipFile(z).namelist()) == P.members(p)
