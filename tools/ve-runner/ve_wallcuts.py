"""Hidden cuts in an occlusion one-take: find where a foreground wall covers the frame, and join pieces there.

An occlusion one-take tracks sideways past walls or columns close to the lens; each time one fills the frame the
place, time or clothes change (styles/live.md, "Occlusion one-take"). A frame fully covered by a wall looks the same
in any clip, so two clips can be joined there and an over-long wall can be trimmed from the middle.

  python3 ve_wallcuts.py spans clip.mp4 ...          # candidate wall spans: start-end s, blurriest frame
  python3 ve_wallcuts.py sheet clip.mp4 out.jpg      # 4 frames a second, to check the candidates by eye
  python3 ve_wallcuts.py join out.mp4 a.mp4:0:6.2 b.mp4:3.55:6.45 b.mp4:7.1:end

`spans` marks frames whose sharpness (variance of the Laplacian) is under LOW x the clip's median: a wall near the
lens is out of focus. A wall with clear texture (stone) stays sharp and is missed, so always check the cut frame
on the sheet: the frame at each cut must be fully covered (measured 2026-11-22: a cut 0.2 s early showed the
kitchen beside the wall; a street seen through a dissolve was not a cover).
"""
import subprocess
import sys

import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import numpy as np

LOW = 0.25        # sharpness below this share of the clip's median counts as covered
MIN_FRAMES = 3    # shorter dips are a post or a hand passing, not a cover
FADE = 0.05       # seconds of audio fade at each join, so the cut does not click


def wall_spans(sharpness, fps, low=LOW, min_frames=MIN_FRAMES):
    """[(start_s, end_s, blurriest_s)] for runs of at least min_frames frames under low x median sharpness."""
    v = np.asarray(sharpness, dtype=float)
    if v.size == 0 or fps <= 0:
        return []
    under = v < np.median(v) * low
    out, i = [], 0
    while i < v.size:
        if not under[i]:
            i += 1
            continue
        j = i
        while j < v.size and under[j]:
            j += 1
        if j - i >= min_frames:
            k = i + int(np.argmin(v[i:j]))
            out.append((round(i / fps, 2), round(j / fps, 2), round(k / fps, 2)))
        i = j
    return out


def parse_piece(arg, duration_of):
    """'clip.mp4:3.55:end' → (clip, 3.55, duration). The clip name may itself contain ':' only before the last two."""
    clip, a, b = arg.rsplit(":", 2)
    start = float(a)
    end = duration_of(clip) if b == "end" else float(b)
    if not 0 <= start < end:
        raise ValueError(f"bad piece {arg}: start {start}, end {end}")
    return clip, start, end


def join_filter(pieces, size="1280:720", fps=24):
    """ffmpeg filter_complex for pieces [(input index, start, end)] trimmed and joined in order."""
    parts, labels = [], []
    for n, (idx, a, b) in enumerate(pieces):
        d = round(b - a, 3)
        parts.append(f"[{idx}:v]trim={a}:{b},setpts=PTS-STARTPTS,fps={fps},scale={size},setsar=1[v{n}]")
        parts.append(f"[{idx}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},"
                     f"afade=t=out:st={max(0.0, round(d - FADE, 3))}:d={FADE}[a{n}]")
        labels.append(f"[v{n}][a{n}]")
    parts.append("".join(labels) + f"concat=n={len(pieces)}:v=1:a=1[v][a]")
    return ";".join(parts)


def _duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]))


def _sharpness(path):
    import cv2
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    vals = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (480, int(480 * f.shape[0] / f.shape[1]))), cv2.COLOR_BGR2GRAY)
        vals.append(cv2.Laplacian(g, cv2.CV_64F).var())
    return fps, vals


def _size(path):
    w, h = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", path], text=True).strip().split(",")
    return f"{w}:{h}"


def main(argv):
    if len(argv) < 2 or argv[0] not in ("spans", "sheet", "join"):
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "spans":
        for p in rest:
            fps, vals = _sharpness(p)
            print(p, wall_spans(vals, fps))
        return 0
    if cmd == "sheet":
        clip, out = rest
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vf", "fps=4,scale=240:-1,tile=10x5",
                        "-frames:v", "1", out], check=True)
        print(out, "(left to right, top to bottom: one frame every 0.25 s from 0 s)")
        return 0
    out, args = rest[0], rest[1:]
    pieces = [parse_piece(a, _duration) for a in args]
    clips = list(dict.fromkeys(c for c, _, _ in pieces))
    ins = sum((["-i", c] for c in clips), [])
    fc = join_filter([(clips.index(c), a, b) for c, a, b in pieces], size=_size(clips[0]))
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", out], check=True)
    print(out, round(sum(b - a for _, a, b in pieces), 2), "s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
