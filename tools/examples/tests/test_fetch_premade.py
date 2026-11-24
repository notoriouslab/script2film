"""fetch_premade.py: a release zip is fetched only when its SHA-256 matches the repository's, never past its size, and
never unpacked outside premade/; a second run with the same hash does nothing."""
import functools
import hashlib
import http.server
import json
import sys
import threading
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fetch_premade as F  # noqa: E402


@pytest.fixture
def served(tmp_path):
    """A local web server over tmp_path/www; yields (folder, base url)."""
    www = tmp_path / "www"
    www.mkdir()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(www))
    handler.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield www, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def make_zip(path, members):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)
    return path


def project(tmp_path, url, zpath, **over):
    P = tmp_path / "proj"
    P.mkdir(exist_ok=True)
    meta = {"url": url, "sha256": hashlib.sha256(zpath.read_bytes()).hexdigest(), "bytes": zpath.stat().st_size, **over}
    (P / "premade.json").write_text(json.dumps(meta))
    return P


def test_good_zip_is_unpacked_and_a_second_run_skips(served, tmp_path, capsys):
    www, base = served
    z = make_zip(www / "p.zip", {"tts/voice.wav": b"RIFF", "tts/lines.json": b"[]"})
    P = project(tmp_path, f"{base}/p.zip", z)
    F.fetch(P)
    assert (P / "premade/tts/voice.wav").read_bytes() == b"RIFF"
    z.unlink()                                                   # the server no longer has it: a second run must not ask
    F.fetch(P)
    assert "already in place" in capsys.readouterr().out


def test_wrong_hash_is_refused_and_nothing_written(served, tmp_path):
    www, base = served
    z = make_zip(www / "p.zip", {"a.txt": b"x"})
    P = project(tmp_path, f"{base}/p.zip", z, sha256="0" * 64)
    with pytest.raises(SystemExit, match="SHA-256 does not match"):
        F.fetch(P)
    assert not (P / "premade").exists()


def test_a_file_bigger_than_announced_is_refused(served, tmp_path):
    www, base = served
    z = make_zip(www / "p.zip", {"a.txt": b"x" * 5000})
    P = project(tmp_path, f"{base}/p.zip", z, bytes=100)
    with pytest.raises(SystemExit, match="premade"):
        F.fetch(P)
    assert not (P / "premade").exists()


def test_a_member_outside_premade_is_refused(served, tmp_path):
    www, base = served
    z = make_zip(www / "p.zip", {"../evil.txt": b"x"})
    P = project(tmp_path, f"{base}/p.zip", z)
    with pytest.raises(SystemExit, match="outside premade"):
        F.fetch(P)
    assert not (tmp_path / "evil.txt").exists() and not (P / "evil.txt").exists()


def test_failure_names_the_release_page(tmp_path):
    P = tmp_path / "proj"
    P.mkdir()
    (P / "premade.json").write_text(json.dumps({"url": "http://127.0.0.1:9/x/releases/download/t1/p.zip", "sha256": "a" * 64,
                                                "bytes": 10}))
    with pytest.raises(SystemExit) as e:
        F.fetch(P)
    assert "http://127.0.0.1:9/x/releases/tag/t1" in str(e.value)
    assert F.release_page("https://github.com/o/r/releases/download/v1/a.zip") == "https://github.com/o/r/releases/tag/v1"
