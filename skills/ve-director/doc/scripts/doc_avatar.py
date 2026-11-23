"""Comic avatar host (doc.json "avatar"): a pack of comic panels of the narrator that pops in on the narrator's own
emotional or call-to-action lines, instead of a talking host.

  python3 doc_avatar.py pack <sheet.png> --grid 5x2 --names shock,think,... --out <pack>
  python3 doc_avatar.py open <pack> <open-mouth sheet> --grid 5x2 [--keep-mouth]
  python3 doc_avatar.py shut <pack> cheer thumbs-up [--keep 0.5]
  python3 doc_avatar.py check <pack>

A pack is a folder: faces.json {"shock": {"file": "01-shock.png", "cx": 0.48, "cy": 0.40}, ...} plus one png per face.
cx / cy are the face centre as a fraction of the image; the badge crop and the peek depth are worked out from them.
After `pack`, look at faces_check.png (badge circle and peek lines drawn on every panel), fix faces.json, run `check`.

Three ways on screen ("show"): panel (the whole comic panel, tilted, slid in), peek (the panel peeks in from an edge and
goes back), badge (a small round badge kept in a corner; a "badge" moment flips it to another face). One avatar at a time:
the badge hides while a panel or a peek is up.

Talking: a second sheet with the same faces, mouths open (`open`), makes every visible avatar open and close its mouth
with the narration's loudness (not lip sync). Only the mouth is taken from that sheet (see mouth_patch).
A face drawn with its mouth already open (a laugh) barely changes between the two sheets; `shut` gives it a closed frame
with the drawn mouth squeezed to half its height, which the talking avatar rests on. Pick those faces by eye after `open`.
"""
import argparse
import json
import sys
from pathlib import Path

SHOWS = ("panel", "peek", "badge")
PEEK_POS = ("left", "right", "lower-left", "lower-right")
PANEL_POS = ("left", "center", "right")
BADGE_POS = ("upper-left", "upper-right", "lower-left", "lower-right")
HOLD = {"panel": 1.8, "peek": 1.4}
# seconds: in, out (badge flip is one FLIP for both halves)
PANEL_IN, PANEL_OUT, PEEK_IN, PEEK_OUT, FLIP, BADGE_POP = 0.45, 0.5, 0.35, 0.3, 0.3, 0.25
FACE_R = 0.24          # the face circle's radius, as a fraction of the panel width
EDGE = 24              # px from the frame edge for lower-corner peeks and badges
MIST_TOP = 800         # doc_cut shell(): the subtitle mist starts here; a panel stays above it
Z = 97                 # above the mist (95), under the subtitles (100)


# ---------- pack / check ----------

def _runs(profile, th=0.6):
    """[(start, end)] of consecutive indices where profile > th."""
    out, start = [], None
    for i, v in enumerate(list(profile) + [0]):
        if v > th and start is None:
            start = i
        elif v <= th and start is not None:
            out.append((start, i - 1))
            start = None
    return out


def _longest(dark):
    """Per column: the longest unbroken dark run. A frame line is one long stroke; hair, flames or a dark backdrop
    break up or stop short, which a plain dark share does not tell apart."""
    import numpy as np
    best = np.zeros(dark.shape[1], int)
    cur = np.zeros(dark.shape[1], int)
    for row in dark:
        cur = np.where(row, cur + 1, 0)
        best = np.maximum(best, cur)
    return best


def _frame(runs, n, size):
    """(outer-left run, outer-right run) per panel along one axis: paired in order when there are exactly 2n lines,
    else the first and last line inside each of n equal slots (a dark backdrop can add a run inside a panel)."""
    if len(runs) == 2 * n:
        return [(runs[2 * k], runs[2 * k + 1]) for k in range(n)]
    out = []
    for k in range(n):
        lo, hi = k * size / n, (k + 1) * size / n
        inside = [r for r in runs if lo <= (r[0] + r[1]) / 2 < hi]
        out.append((inside[0], inside[-1]) if len(inside) >= 2 else None)
    return out


def grid_boxes(gray, cols, rows, inset=9):
    """Crop boxes of a cols x rows comic sheet with dark frame lines (gray < 100), row by row. A frame line is a
    column (row) whose longest dark run covers > 0.6 of a panel's height (width). The inner edge is the line's outer
    side plus its typical thickness, so dark art touching the frame is not mistaken for frame."""
    import numpy as np
    dark = np.asarray(gray) < 100
    H, W = dark.shape
    xs = _frame(_runs(_longest(dark) / (H / rows)), cols, W)
    ys = _frame(_runs(_longest(dark.T) / (W / cols)), rows, H)
    if None in xs or None in ys:
        sys.exit(f"✗ pack: frame lines not found for a {cols}x{rows} grid (needs dark panel borders)")
    t = int(np.median([e - s + 1 for pair in xs + ys for s, e in pair]))
    boxes = []
    for (top, bot) in ys:
        for (left, right) in xs:
            boxes.append((left[0] + t + inset, top[0] + t + inset, right[1] - t - inset + 1, bot[1] - t - inset + 1))
    return boxes


def draw_check(pack):
    """faces_check.png: every panel with its badge circle and the peek lines (side: right / left visible width; lower:
    visible height), so a wrong cx / cy shows at a glance."""
    from PIL import Image, ImageDraw
    faces = json.loads((pack / "faces.json").read_text())
    tiles = []
    for name, f in faces.items():
        im = Image.open(pack / f["file"]).convert("RGB")
        w, h = im.size
        d = ImageDraw.Draw(im)
        cx, cy, r = f["cx"] * w, f["cy"] * h, FACE_R * w
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 0, 0), width=4)
        # what stays on screen: a lower peek shows the panel above the blue line; a right-edge peek the part left of
        # the right green line, a left-edge peek the part right of the left green line
        yb = h * lower_visible(f["cy"])
        xr, xl = w * side_visible(f["cx"], "right"), w * (1 - side_visible(f["cx"], "left"))
        d.line([0, yb, w, yb], fill=(0, 120, 255), width=3)
        d.line([xr, 0, xr, h], fill=(0, 160, 0), width=3)
        d.line([xl, 0, xl, h], fill=(0, 160, 0), width=3)
        if "mx" in f:
            mx, my = f["mx"] * w, f["my"] * h
            d.ellipse([mx - MOUTH_RX * w, my - MOUTH_RY * w, mx + MOUTH_RX * w, my + MOUTH_RY * w], outline=(255, 0, 255), width=3)
        d.text((8, 8), name, fill=(255, 0, 0))
        tile = im.resize((240, int(240 * h / w)))
        if f.get("open") and (pack / f["open"]).is_file():   # the open-mouth panel in the corner, to compare
            tile.paste(Image.open(pack / f["open"]).convert("RGB").resize((96, int(96 * h / w))), (240 - 96, 0))
        tiles.append(tile)
    th = max(t.height for t in tiles)
    sheet = Image.new("RGB", (250 * min(5, len(tiles)) + 10, (th + 10) * ((len(tiles) + 4) // 5) + 10), "white")
    for k, t in enumerate(tiles):
        sheet.paste(t, (10 + 250 * (k % 5), 10 + (th + 10) * (k // 5)))
    sheet.save(pack / "faces_check.png")


def pack_sheet(sheet, grid, names, out):
    from PIL import Image
    cols, rows = map(int, grid.lower().split("x"))
    if len(names) != cols * rows:
        sys.exit(f"✗ pack: {len(names)} names for a {cols}x{rows} grid")
    im = Image.open(sheet).convert("RGB")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    faces = {}
    for k, (name, box) in enumerate(zip(names, grid_boxes(im.convert("L"), cols, rows))):
        f = f"{k + 1:02d}-{name}.png"
        im.crop(box).save(out / f)
        faces[name] = {"file": f, "cx": 0.5, "cy": 0.42}
    (out / "faces.json").write_text(json.dumps(faces, indent=2, ensure_ascii=False) + "\n")
    draw_check(out)
    return faces


def check_pack(pack):
    """List what is wrong with a pack ([] when fine)."""
    from PIL import Image
    pack = Path(pack)
    fj = pack / "faces.json"
    if not fj.is_file():
        return [f"{fj} missing"]
    bad = []
    for name, f in json.loads(fj.read_text()).items():
        p = pack / f.get("file", "")
        if not f.get("file") or not p.is_file():
            bad.append(f"{name}: file {f.get('file')!r} missing")
            continue
        if not all(isinstance(f.get(k), (int, float)) and 0 <= f[k] <= 1 for k in ("cx", "cy")):
            bad.append(f"{name}: cx / cy must be between 0 and 1")
        if Image.open(p).width < 400:
            bad.append(f"{name}: {Image.open(p).width} px wide, needs at least 400")
        if "open" in f:
            o = pack / f["open"]
            if not o.is_file():
                bad.append(f"{name}: open {f['open']!r} missing")
            elif Image.open(o).size != Image.open(p).size:
                bad.append(f"{name}: open is {Image.open(o).size}, the face is {Image.open(p).size}")
            if not all(isinstance(f.get(k), (int, float)) and 0 <= f[k] <= 1 for k in ("mx", "my")):
                bad.append(f"{name}: mx / my must be between 0 and 1")
        if "shut" in f:
            o = pack / f["shut"]
            if not o.is_file():
                bad.append(f"{name}: shut {f['shut']!r} missing")
            elif Image.open(o).size != Image.open(p).size:
                bad.append(f"{name}: shut is {Image.open(o).size}, the face is {Image.open(p).size}")
    return bad


MOUTH_RX, MOUTH_RY, MOUTH_BLUR = 0.17, 0.10, 8   # the mouth patch: half-width / half-height (panel widths), feather px
SAME_FACE = 0.6                                  # open panel vs its closed panel, gray correlation at 64 x 64


def find_mouth(closed, opened, cx, cy):
    """(mx, my): where the open-mouth panel differs most from the closed one, below the face centre and within the face
    (Gaussian-blurred gray difference). Both PIL images of the same size."""
    import numpy as np
    from scipy import ndimage
    a = np.asarray(closed.convert("L"), float)
    b = np.asarray(opened.convert("L"), float)
    h, w = a.shape
    d = ndimage.gaussian_filter(np.abs(a - b), 3)
    r = FACE_R * w
    m = np.zeros_like(d, bool)
    m[int(cy * h):int(cy * h + 1.6 * r), max(0, int(cx * w - 0.9 * r)):int(cx * w + 0.9 * r)] = True
    y, x = np.unravel_index(np.where(m, d, 0).argmax(), d.shape)
    return round(x / w, 3), round(y / h, 3)


def mouth_patch(closed, opened, mx, my):
    """The closed panel with only a feathered ellipse around (mx, my) taken from the open one: the open sheet is a redraw,
    and its background lines, petals and confetti differ (1-9 % of the pixels outside the mouth), so swapping whole
    images would flicker."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = closed.size
    x, y, rx, ry = mx * w, my * h, MOUTH_RX * w, MOUTH_RY * w
    mask = Image.new("L", closed.size, 0)
    ImageDraw.Draw(mask).ellipse([x - rx, y - ry, x + rx, y + ry], fill=255)
    return Image.composite(opened.convert("RGB"), closed.convert("RGB"), mask.filter(ImageFilter.GaussianBlur(MOUTH_BLUR)))


def _similar(a, b):
    import numpy as np
    x = np.asarray(a.convert("L").resize((64, 64)), float).ravel()
    y = np.asarray(b.convert("L").resize((64, 64)), float).ravel()
    return float(np.corrcoef(x, y)[0, 1])


def open_sheet(pack, sheet, grid, keep_mouth=False):
    """Cut an open-mouth sheet laid out like the pack's own (same grid, faces in faces.json's file-number order) into
    <NN-name>_open.<ext>: the closed panel with the mouth taken from the open one. Writes open / mx / my into faces.json.
    Stops when a cell does not look like its closed panel (a sheet in another order would put mouths on other faces)."""
    from PIL import Image
    pack = Path(pack)
    faces = json.loads((pack / "faces.json").read_text())
    cols, rows = map(int, grid.lower().split("x"))
    order = sorted(faces, key=lambda k: faces[k]["file"])
    if len(order) != cols * rows:
        sys.exit(f"✗ open: {len(order)} faces in the pack, {cols}x{rows} cells in the sheet")
    im = Image.open(sheet).convert("RGB")
    cells = [im.crop(b) for b in grid_boxes(im.convert("L"), cols, rows)]
    closed = {k: Image.open(pack / faces[k]["file"]).convert("RGB") for k in order}
    opened = {k: c.resize(closed[k].size) for k, c in zip(order, cells)}
    bad = [f"cell {n + 1} ({k}): looks like a different picture ({_similar(closed[k], opened[k]):.2f} < {SAME_FACE})"
           for n, k in enumerate(order) if _similar(closed[k], opened[k]) < SAME_FACE]
    if bad:
        sys.exit("✗ open:\n  " + "\n  ".join(bad))
    for k in order:
        f = faces[k]
        if not (keep_mouth and "mx" in f and "my" in f):
            f["mx"], f["my"] = find_mouth(closed[k], opened[k], f["cx"], f["cy"])
        stem, ext = f["file"].rsplit(".", 1)
        f["open"] = f"{stem}_open.{ext}"
        out = mouth_patch(closed[k], opened[k], f["mx"], f["my"])
        out.save(pack / f["open"], **({"quality": 88} if ext.lower() in ("jpg", "jpeg") else {}))
    (pack / "faces.json").write_text(json.dumps(faces, indent=2, ensure_ascii=False) + "\n")
    draw_check(pack)
    return faces


SHUT_KEEP = 0.5        # shut: the drawn mouth is squeezed to this share of its height (2026-11-24, tried on a laughing face)
SHUT_KEEP_RANGE = (0.2, 0.9)   # below: a slit that no longer reads as a mouth; above: too close to the open drawing
SHUT_SKIN = 45         # RGB distance from the skin colour that counts as part of the mouth (lips, teeth, tongue, outline)


def mouth_mask(img, mx, my):
    """The drawn mouth around (mx, my) as a bool array: the shape that is not skin, connected to the mouth centre, holes
    filled. None when it runs into the face's other lines (it reaches the search ellipse's edge: jaw, hand, hair),
    because then it is not the mouth alone. Skin is the median colour of a band just above the mouth."""
    import numpy as np
    from scipy import ndimage
    a = np.asarray(img.convert("RGB"), float)
    h, w, _ = a.shape
    X, Y = int(mx * w), int(my * h)
    band = a[max(0, int(Y - .12 * h)):max(1, int(Y - .06 * h)), max(0, int(X - .08 * w)):int(X + .08 * w)].reshape(-1, 3)
    skin = np.median(band, 0)
    yy, xx = np.mgrid[0:h, 0:w]
    ell = ((xx - X) / (.2 * w)) ** 2 + ((yy - Y) / (.13 * h)) ** 2 <= 1
    lab, _ = ndimage.label((np.sqrt(((a - skin) ** 2).sum(2)) > SHUT_SKIN) & ell)
    ids = [lab[y, x] for y in range(Y - 10, Y + 11, 2) for x in range(X - 10, X + 11, 2) if 0 <= y < h and 0 <= x < w and lab[y, x]]
    if not ids:
        return None, skin
    m = ndimage.binary_fill_holes(lab == max(set(ids), key=ids.count))
    if (m & ell & ~ndimage.binary_erosion(ell, iterations=2)).any():   # reaches the search edge: joined to other lines
        return None, skin
    return m, skin


def shut_face(img, mx, my, keep=SHUT_KEEP):
    """A face drawn with its mouth already open (a laugh), made into a closed frame: the mouth painted over with skin and
    pasted back squeezed to `keep` of its height (92 % of its width), hanging from the upper lip. Its open panel then
    differs enough to read as talking even in a 170 px badge (2026-11-24: the laughing face's two drawings looked alike).
    None when the mouth cannot be told from the other lines."""
    import numpy as np
    from PIL import Image, ImageFilter
    from scipy import ndimage
    m, skin = mouth_mask(img, mx, my)
    if m is None:
        return None
    img = img.convert("RGB")
    ys, xs = np.where(m)
    t, b, l, r = ys.min(), ys.max(), xs.min(), xs.max()
    base = np.asarray(img).copy()
    base[ndimage.binary_dilation(m, iterations=3)] = skin.astype(np.uint8)
    out = Image.fromarray(base)
    mw, mh = r - l + 1, b - t + 1
    nw, nh = max(2, int(mw * .92)), max(4, int(mh * keep))
    part = img.crop((l, t, r + 1, b + 1)).resize((nw, nh), Image.LANCZOS)
    alpha = Image.fromarray((m[t:b + 1, l:r + 1] * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1))
    out.paste(part, (l + (mw - nw) // 2, t + int(mh * .08)), alpha)
    return out


def shut_faces(pack, names, keep=SHUT_KEEP):
    """shut_face() for the named faces of a pack → <NN-name>_shut.<ext> and "shut" in faces.json. Needs "open" first (the
    mouth position comes from it). Stops, listing every face it could not do, before writing anything."""
    from PIL import Image
    if not SHUT_KEEP_RANGE[0] <= keep <= SHUT_KEEP_RANGE[1]:
        sys.exit(f"✗ shut: --keep must be between {SHUT_KEEP_RANGE[0]} and {SHUT_KEEP_RANGE[1]}: {keep}")
    pack = Path(pack)
    faces = json.loads((pack / "faces.json").read_text())
    bad = [f"{n}: not in the pack" for n in names if n not in faces]
    bad += [f"{n}: no open-mouth panel yet (run open first)" for n in names if n in faces and "mx" not in faces[n]]
    if bad:
        sys.exit("✗ shut:\n  " + "\n  ".join(bad))
    made = {n: shut_face(Image.open(pack / faces[n]["file"]), faces[n]["mx"], faces[n]["my"], keep) for n in names}
    if bad := [f"{n}: the mouth runs into other lines (jaw, hand, hair), so it cannot be squeezed alone" for n, im in made.items() if im is None]:
        sys.exit("✗ shut:\n  " + "\n  ".join(bad))
    for n, im in made.items():
        stem, ext = faces[n]["file"].rsplit(".", 1)
        faces[n]["shut"] = f"{stem}_shut.{ext}"
        im.save(pack / faces[n]["shut"], **({"quality": 88} if ext.lower() in ("jpg", "jpeg") else {}))
    (pack / "faces.json").write_text(json.dumps(faces, indent=2, ensure_ascii=False) + "\n")
    return faces


def talking(faces):
    """The faces as a talking avatar draws them: a face with a "shut" panel rests on it (its open panel is the other
    frame); without talking the drawing stays as it was."""
    return {k: {**f, "file": f["shut"]} if f.get("shut") else f for k, f in faces.items()}


def load_pack(pack):
    """{face: {"file", "cx", "cy", "w", "h"}} of a pack folder (sizes read from the pngs)."""
    from PIL import Image
    pack = Path(pack)
    faces = json.loads((pack / "faces.json").read_text())
    for f in faces.values():
        f["w"], f["h"] = Image.open(pack / f["file"]).size
    return faces


def find_pack(project, name):
    """<project>/avatar/<name>/ first (a film's own pack, e.g. an example's), then the asset layers."""
    own = Path(project) / "avatar" / name
    if (own / "faces.json").is_file():
        return own
    from doc_common import asset
    return asset("avatar", name)


# ---------- geometry (1920 x 1080 unless w / h given) ----------

def lower_visible(cy):
    """Share of the panel height shown by a lower-corner peek: the face circle and the chin always in."""
    return min(1.0, max(0.8, cy + FACE_R + 0.1))


def side_visible(cx, pos):
    """Share of the panel width shown by a side peek."""
    return min(1.0, (cx if pos == "right" else 1 - cx) + FACE_R)


def peek_geometry(face, pos, w=1920, h=1080):
    """Where a peek rests when fully out: {x, y, w, h} of the panel box and the slide (dx, dy) it comes in from."""
    aspect = face["h"] / face["w"]
    if pos in ("left", "right"):
        qw = round(0.42 * h)
        qh = round(qw * aspect)
        vis = side_visible(face["cx"], pos) * qw
        x = w - vis if pos == "right" else vis - qw
        return {"x": round(x), "y": round(0.2 * h), "w": qw, "h": qh, "dx": round(qw * 1.1) * (1 if pos == "right" else -1), "dy": 0}
    if pos in ("lower-left", "lower-right"):
        qw = round(0.34 * h)
        qh = round(qw * aspect)
        x = EDGE if pos == "lower-left" else w - EDGE - qw
        return {"x": x, "y": round(h - lower_visible(face["cy"]) * qh), "w": qw, "h": qh, "dx": 0, "dy": qh}
    raise ValueError(pos)


def panel_geometry(face, pos="center", w=1920, h=1080):
    """The whole panel: 0.64 of the frame height, top 96 (bottom above the subtitle mist)."""
    ph = round(0.64 * h)
    pw = round(ph * face["w"] / face["h"])
    x = {"left": round(0.07 * w), "center": round((w - pw) / 2), "right": round(w - 0.07 * w - pw)}[pos]
    return {"x": x, "y": 96, "w": pw, "h": ph}


def badge_geometry(pos, d=170, w=1920, h=1080):
    """Badge box; lower corners rest at 0.8 of the frame height, clear of the subtitle line."""
    x = EDGE if pos.endswith("left") else w - EDGE - d
    y = EDGE if pos.startswith("upper") else round(0.8 * h) - d
    return {"x": x, "y": y, "w": d, "h": d}


# ---------- timing ----------

def resolve(doc, beats, faces, phrase_time):
    """doc["avatar"] → sorted events [{t, kind, face, pos, end}] in film seconds. kind: panel / peek / flip (badge face
    change) / badge-on / badge-off. phrase_time(doc, beat, phrase) is doc_cut's, passed in to keep the import one-way.
    Every problem is collected and reported in one stop."""
    av = doc.get("avatar")
    if not av:
        return []
    by_id = {b["id"]: b for b in beats}
    bad, moments = [], []
    for m in av.get("moments", []):
        where = f"{m.get('beat')} \"{m.get('at')}\""
        b = by_id.get(m.get("beat"))
        show, pos = m.get("show"), m.get("pos")
        if show not in SHOWS:
            bad.append(f"{where}: show must be one of {', '.join(SHOWS)}: {show!r}")
        if m.get("face") not in faces:
            bad.append(f"{where}: face {m.get('face')!r} not in the pack ({', '.join(faces)})")
        if show == "peek" and pos not in PEEK_POS:
            bad.append(f"{where}: peek pos must be one of {', '.join(PEEK_POS)}: {pos!r}")
        if show == "panel" and pos is not None and pos not in PANEL_POS:
            bad.append(f"{where}: panel pos must be one of {', '.join(PANEL_POS)}: {pos!r}")
        if b is None:
            bad.append(f"{where}: unknown beat")
            continue
        off = phrase_time(doc, b, m.get("at", ""))
        if off is None:
            bad.append(f"{where}: phrase not in the beat's narration")
            continue
        moments.append((b["start"] + off, m))
    badge = av.get("badge")
    if badge:
        if badge.get("pos", "lower-right") not in BADGE_POS:
            bad.append(f"badge pos must be one of {', '.join(BADGE_POS)}: {badge.get('pos')!r}")
        if badge.get("face") and badge["face"] not in faces:
            bad.append(f"badge face {badge['face']!r} not in the pack")
        if badge.get("from") and badge["from"] not in by_id:
            bad.append(f"badge from: unknown beat {badge['from']!r}")
    if not badge and any(m.get("show") == "badge" for _, m in moments):
        bad.append("a \"badge\" moment needs avatar.badge")
    if bad:
        sys.exit("✗ avatar:\n  " + "\n  ".join(bad))

    moments.sort(key=lambda x: x[0])
    ev = []
    for t, m in moments:
        if m["show"] == "badge":
            continue
        hold = float(m.get("hold", HOLD[m["show"]]))
        dur = (PANEL_IN + hold + PANEL_OUT) if m["show"] == "panel" else (PEEK_IN + hold + PEEK_OUT)
        ev.append({"t": round(t, 3), "kind": m["show"], "face": m["face"], "pos": m.get("pos", "center"),
                   "end": round(t + dur, 3)})
    if badge:
        panels = [e for e in ev if e["kind"] == "panel"]
        start = by_id[badge["from"]]["start"] if badge.get("from") else (panels[0]["end"] if panels else 0.0)
        for a, z in sorted((e["t"], e["end"]) for e in ev):   # never pop up over a panel or a peek: wait for it to leave
            if a <= start < z:
                start = z
        face = badge.get("face") or (panels[0]["face"] if panels else next(iter(faces)))
        busy = sorted((e["t"], e["end"]) for e in ev)
        on = [(start, face)]
        for t, m in moments:
            if m["show"] == "badge" and t >= start:
                on.append((t, m["face"]))
        # hide / show around every panel or peek after the badge starts
        out = []
        for a, z in busy:
            if z <= start:
                continue
            out.append({"t": round(max(a, start), 3), "kind": "badge-off"})
            out.append({"t": round(z, 3), "kind": "badge-on"})
        out.insert(0, {"t": round(start, 3), "kind": "badge-on", "face": face, "pos": badge.get("pos", "lower-right"),
                       "d": int(badge.get("d", 170))})
        for t, f in on[1:]:
            out.append({"t": round(t, 3), "kind": "flip", "face": f})
        ev += out
    order = {"badge-off": 0, "panel": 1, "peek": 1, "flip": 2, "badge-on": 3}
    return sorted(ev, key=lambda e: (e["t"], order[e["kind"]]))


# ---------- mouth timing ----------

FPS = 30
OPEN_HI, OPEN_LO = 0.35, 0.25     # of the 90th percentile of the voiced frames' loudness (2026-11-23 test clip, accepted)
MIN_RUN, MAX_OPEN = 2, 6          # frames: a state lasts at least 2; an open mouth closes after 6 (for 2) on a long vowel


def voice_env(path, fps=FPS):
    """Loudness (RMS) of the narration per video frame."""
    import subprocess
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    hop = 16000 // fps
    n = len(x) // hop
    return np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) if n else np.zeros(0)


def flaps(env, fps=FPS):
    """[(t_open, t_close)] seconds: the mouth opens when the voice is loud and closes when it is quiet (two thresholds, so
    it does not chatter), never for less than MIN_RUN frames, and closes for MIN_RUN after MAX_OPEN open frames."""
    import numpy as np
    env = np.asarray(env, float)
    voiced = env[env > env.max() * 0.05] if env.size and env.max() > 0 else env[:0]
    if not voiced.size:
        return []
    P = np.percentile(voiced, 90)
    hi, lo = OPEN_HI * P, OPEN_LO * P
    state, run, hold, opened, out = False, MIN_RUN, 0, None, []
    for i, e in enumerate(env):
        if hold:
            want, hold = False, hold - 1
        else:
            want = e > (lo if state else hi)
            if want != state and run < MIN_RUN:
                want = state
            if state and want and run >= MAX_OPEN:
                want, hold = False, MIN_RUN - 1
        if want != state:
            if want:
                opened = i
            else:
                out.append((round(opened / fps, 3), round(i / fps, 3)))
            state, run = want, 1
        else:
            run += 1
    if state:
        out.append((round(opened / fps, 3), round(len(env) / fps, 3)))
    return out


# ---------- markup ----------

def copy_pack(pack, faces, dest):
    """The pngs the events use → <page>/avatar/, so the page reads them by relative path (no network)."""
    import shutil
    (Path(dest) / "avatar").mkdir(parents=True, exist_ok=True)
    for f in faces.values():
        for k in ("file", "open", "shut"):
            if f.get(k):
                shutil.copy(Path(pack) / f[k], Path(dest) / "avatar" / f[k])


def _crop(face, d):
    """background-size / -position for a d px circle: centred on the face, or, when the mouth is known, halfway between
    the face centre and the mouth, so a face looking down keeps its mouth and chin inside the circle (a talking badge
    is watched at the mouth)."""
    W = d * 1.6
    H = W * face["h"] / face["w"]
    cy = (face["cy"] + face["my"]) / 2 if "my" in face else face["cy"]
    return {"backgroundImage": f"url(avatar/{face['file']})", "backgroundSize": f"{W:.1f}px {H:.1f}px",
            "backgroundPosition": f"{d / 2 - face['cx'] * W:.1f}px {d / 2 - cy * H:.1f}px"}


def avatar_markup(events, faces, mode="shell", w=1920, h=1080, mouth=None):
    """(css, dom, js) for resolve()'s events. mode "shell": js adds to the shell page's `main` timeline; "alpha": the same
    lines, for alpha_page() (one function, so the burned-in avatar and the Concat lane cannot drift apart).
    mouth: flaps() intervals; faces with an "open" panel get a mouth layer inside their card or badge (so it moves and
    flips with it), and every mouth layer opens and closes together."""
    if mode not in ("shell", "alpha"):
        raise ValueError(mode)
    css = (f".av {{ position: absolute; z-index: {Z}; opacity: 0; pointer-events: none; will-change: transform; }}\n"
           "  .av-card { background-size: cover; background-position: center; border: 6px solid #fff; outline: 3px solid #222;"
           " border-radius: 4px; box-shadow: 0 10px 28px rgba(0,0,0,.28); }\n"
           "  .av-badge { border-radius: 50%; border: 5px solid #fff; box-shadow: 0 4px 14px rgba(0,0,0,.3);"
           " background-repeat: no-repeat; background-color: #fff; }\n"
           "  .av-mouth { position: absolute; inset: 0; opacity: 0; border-radius: inherit; background-size: inherit;"
           " background-position: inherit; background-repeat: inherit; }")
    dom, js = [], []
    badge = next((e for e in events if e["kind"] == "badge-on" and "pos" in e), None)
    bg = badge_geometry(badge["pos"], badge["d"], w, h) if badge else None
    for i, e in enumerate(events):
        t = e["t"]
        if e["kind"] in ("panel", "peek"):
            f = faces[e["face"]]
            g = panel_geometry(f, e["pos"], w, h) if e["kind"] == "panel" else peek_geometry(f, e["pos"], w, h)
            inner = (f'<div class="av-mouth" style="background-image:url(avatar/{f["open"]})"></div>'
                     if mouth and f.get("open") else "")
            dom.append(f'<div id="av{i}" class="av av-card" style="left:{g["x"]}px;top:{g["y"]}px;width:{g["w"]}px;'
                       f'height:{g["h"]}px;background-image:url(avatar/{f["file"]})">{inner}</div>')
            el = f'"#av{i}"'
            if e["kind"] == "panel":
                js.append(f'main.fromTo({el}, {{xPercent: -30, rotation: -12, scale: 0.9, opacity: 0}}, '
                          f'{{xPercent: 0, rotation: -2, scale: 1, opacity: 1, duration: {PANEL_IN}, ease: "back.out(1.6)"}}, {t});')
                out = round(e["end"] - PANEL_OUT, 3)
                if bg and any(x["kind"] == "badge-on" and abs(x["t"] - e["end"]) < 1e-6 for x in events):
                    # dock: shrink and fly into the badge, which pops right after
                    dx = bg["x"] + bg["w"] / 2 - (g["x"] + g["w"] / 2)
                    dy = bg["y"] + bg["h"] / 2 - (g["y"] + g["h"] / 2)
                    js.append(f'main.to({el}, {{x: {dx:.0f}, y: {dy:.0f}, scale: 0.25, rotation: 0, opacity: 0, '
                              f'duration: {PANEL_OUT}, ease: "power2.inOut"}}, {out});')
                else:
                    js.append(f'main.to({el}, {{xPercent: 30, opacity: 0, duration: {PANEL_OUT}, ease: "power2.in"}}, {out});')
            else:
                r0, r1 = {"left": (-8, 3), "right": (8, -3), "lower-left": (-2, -2), "lower-right": (2, 2)}[e["pos"]]
                js.append(f'main.fromTo({el}, {{x: {g["dx"]}, y: {g["dy"]}, rotation: {r0}, opacity: 1}}, '
                          f'{{x: 0, y: 0, rotation: {r1}, duration: {PEEK_IN}, ease: "back.out(2.2)"}}, {t});')
                js.append(f'main.to({el}, {{x: {g["dx"]}, y: {g["dy"]}, duration: {PEEK_OUT}, ease: "power3.in"}}, '
                          f'{round(e["end"] - PEEK_OUT, 3)});')
        elif e["kind"] == "badge-on":
            if "pos" in e:
                f = faces[e["face"]]
                look = _crop(f, bg["w"])
                inner = ""
                if mouth and any(x.get("open") for x in faces.values()):
                    inner = (f'<div id="avbm" class="av-mouth" style="background-image:'
                             f'{"url(avatar/" + f["open"] + ")" if f.get("open") else "none"}"></div>')
                dom.append(f'<div id="avb" class="av av-badge" style="left:{bg["x"]}px;top:{bg["y"]}px;width:{bg["w"]}px;'
                           f'height:{bg["h"]}px;background-image:{look["backgroundImage"]};background-size:{look["backgroundSize"]};'
                           f'background-position:{look["backgroundPosition"]}">{inner}</div>')
            js.append(f'main.fromTo("#avb", {{scale: 0.6, opacity: 0}}, {{scale: 1, opacity: 1, duration: {BADGE_POP}, '
                      f'ease: "back.out(2)", immediateRender: false}}, {t});')
        elif e["kind"] == "badge-off":
            js.append(f'main.to("#avb", {{scale: 0.6, opacity: 0, duration: 0.2, ease: "power2.in"}}, {t});')
        elif e["kind"] == "flip":
            half = FLIP / 2
            js.append(f'main.to("#avb", {{scaleX: 0, duration: {half}, ease: "power1.in"}}, {t});')
            js.append(f'main.set("#avb", {json.dumps(_crop(faces[e["face"]], bg["w"]))}, {round(t + half, 3)});')
            if mouth and any(x.get("open") for x in faces.values()):   # the badge's mouth follows the new face, or hides
                op = faces[e["face"]].get("open")
                js.append(f'main.set("#avbm", {json.dumps({"backgroundImage": f"url(avatar/{op})", "display": "block"} if op else {"display": "none"})}, '
                          f'{round(t + half, 3)});')
            js.append(f'main.to("#avb", {{scaleX: 1, duration: {half}, ease: "power1.out"}}, {round(t + half, 3)});')
    if mouth and any(f.get("open") for f in faces.values()):
        for a, z in mouth:
            js.append(f'main.set(".av-mouth", {{opacity: 1}}, {a});')
            js.append(f'main.set(".av-mouth", {{opacity: 0}}, {z});')
    return css, "\n  ".join(dom), "\n  ".join(js)


def alpha_page(events, faces, total, title="avatar", w=1920, h=1080, mouth=None):
    """A page with only the avatar on a transparent ground, for `hyperframes render --format mov` (ProRes 4444) and a
    Concat lane of its own."""
    css, dom, js = avatar_markup(events, faces, "alpha", w, h, mouth)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title>
<script src="gsap.min.js"></script>
<style>
  * {{ box-sizing: border-box; }} html, body {{ margin: 0; background: transparent; overflow: hidden; }}
  #root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; background: transparent; }}
  {css}
</style></head><body>
<div id="root" data-composition-id="main" data-width="{w}" data-height="{h}" data-start="0" data-duration="{total}">
  {dom}
</div>
<script>
  const main = gsap.timeline({{ paused: true }});
  {js}
  main.set({{}}, {{}}, {total});
  window.__timelines = window.__timelines || {{}}; window.__timelines["main"] = main;
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack", help="cut a comic sheet into a pack")
    p.add_argument("sheet")
    p.add_argument("--grid", required=True, help="columns x rows, e.g. 5x2")
    p.add_argument("--names", required=True, help="face names, row by row, comma separated")
    p.add_argument("--out", required=True)
    o = sub.add_parser("open", help="add open-mouth panels from a second sheet laid out like the pack's")
    o.add_argument("pack")
    o.add_argument("sheet")
    o.add_argument("--grid", required=True)
    o.add_argument("--keep-mouth", action="store_true", help="use the mx / my already in faces.json")
    t = sub.add_parser("shut", help="for faces drawn with the mouth already open: a squeezed-mouth closed frame, so talking shows")
    t.add_argument("pack")
    t.add_argument("faces", nargs="+")
    t.add_argument("--keep", type=float, default=SHUT_KEEP, help=f"share of the mouth's height kept (default {SHUT_KEEP})")
    c = sub.add_parser("check", help="validate a pack and redraw faces_check.png")
    c.add_argument("pack")
    a = ap.parse_args()
    if a.cmd == "open":
        faces = open_sheet(a.pack, a.sheet, a.grid, a.keep_mouth)
        print(f"✓ {len(faces)} open-mouth panels in {a.pack}; check the magenta mouth ellipses in faces_check.png")
    elif a.cmd == "shut":
        shut_faces(a.pack, a.faces, a.keep)
        print(f"✓ closed frames for {', '.join(a.faces)} in {a.pack}; look at the *_shut files next to the faces")
    elif a.cmd == "pack":
        faces = pack_sheet(a.sheet, a.grid, [n.strip() for n in a.names.split(",") if n.strip()], a.out)
        print(f"✓ {len(faces)} faces → {a.out}; set cx / cy in faces.json from faces_check.png, then run check")
    else:
        bad = check_pack(a.pack)
        if bad:
            sys.exit("✗ pack:\n  " + "\n  ".join(bad))
        draw_check(Path(a.pack))
        print(f"✓ {a.pack} ok; faces_check.png redrawn")


if __name__ == "__main__":
    main()
