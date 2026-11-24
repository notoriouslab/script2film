"""Fetch a template's premade files (narration, host clips, generated shots) from its GitHub Release.

  python3 tools/examples/fetch_premade.py examples/<template>/<zh|en>

The project folder holds premade.json: {"url": "<release asset .zip>", "sha256": "<hex>", "bytes": <size>}. The zip is
downloaded with curl (stopped past "bytes"), its SHA-256 compared with the one in the repository (an asset swapped on
the release no longer matches and is refused), every member checked to stay inside premade/, then unpacked there.
premade/.sha256 records what is in place, so a second run with the same hash does nothing.
On any failure it prints the release page and the commands to download and unpack by hand, and exits 1.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def release_page(url):
    """https://github.com/o/r/releases/download/<tag>/<file> → https://github.com/o/r/releases/tag/<tag>; else the url."""
    if "/releases/download/" not in url:
        return url
    base, rest = url.split("/releases/download/", 1)
    return f"{base}/releases/tag/{rest.split('/', 1)[0]}"


def fail(meta, why):
    page = release_page(meta.get("url", "")) if meta else ""
    sys.exit(f"✗ premade: {why}\n"
             + (f"  Download it by hand from {page}\n"
                f"  then: unzip <file>.zip -d <project>/premade && python3 tools/examples/fetch_premade.py <project>\n"
                if page else ""))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def unpack(zip_path, dest):
    """Unzip into dest, refusing any member that would land outside it (an absolute path or ../)."""
    dest = Path(dest).resolve()
    with zipfile.ZipFile(zip_path) as z:
        for m in z.infolist():
            if not (dest / m.filename).resolve().is_relative_to(dest):
                raise ValueError(f"member outside premade/: {m.filename}")
        z.extractall(dest)


def fetch(project):
    project = Path(project)
    try:
        meta = json.loads((project / "premade.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        fail(None, f"cannot read {project / 'premade.json'}: {e}")
    if not all(meta.get(k) for k in ("url", "sha256", "bytes")):
        fail(meta, f"{project / 'premade.json'} needs url, sha256 and bytes")
    dest = project / "premade"
    mark = dest / ".sha256"
    if mark.is_file() and mark.read_text().strip() == meta["sha256"]:
        print(f"✓ premade already in place: {dest}")
        return dest
    with tempfile.TemporaryDirectory() as tmp:
        z = Path(tmp) / "premade.zip"
        r = subprocess.run(["curl", "-fsSL", "--max-filesize", str(int(meta["bytes"])), "-o", str(z), meta["url"]],
                           capture_output=True, text=True)
        if r.returncode:
            fail(meta, f"download failed (curl exit {r.returncode}): {r.stderr.strip() or meta['url']}")
        if z.stat().st_size > int(meta["bytes"]):
            fail(meta, f"the file is {z.stat().st_size} bytes, more than the {meta['bytes']} expected")
        got = sha256(z)
        if got != meta["sha256"]:
            fail(meta, f"SHA-256 does not match (got {got}, expected {meta['sha256']})")
        staged = Path(tmp) / "out"
        try:
            unpack(z, staged)
        except (ValueError, zipfile.BadZipFile) as e:
            fail(meta, str(e))
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(staged, dest)
    mark.write_text(meta["sha256"] + "\n")
    print(f"✓ premade unpacked: {dest}")
    return dest


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    fetch(sys.argv[1])
