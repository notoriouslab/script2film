"""S2F_ prefix on the tool variables (s2f-naming D6): S2F_<name> when set (non-empty), otherwise the old name <name>.
Covers doc_common.s2f_env, need_local_asr and qwen_models_dir with either name, both, or neither."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import doc_common  # noqa: E402

NAMES = ("MLX_WHISPER_DIR", "QWEN_TTS_DIR", "QWEN_TTS_MODELS")


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    for n in NAMES:
        monkeypatch.delenv(n, raising=False)
        monkeypatch.delenv(f"S2F_{n}", raising=False)


def test_s2f_env_only_new(monkeypatch):
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", "/new")
    assert doc_common.s2f_env("MLX_WHISPER_DIR") == "/new"


def test_s2f_env_only_old(monkeypatch):
    monkeypatch.setenv("MLX_WHISPER_DIR", "/old")
    assert doc_common.s2f_env("MLX_WHISPER_DIR") == "/old"


def test_s2f_env_both_takes_new(monkeypatch):
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", "/new")
    monkeypatch.setenv("MLX_WHISPER_DIR", "/old")
    assert doc_common.s2f_env("MLX_WHISPER_DIR") == "/new"


def test_s2f_env_neither_is_none():
    assert doc_common.s2f_env("MLX_WHISPER_DIR") is None


def test_need_local_asr_only_old_name(monkeypatch, tmp_path):
    monkeypatch.setenv("MLX_WHISPER_DIR", str(tmp_path))
    doc_common.need_local_asr()


def test_need_local_asr_only_new_name(monkeypatch, tmp_path):
    monkeypatch.setenv("S2F_MLX_WHISPER_DIR", str(tmp_path))
    doc_common.need_local_asr()


def test_need_local_asr_neither_stops_with_new_name():
    with pytest.raises(SystemExit) as e:
        doc_common.need_local_asr()
    assert "S2F_MLX_WHISPER_DIR" in str(e.value)


def test_qwen_models_dir_only_old_tts_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("QWEN_TTS_DIR", str(tmp_path / "qwen3-tts"))
    assert doc_common.qwen_models_dir() == tmp_path / "_models"


def test_qwen_models_dir_neither_stops():
    with pytest.raises(SystemExit) as e:
        doc_common.qwen_models_dir()
    assert "S2F_QWEN_TTS_DIR" in str(e.value)
