"""GSAP 本機載入、失敗時印原因。"""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parents[1]
REPO = DOC.parents[2]
sys.path.insert(0, str(DOC / "scripts"))
import doc_common  # noqa: E402

LOCAL = '<script src="gsap.min.js"></script>'


def test_pages_load_gsap_from_their_own_folder():
    for f in ("lib/template.html", "scripts/doc_cut.py", "tests/fixtures/shell_no_bgm.html"):
        assert (DOC / f).read_text(encoding="utf-8").count(LOCAL) == 1, f


def test_no_cdn_left_in_code():
    if not (REPO / ".git").exists():
        pytest.skip("不是 git 倉庫")
    r = subprocess.run(["git", "grep", "-n", "-I", "-e", "cdnjs", "--", "skills", "tools", ":!*test_gsap_local.py"],
                       cwd=REPO, capture_output=True, text=True)
    assert r.stdout == "", r.stdout


def test_gsap_is_copied_to_all_three_page_folders():
    code = (DOC / "scripts/doc_code.py").read_text(encoding="utf-8")
    cut = (DOC / "scripts/doc_cut.py").read_text(encoding="utf-8")
    assert 'shutil.copy(gsap_file(), out / "gsap.min.js")' in code            # code_<theme>/<beat>/
    assert 'shutil.copy(gsap_file(), S / "gsap.min.js")' in cut               # shell_<theme>/
    assert '"copy": ["index.html", "gsap.min.js", ' in cut                    # → cut_<theme>/ (tools/assemble copy_shell)


def test_gsap_file_points_into_node_modules_and_says_npm_ci_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(doc_common, "REPO", tmp_path)
    with pytest.raises(SystemExit) as e:
        doc_common.gsap_file()
    assert "npm ci" in str(e.value)
    f = tmp_path / "node_modules/gsap/dist/gsap.min.js"
    f.parent.mkdir(parents=True)
    f.write_text("x", encoding="utf-8")
    assert doc_common.gsap_file() == f


def test_log_tail(tmp_path):
    log = tmp_path / "x.log"
    log.write_text("\n".join(f"line {i}" for i in range(1, 13)) + "\n\n  \n", encoding="utf-8")
    assert doc_common.log_tail(log).splitlines() == [f"line {i}" for i in range(3, 13)]
    assert doc_common.log_tail(log, 2) == "line 11\nline 12"
    assert doc_common.log_tail(tmp_path / "nope.log") == ""


def test_render_failures_print_the_end_of_the_log():
    assert 'render failed: {log}\\n{log_tail(log)}' in (DOC / "scripts/doc_code.py").read_text(encoding="utf-8")
    assert "log_tail(o / 'render.log')" in (DOC / "scripts/doc_cut.py").read_text(encoding="utf-8")


def fake_python(tmp_path, body):
    py = tmp_path / ".venv/bin/python"
    py.parent.mkdir(parents=True)
    py.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    py.chmod(py.stat().st_mode | stat.S_IXUSR)
    return py


def test_local_asr_failure_shows_the_transcribers_stderr(tmp_path, monkeypatch):
    fake_python(tmp_path, "echo 'boom: model missing' >&2\nexit 3\n")
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", str(tmp_path))
    with pytest.raises(SystemExit) as e:
        doc_common.local_asr([tmp_path / "a.wav"], "zh")
    assert "exit 3" in str(e.value) and "boom: model missing" in str(e.value)


def test_local_asr_output_that_is_not_json_is_a_failure_too(tmp_path, monkeypatch):
    fake_python(tmp_path, "echo 'warming up'\necho 'cache broken' >&2\nexit 0\n")
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", str(tmp_path))
    with pytest.raises(SystemExit) as e:
        doc_common.local_asr([tmp_path / "a.wav"], "zh")
    assert "cache broken" in str(e.value)


def test_local_asr_still_returns_the_last_json_line(tmp_path, monkeypatch):
    fake_python(tmp_path, "echo 'noise'\necho '{\"a.wav\": \"hello\"}'\n")
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", str(tmp_path))
    assert doc_common.local_asr([tmp_path / "a.wav"], "en") == {Path("a.wav"): "hello"}


def test_a_failed_render_prints_what_the_renderer_said(tmp_path, monkeypatch):
    """假的 HyperFrames（印一行到 stderr、exit 1）：doc_cut.render 停下來的訊息要帶著那一行，不只是 log 的路徑。"""
    import shutil
    if not shutil.which("node"):
        pytest.skip("沒有 node")
    pkg = tmp_path / "hf"
    pkg.mkdir()
    (pkg / "package.json").write_text('{"name": "hyperframes", "bin": "cli.js"}', encoding="utf-8")
    (pkg / "cli.js").write_text('console.error("boom: chrome did not start"); process.exit(1);\n', encoding="utf-8")
    monkeypatch.setenv("S2F_HF_BIN", str(pkg))
    import doc_cut
    o = tmp_path / "cut"
    o.mkdir()
    with pytest.raises(SystemExit) as e:
        doc_cut.render(o)
    assert "render.log" in str(e.value) and "boom: chrome did not start" in str(e.value)
