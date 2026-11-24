"""Pack a template's premade files into a zip for its GitHub Release, and write premade.json (the other half of
fetch_premade.py).

  python3 tools/examples/pack_premade.py examples/<template>/<zh|en> --out <folder> [--tag v1.2.0]

What goes in, relative to the project folder (the zip unpacks into premade/, and the README copies premade/. back):
- a narrated project (doc.json): tts/voice.wav and tts/lines.json; with a host (host/parts.json), also host/parts.json
  and host/parts/part<k>.mp4 for every part it lists.
- a drama (cut.json): every clip the timeline uses (shots' src and pics' src) and the music file.
The zip is the same bytes for the same files (sorted names, fixed dates), so packing again changes nothing.
The zip is named <template>-<lang>.zip; premade.json gets
https://github.com/notoriouslab/script2film/releases/download/<tag>/<template>-<lang>.zip, its SHA-256 and size.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

REPO = "notoriouslab/script2film"
STAMP = (2026, 1, 1, 0, 0, 0)


def members(project):
    """The project-relative paths to pack, sorted; raises FileNotFoundError naming the first one missing."""
    project = Path(project)
    out = []
    if (project / "cut.json").is_file():
        cut = json.loads((project / "cut.json").read_text(encoding="utf-8"))
        for s in cut.get("shots", []):
            out += [s["src"]] if s.get("src") else []
            out += [p["src"] for p in s.get("pics", []) if p.get("src")]
        if cut.get("music", {}).get("file"):
            out.append(cut["music"]["file"])
    elif (project / "doc.json").is_file():
        out += ["tts/voice.wav", "tts/lines.json"]
        parts = project / "host" / "parts.json"
        if parts.is_file():
            out.append("host/parts.json")
            out += [f"host/parts/part{p['k']}.mp4" for p in json.loads(parts.read_text(encoding="utf-8"))]
    else:
        raise FileNotFoundError(f"{project}: no doc.json or cut.json")
    out = sorted(set(out))
    for m in out:
        if Path(m).is_absolute() or ".." in Path(m).parts:
            raise ValueError(f"{m}: premade files must sit inside the project folder")
        if not (project / m).is_file():
            raise FileNotFoundError(f"{project / m} is missing: make the film once before packing")
    return out


def pack(project, zip_path):
    project = Path(project)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for m in members(project):
            info = zipfile.ZipInfo(m, STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, (project / m).read_bytes())
    return zip_path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("project")
    ap.add_argument("--out", required=True, help="folder for the zip (keep it out of the repository)")
    ap.add_argument("--tag", default="v1.2.0")
    a = ap.parse_args(argv)
    project = Path(a.project)
    name = f"{project.resolve().parent.name}-{project.resolve().name}.zip"
    Path(a.out).mkdir(parents=True, exist_ok=True)
    z = pack(project, Path(a.out) / name)
    meta = {"url": f"https://github.com/{REPO}/releases/download/{a.tag}/{name}", "sha256": sha256(z),
            "bytes": z.stat().st_size}
    (project / "premade.json").write_text(json.dumps(meta) + "\n", encoding="utf-8")
    print(f"{z}  {meta['bytes']} bytes  {meta['sha256'][:12]}  ({len(members(project))} files)")


if __name__ == "__main__":
    sys.exit(main())
