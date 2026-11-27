"""Host take on VideoExpress Lipsync Video (Old Algorithm) instead of TalkingPhotos: an English host in the small
circle (doc.json "pip") only.

  python3 tools/ve-runner/ve_host.py <project> --prefix Ep01 --look <look image> [--who "A man in a grey blazer"]
                                     [--parts 1 2] [--timeout 20] [--tol 0.3] [--dry-run] [--any-lang] [--any-size]

Run `doc_host.py split <project>/doc.json --max 290` first (VE takes up to 300 s of audio, so most narrations are one
part). Each host/parts/partK.mp3 and the look image are uploaded to the VE media library as <prefix>_partK /
<prefix>_look, sent through Lipsync Video with the prompt rewrite off, then downloaded to host/parts/partK.mp4 (an
older file is kept as partK.bak.mp4) and checked: video and sound present, length within --tol s of the mp3.
`doc_host.py join` then works as with TalkingPhotos.

host/ve_host.json keeps what was uploaded and sent, by content hash: a rerun does not upload or send the same part
again, it only waits and downloads. Exit 0: every part downloaded and checked; 1: a part failed (the message says which);
2: still processing after --timeout minutes (rerun to collect).

Tried 2026-11-24 (NOTES.md item 11): the clip is the audio's length and its sound is the audio itself; ready 4.5 to
6 minutes after sending. The user's verdict: good enough for an English host in the small circle; a full-screen host
and any Chinese host look clearly better from TalkingPhotos, hence the two stops. With the prompt rewrite on, the hands
froze at the chest for the whole clip.
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, hashlib, json, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VE_MAX = 300.0          # Import Audio: "The maximum audio duration 5 minutes (300 seconds)"
TOL_DEFAULT = 0.3       # the three trial clips came back 0.01-0.02 s longer than their audio
DEFAULT_WHO = "The presenter"
PROMPT = ("{who} talks to the camera in a calm, friendly way. Their head and body stay steady and centred, with only "
          "small natural nods. Their hands stay low and move only a little, naturally. They keep eye contact with the "
          "camera. Plain studio background. No text, no captions, no subtitles.")
BOXES = (("auto_enhance_prompt", False), ("talking_video_singing", False), ("shared", False),
         ("talking_video_loop_forward", True))


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe(path: Path) -> tuple[float, set[str]]:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json",
                          str(path)], capture_output=True, text=True)
    if out.returncode:
        return 0.0, set()
    j = json.loads(out.stdout)
    return float(j.get("format", {}).get("duration", 0)), {s["codec_type"] for s in j.get("streams", [])}


def lang_stop(doc: dict, any_lang: bool) -> str | None:
    """Why not to send (a Chinese or unmarked-non-English doc), or None."""
    lang = str(doc.get("lang", "zh")).lower()
    if any_lang or lang.startswith("en"):
        return None
    return (f"✗ doc.json lang is {lang!r}: VE lip sync was clearly behind TalkingPhotos for Chinese (2026-11-24), so the "
            "host goes through tools/tp/tp_host.py. Pass --any-lang to send anyway.")


def full_screen_stop(doc: dict, any_size: bool) -> str | None:
    """Why not to send when the host also fills the screen (a beat playing a host/ take in sync), or None."""
    big = [b["id"] for b in doc.get("beats", []) if b.get("source") == "clip" and b.get("clip_sync")
           and str(b.get("clip", "")).startswith("host/")]
    if any_size or not big:
        return None
    return (f"✗ the host fills the screen in {', '.join(big)}: a full-screen host looked clearly better from TalkingPhotos "
            "(2026-11-24), so use tools/tp/tp_host.py; VE is for the small circle only. Pass --any-size to send anyway.")


def prompt_for(who: str | None) -> str:
    return PROMPT.format(who=(who or DEFAULT_WHO).strip().rstrip("."))


def wanted_parts(P: Path, only: list[int] | None) -> list[dict]:
    """parts.json entries to send, each with its mp3 and length; stops on a missing file or a part over VE_MAX."""
    pj = P / "host/parts.json"
    if not pj.exists():
        sys.exit(f"✗ {pj} missing: run doc_host.py split <project>/doc.json --max 290 first")
    parts = json.loads(pj.read_text(encoding="utf-8"))
    if only:
        unknown = set(only) - {p["k"] for p in parts}
        if unknown:
            sys.exit(f"✗ --parts {sorted(unknown)} not in {pj}")
        parts = [p for p in parts if p["k"] in only]
    out = []
    for p in parts:
        mp3 = P / f"host/parts/part{p['k']}.mp3"
        if not mp3.exists():
            sys.exit(f"✗ {mp3} missing: run doc_host.py split again")
        d, _ = probe(mp3)
        if d > VE_MAX:
            sys.exit(f"✗ {mp3.name} is {d:.1f}s; VE takes at most {VE_MAX:g}s: split with --max 290")
        out.append({**p, "mp3": mp3, "seconds": d})
    return out


def check_take(mp4: Path, seconds: float, tol: float) -> str | None:
    """What is wrong with a downloaded take, or None."""
    d, kinds = probe(mp4)
    if not {"video", "audio"} <= kinds:
        return f"{mp4.name}: streams {sorted(kinds)}, needs video and audio"
    if abs(d - seconds) > tol:
        return f"{mp4.name}: {d:.2f}s against {seconds:.2f}s of audio (more than {tol:g}s apart)"
    return None


def place(src: Path, dst: Path):
    """src → dst; an older dst is kept as <name>.bak.mp4."""
    if dst.exists():
        dst.replace(dst.with_suffix(".bak.mp4"))
    shutil.move(str(src), dst)


def modal_js(body: str) -> str:
    """JS run against the top visible .bbm-modal (the Lipsync dialog, or the audio dialog above it) as `m`."""
    return ("(arg) => { const m=[...document.querySelectorAll('.bbm-modal')].filter(e=>e.getBoundingClientRect().width>0)"
            ".pop(); if(!m) throw new Error('no dialog open'); " + body + " }")


def send(ve, part: dict, look_id: int, audio_id: int, prompt: str, aspect: str, dry: bool) -> str | None:
    """One Lipsync Video job; returns its library uuid (None on --dry-run)."""
    import ve_runner as V
    p = ve.page
    ve.open_app()
    nt = p.locator("text=Not today")    # the two-factor reminder sits over the cards
    if nt.count() and nt.first.is_visible():
        nt.first.click()
    p.locator("text=Lipsync Video(Old Algorithm").first.click()
    p.wait_for_selector("text=Reverse for smoother video", state="visible", timeout=15_000)
    p.evaluate(modal_js("const b=[...m.querySelectorAll('button')].find(e=>e.innerText.trim().replace(/\\s+/g,' ')===arg);"
                        " if(b) b.setAttribute('data-s2f-click','1');"), "Landscape 16:9" if aspect == "16:9" else "Vertical 9:16")
    if p.locator("[data-s2f-click]").count():
        ve.click_marked()
    ve.use_from_library(look_id, "Images")
    for name, on in BOXES:
        state = modal_js("const e=m.querySelector('input[name='+arg[0]+']'); if(!e) return null;"
                         " if(arg[1]!==null&&e.checked!==arg[1]) e.setAttribute('data-s2f-click','1'); return e.checked;")
        if p.evaluate(state, [name, on]) is not on and p.locator("[data-s2f-click]").count():
            ve.click_marked()  # real click: VE ignores a scripted el.click() on several controls since 2026-11-25
            p.wait_for_timeout(300)
        got = p.evaluate(state, [name, None])
        if got is not on:
            ve.shot_png(f"part{part['k']}_box_{name}")
            raise RuntimeError(f"checkbox {name} is {got}, wanted {on}")
    p.evaluate(modal_js("const t=m.querySelector('#opt_video_prompt'); t.value=arg;"
                        " t.dispatchEvent(new Event('input',{bubbles:true})); t.dispatchEvent(new Event('change',{bubbles:true}));"),
               prompt)
    p.evaluate(modal_js("const b=[...m.querySelectorAll('button')].filter(e=>e.getBoundingClientRect().width>0"
                        "&&e.innerText.trim()==='Create Video').pop(); if(!b) throw new Error('no Create Video'); b.setAttribute('data-s2f-click','1');"))
    ve.click_marked()
    p.wait_for_selector("text=Create Talking Video - Create Audio", state="visible", timeout=15_000)
    p.locator("a:visible:text-is('Import Audio')").first.click()     # tabs switch only on a real mouse click
    p.locator("button.button-select-file:visible").first.click()
    ve.open_folder("Audio")
    sel = f'.library-item[data-ident="{audio_id}"]'
    p.wait_for_selector(sel, state="attached", timeout=15_000)
    p.locator(sel).first.click(force=True)
    p.wait_for_timeout(500)
    p.evaluate("""() => { const b=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Choose'
                          &&b.getBoundingClientRect().width>0).pop(); if(!b) throw new Error('no Choose'); b.setAttribute('data-s2f-click','1'); }""")
    ve.click_marked()
    p.wait_for_timeout(2500)
    ve.shot_png(f"part{part['k']}_audio_chosen")
    if dry:
        ve.log(f"part{part['k']}: dry run, stopped before Create Talking Video")
        return None
    before = {x["id"] for x in ve.library(V.VID_CAT, "", 20)}
    ve.wait_for_slot()
    p.evaluate(modal_js("const b=[...m.querySelectorAll('button')].filter(e=>e.getBoundingClientRect().width>0"
                        "&&e.innerText.trim()==='Create Talking Video').pop(); if(!b) throw new Error('no Create Talking Video');"
                        " b.setAttribute('data-s2f-click','1');"))
    ve.click_marked()
    for _ in range(12):
        time.sleep(5)
        new = [x for x in ve.library(V.VID_CAT, "", 20) if x["id"] not in before]
        if len(new) == 1:
            ve.log(f"part{part['k']}: sent, library item {new[0]['id']}")
            return new[0]["uuid"]
        if len(new) > 1:
            raise RuntimeError(f"part{part['k']}: several new videos appeared at once {[x['id'] for x in new]}; "
                               "is someone else sending on this account?")
    ve.shot_png(f"part{part['k']}_not_sent")
    raise RuntimeError(f"part{part['k']}: no new video in My AI Videos within 60 s (alerts: {ve.alerts()})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--prefix", required=True, help="media library name prefix, e.g. Ep01")
    ap.add_argument("--look", required=True, help="the look image (a file; the same rules as for TalkingPhotos)")
    ap.add_argument("--who", help='who is on screen, for the prompt, e.g. "A man in a grey blazer"')
    ap.add_argument("--prompt", help="the whole Lipsync prompt instead of the built-in one (e.g. a side-angle host who "
                                     "looks off camera); --who is then ignored")
    ap.add_argument("--parts", type=int, nargs="*", help="only these parts (default: all of parts.json)")
    ap.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"])
    ap.add_argument("--timeout", type=int, default=20, help="minutes to wait for the takes after sending")
    ap.add_argument("--tol", type=float, default=TOL_DEFAULT, help="allowed difference between take and audio (s)")
    ap.add_argument("--dry-run", action="store_true", help="upload and fill in the dialogs, stop before sending")
    ap.add_argument("--any-lang", action="store_true", help="send a non-English narration too")
    ap.add_argument("--any-size", action="store_true", help="send even when the host also fills the screen")
    ap.add_argument("--skip-checklist", help="run even if the opening checklist fails: give the reason")
    a = ap.parse_args()
    P = Path(a.project).resolve()
    doc = json.loads((P / "doc.json").read_text(encoding="utf-8")) if (P / "doc.json").exists() else {}
    for msg in (lang_stop(doc, a.any_lang), full_screen_stop(doc, a.any_size)):
        if msg:
            sys.exit(msg)
    look = Path(a.look).resolve()
    if not look.exists():
        sys.exit(f"✗ look image {look} missing")
    parts = wanted_parts(P, a.parts)
    sys.path.insert(0, str(HERE.parent / "checklist"))
    import checklist
    checklist.gate(P, "start", a.skip_checklist, "ve")

    import ve_runner as V
    from playwright.sync_api import sync_playwright
    state_f = P / "host/ve_host.json"
    state = json.loads(state_f.read_text(encoding="utf-8")) if state_f.exists() else {"uploads": {}, "sent": {}}
    save = lambda: state_f.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")  # noqa: E731
    up = P / "host/ve_upload"
    up.mkdir(parents=True, exist_ok=True)
    run_dir = up / time.strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir()
    prompt = a.prompt.strip() if a.prompt else prompt_for(a.who)
    todo = [p for p in parts if state["sent"].get(f"part{p['k']}", {}).get("audio_sha256") != sha256(p["mp3"])]
    if todo:
        with sync_playwright() as pw:
            ctx = V.launch_browser(pw, V.HERE / ".profile")
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            ve = V.VE(page, run_dir, step=False, aspect=a.aspect)
            try:
                ve.open_app()

                def uploaded(src: Path, name: str, folder: str) -> int:
                    h = sha256(src)
                    hit = state["uploads"].get(h)
                    if hit:
                        return hit
                    copy = up / f"{name}{src.suffix.lower()}"
                    shutil.copyfile(src, copy)
                    state["uploads"][h] = ve.upload_file(copy, folder)
                    save()
                    return state["uploads"][h]

                audio = {p["k"]: uploaded(p["mp3"], f"{a.prefix}_part{p['k']}", "Audio") for p in todo}
                look_id = uploaded(look, f"{a.prefix}_look", "Images")
                for p in todo:
                    t0 = time.time()
                    uuid = send(ve, p, look_id, audio[p["k"]], prompt, a.aspect, a.dry_run)
                    if uuid:
                        state["sent"][f"part{p['k']}"] = {"video_uuid": uuid, "audio_sha256": sha256(p["mp3"]),
                                                          "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
                        save()
            except Exception as e:  # noqa: BLE001
                ve.shot_png("failed")
                sys.exit(f"✗ {e} (screenshots in {run_dir})")
            finally:
                ctx.close()
    if a.dry_run:
        print(f"dry run done: screenshots in {run_dir}")
        return
    want = [{"label": f"part{p['k']}", **state["sent"][f"part{p['k']}"]} for p in parts]
    sub = run_dir / "submitted.json"
    sub.write_text(json.dumps(want, indent=1), encoding="utf-8")
    dl = run_dir / "takes"
    subprocess.run([sys.executable, str(HERE / "ve_collect.py"), "--submitted", str(sub), "--out", str(dl),
                    "--wait", str(a.timeout)])
    bad, waiting = [], []
    for p in parts:
        got = dl / f"part{p['k']}.mp4"
        if not got.exists():
            waiting.append(f"part{p['k']}")
            continue
        if err := check_take(got, p["seconds"], a.tol):
            bad.append(err)
            continue
        dst = P / f"host/parts/part{p['k']}.mp4"
        place(got, dst)
        print(f"{dst.name} ok ({probe(dst)[0]:.2f}s for {p['seconds']:.2f}s of audio)")
    if bad:
        sys.exit("✗ " + "; ".join(bad))
    if waiting:
        print(f"still processing: {', '.join(waiting)}; run the same command again to collect")
        sys.exit(2)
    print("all done: next, doc_host.py join <project>/doc.json")


if __name__ == "__main__":
    main()
