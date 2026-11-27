"""doc.json "font": no key keeps Noto (None); a name is looked up in the fonts asset layers; the @font-face spans 100–900
so the browser draws the file's own weight and never fakes a bold."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import doc_common  # noqa: E402


def test_no_key_means_no_font():
    assert doc_common.doc_font({}) is None


def test_name_found_in_user_layer(tmp_path, monkeypatch):
    (tmp_path / "fonts").mkdir()
    f = tmp_path / "fonts" / "Kai-Medium.ttf"
    f.write_bytes(b"x")
    monkeypatch.setenv("S2F_ASSETS_LOCAL", str(tmp_path))
    assert doc_common.doc_font({"font": "Kai-Medium.ttf"}) == f


def test_font_face_uses_file_name_and_full_weight_range():
    css = doc_common.doc_font_face(Path("/a/b/Kai-Medium.ttf"))
    assert 'url("fonts/Kai-Medium.ttf")' in css
    assert "font-weight: 100 900" in css
    assert f'font-family: "{doc_common.DOC_FONT}"' in css
