"""ve_collect 的設定檔判斷：沒人用就直接用；被佔用就複製一份不含快取與鎖檔的。"""
import os

import pytest

pytest.importorskip("playwright")
import ve_collect as vc  # noqa: E402


def make_profile(root):
    p = root / ".profile"
    (p / "Default" / "Code Cache").mkdir(parents=True)
    (p / "Default" / "Code Cache" / "big.bin").write_bytes(b"x" * 10)
    (p / "Default" / "Service Worker").mkdir()
    (p / "GPUCache").mkdir()
    (p / "Default" / "Cookies").write_text("login")
    (p / "Local State").write_text("{}")
    return p


def test_free_profile_is_used_directly(tmp_path):
    p = make_profile(tmp_path)
    assert vc.usable_profile(p) == (p, None)


def test_locked_profile_is_copied_without_caches(tmp_path):
    p = make_profile(tmp_path)
    os.symlink("host-12345", p / "SingletonLock")      # Chrome 的鎖檔是指向不存在目標的符號連結
    assert vc.in_use(p)
    use, tmp = vc.usable_profile(p)
    try:
        assert tmp is not None and use != p
        assert (use / "Default" / "Cookies").read_text() == "login"
        assert (use / "Local State").exists()
        for skipped in ("SingletonLock", "GPUCache", "Default/Code Cache", "Default/Service Worker"):
            assert not os.path.lexists(use / skipped), skipped
    finally:
        vc.shutil.rmtree(tmp, ignore_errors=True)
