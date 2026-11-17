"""Shared bits for doc-mode scripts: project loading, tool locations, tokens.

Every script takes the project's doc.json; all paths inside it are relative to the project folder.
External tools are found through environment variables (no machine paths in this repo). The tool variables also work
under their old names without the S2F_ prefix (QWEN_TTS_DIR, QWEN_TTS_MODELS, MLX_WHISPER_DIR); when both are set, the
S2F_ name wins (s2f_env).

Any of these can be written once in ~/.config/script2film/config.json instead of exported (same names as the keys;
tools/config/s2f_config.py, loaded at the top of every script that reads them). Order: environment, then the config file,
then the default. `python3 tools/config/s2f_config.py --show` prints each value and where it came from;
`python3 tools/doctor/doctor.py` checks the machine. The starter template (formats/vox-host/make_doc_template.py) is
copied into projects, so it finds this repo by itself (find_s2f: S2F_DIR in the environment, else its own location):
S2F_DIR from the config file does not reach that one step.

Required:
  S2F_QWEN_TTS_DIR     qwen3-tts folder with its .venv (doc_tts.py runs inside it)
  S2F_MLX_WHISPER_DIR  a folder whose .venv has mlx-whisper (Apple Silicon). doc.json "asr": "local" (the default)
                       transcribes with it: picking TTS candidates (doc_voice) and word timing (doc_align); no keys, no
                       audio sent out
Optional:
  S2F_QWEN_TTS_MODELS  the Qwen3-TTS models folder; default: $S2F_QWEN_TTS_DIR/../_models (qwen_models_dir)
  S2F_ASSETS           the bundled asset layer (fonts/, sfx/ with manifest.json); default: the repo root's assets/
  S2F_ASSETS_LOCAL     user asset layer, same layout, looked in first (your own sounds)
  S2F_HF_BIN           a HyperFrames package folder or entry script; default: the repo root's node_modules/hyperframes
                       (`npm ci`), run with a Node 22+ `node` from PATH
  S2F_SCRIBE_MODEL     the ElevenLabs Scribe model for "asr": "cloud"; default: scribe_v2
Only with doc.json "asr": "cloud":
  GROQ_API_KEY         picking TTS candidates with Groq; when Groq is rate-limited and S2F_MLX_WHISPER_DIR is set, the
                       rest are transcribed locally
  ELEVENLABS_API_KEY   word timing with ElevenLabs Scribe (ELEVEN_API_KEY also works); without a key, or when Scribe
                       fails, mlx-whisper times the words if S2F_MLX_WHISPER_DIR is set. The whole narration audio is
                       sent to ElevenLabs
  Keys come from the environment first, then from ~/.config/script2film/secrets.json (JSON, the key names as above).
"""
import sys as _sys, pathlib as _pl   # 設定檔：tools/config/s2f_config.py
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[4] / "tools/config"))
import s2f_config; s2f_config.load()
import hashlib, json, os, re, shutil, subprocess, sys, uuid
from pathlib import Path

SKILL_DOC = Path(__file__).resolve().parents[1]


def _load_lexicon():
    """The shared pronunciation table module (tools/tts/lexicon.py), loaded by path under its own name: an episode or
    series folder may have a lexicon.py of its own on sys.path."""
    import importlib.util
    if "s2f_lexicon" in sys.modules:
        return sys.modules["s2f_lexicon"]
    spec = importlib.util.spec_from_file_location("s2f_lexicon", Path(__file__).resolve().parents[4] / "tools/tts/lexicon.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["s2f_lexicon"] = mod
    spec.loader.exec_module(mod)
    return mod


lexicon = _load_lexicon()


def read_json(path, missing=""):
    """A JSON file the script reads in (doc.json, beats.json, the previous episode's doc.json ...). A missing or
    unreadable file, or one that is not valid JSON, stops the script with one line naming the file and the reason (JSON
    errors with their line and column), not a traceback. missing: a hint added when the file does not exist."""
    p = Path(path).resolve()
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        sys.exit(f"✗ {p}: no such file" + (f" ({missing})" if missing else ""))
    except UnicodeDecodeError:
        sys.exit(f"✗ {p}: not UTF-8 text")
    except OSError as e:
        sys.exit(f"✗ {p}: cannot read it ({e.strerror or e.__class__.__name__})")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"✗ {p}: not valid JSON (line {e.lineno}, column {e.colno}: {e.msg})")


def read_beats(path):
    """A beats.json from doc_align (read_json; a missing file says to run doc_align.py first, one without a "beats"
    list stops too)."""
    B = read_json(path, "run doc_align.py first")
    if not isinstance(B, dict) or not isinstance(B.get("beats"), list):
        sys.exit(f"✗ {Path(path).resolve()}: no \"beats\" list (not a beats.json from doc_align.py)")
    return B


def load(doc_path):
    """doc.json → (the doc, the project folder); a bad file stops the script with one line (read_json)."""
    p = Path(doc_path).resolve()
    return read_json(p), p.parent


def lines_hash(doc, fmt="doc"):
    """The narration's fingerprint (12 hex characters): which version of the narration an answer or an approval was
    given for; change any line and it changes. fmt "doc": lines[].text; "book" (day.json): narration[].text.
    tools/checklist (its answers) and doc_approval (script approval) share this one definition."""
    texts = [l["text"] for l in doc.get("lines", [])] if fmt == "doc" else [x["text"] for x in doc.get("narration", [])]
    return hashlib.sha256("\n".join(texts).encode("utf-8")).hexdigest()[:12]


def series_of(P):
    """The series settings for the episode folder P: the series.json one level up, or None (a single episode).
    Same lookup as tools/checklist/items.series_cfg (a test there holds the two together)."""
    p = Path(P).resolve().parent / "series.json"
    if not p.exists():
        return None
    s = json.loads(p.read_text(encoding="utf-8"))
    return s if isinstance(s, dict) else None


SUB_LANGS = ("zh", "en")


def sub_lang(doc):
    """The narration's language as a caption code: "en" for English, else "zh" (doc.json "lang" may be "zh-Hant")."""
    return "en" if str(doc.get("lang", "zh")).lower().startswith("en") else "zh"


def burn_lang(doc, series):
    """Which language the film burns in: doc.json "subs"."burn", else the series', else None (not set: the old rules)."""
    for src in (doc, series or {}):
        subs = src.get("subs")
        if isinstance(subs, dict) and subs.get("burn"):
            return subs["burn"]
    return None


def subs_problems(doc, series):
    """What is wrong with the subtitle settings, one line each ([] when fine). FORMAT §4d point 4:
    "subs": {"burn": "<lang>"} in series.json (an episode's doc.json overrides it) names the one language burned in."""
    out, lang, burn = [], sub_lang(doc), burn_lang(doc, series)
    for name, src in (("doc.json", doc), ("series.json", series or {})):
        if "subs" in src and not isinstance(src["subs"], dict):
            return [f'subs in {name} must be an object such as {{"burn": "zh"}}']
    if lang == "en" and doc.get("en"):
        out.append('English narration needs no en field (en is the English translation of Chinese narration)')
    if burn is None:
        return out
    if burn not in SUB_LANGS:
        return out + [f"subs.burn must be zh or en: {burn!r}"]
    if "en_layer" in doc:
        out.append("keep only one of subs.burn and en_layer (en_layer is the old form)")
    if lang == "en" and burn == "zh" and not doc.get("zh"):
        out.append('subs.burn is zh, but the script has no Chinese translation ("zh" field)')
    if lang == "zh" and burn == "en":
        out.append("burning only English subtitles over Chinese narration is not supported yet")
    return out


def subtitle_plan(doc, series):
    """{"burn": lang or None, "main": "narration" | "zh", "second": bool}: what the main (burned) subtitle shows and
    whether a second line is laid under it. Not set (burn None) keeps the old rules: the Chinese translation is the main
    subtitle when the doc has "zh", and a second line is burned when there is "en" or "zh" unless "en_layer" is false.
    Set: the one language only, no second line. Raises ValueError on settings subs_problems rejects."""
    bad = subs_problems(doc, series)
    if bad:
        raise ValueError("; ".join(bad))
    burn = burn_lang(doc, series)
    if burn is None:
        return {"burn": None, "main": "zh" if doc.get("zh") else "narration",
                "second": bool((doc.get("en") or doc.get("zh")) and doc.get("en_layer", True))}
    return {"burn": burn, "main": "narration" if burn == sub_lang(doc) else "zh", "second": False}


def spoken_text(doc, line):
    """The string sent to speech synthesis: the line's own "tts" (or its text) with the shared pronunciation table
    (tools/tts/lexicon.json) applied on top, so a per-episode "tts" cannot bypass the table."""
    return lexicon.spoken(line.get("tts") or line["text"], doc["lang"])


def line_key(doc, P, line):
    """Name of a line's TTS candidates: a hash of everything that changes the synthesis (spoken text, language, reference
    voice). Inserting or deleting a line no longer shifts other lines onto stale takes, and an edited line gets new takes
    (2026-10-28; the old <NN>_<seed> names went stale when a script was restructured)."""
    v = doc["voice"]
    h = hashlib.sha256()
    for part in (doc["lang"], spoken_text(doc, line), (P / v["ref_text"]).read_text(encoding="utf-8").strip()):
        h.update(part.encode("utf-8") + b"\0")
    h.update((P / v["ref_wav"]).read_bytes())
    return h.hexdigest()[:12]


def s2f_env(name):
    """S2F_<name> when it is set (non-empty), otherwise the old name <name>; None when neither is set. name is given
    without the prefix (s2f_env("MLX_WHISPER_DIR"))."""
    return os.environ.get(f"S2F_{name}") or os.environ.get(name) or None


def env_dir(name, default=None):
    """The folder in S2F_<name> (or the old name <name>, read by s2f_env), else default; stops when unset or missing."""
    v = s2f_env(name) or default
    if not v:
        sys.exit(f"✗ set S2F_{name} (the old name {name} also works) (see doc_common.py)")
    d = Path(v).expanduser()
    if not d.exists():
        used = f"S2F_{name}" if os.environ.get(f"S2F_{name}") else name
        sys.exit(f"✗ {used}={d} does not exist")
    return d


def has_local_asr():
    """True when the local transcription folder (S2F_MLX_WHISPER_DIR, or the old name MLX_WHISPER_DIR) is set."""
    return bool(s2f_env("MLX_WHISPER_DIR"))


def qwen_models_dir():
    """Folder of the Qwen3-TTS models: S2F_QWEN_TTS_MODELS (old name QWEN_TTS_MODELS) when set, otherwise
    <S2F_QWEN_TTS_DIR or QWEN_TTS_DIR>/../_models; stops when neither the models nor the qwen3-tts folder is set."""
    models = s2f_env("QWEN_TTS_MODELS")
    if models:
        return Path(models).expanduser()
    tts = s2f_env("QWEN_TTS_DIR")
    if not tts:
        sys.exit("✗ set S2F_QWEN_TTS_DIR (the old name QWEN_TTS_DIR also works)")
    return Path(tts).expanduser().parent / "_models"


SECRET_FILES = ("~/.config/script2film/secrets.json",)


def secret(name):
    """The value of name in the secrets file (SECRET_FILES); None when the file is missing or does not have it."""
    for f in SECRET_FILES:
        p = Path(f).expanduser()
        if p.exists():
            data = json.loads(p.read_text())
            if name in data:
                return data[name]
    return None


def eleven_key():
    """ElevenLabs key: env ELEVENLABS_API_KEY, then env ELEVEN_API_KEY, then the same two names in the secrets files
    (secret()); None when none of them is set."""
    for name in ("ELEVENLABS_API_KEY", "ELEVEN_API_KEY"):
        if os.environ.get(name):
            return os.environ[name]
    return secret("ELEVENLABS_API_KEY") or secret("ELEVEN_API_KEY")


def groq_key():
    key = os.environ.get("GROQ_API_KEY") or secret("GROQ_API_KEY")
    if not key:
        sys.exit("✗ set GROQ_API_KEY (or put it in ~/.config/script2film/secrets.json)")
    return key


def asr_mode(doc):
    """doc.json "asr": "local" (default: mlx-whisper on this machine, no keys, no audio sent out) or "cloud" (Groq picks
    takes, ElevenLabs Scribe times the words; each falls back to local when it fails or has no key)."""
    mode = doc.get("asr", "local")
    if mode not in ("local", "cloud"):
        sys.exit(f'✗ doc.json "asr" must be "local" or "cloud", not {mode!r}')
    return mode


def need_local_asr():
    """Stop with how to set it up when "asr" is local and S2F_MLX_WHISPER_DIR (or the old MLX_WHISPER_DIR) is not set."""
    if not has_local_asr():
        sys.exit('✗ "asr": "local" transcribes on this machine: set S2F_MLX_WHISPER_DIR (the old name MLX_WHISPER_DIR also works) to a '
                 'folder whose .venv has mlx-whisper (python3 -m venv .venv && .venv/bin/pip install mlx-whisper)')


LOCAL_MODEL = "mlx-community/whisper-large-v3-turbo"
LOCAL_ASR = """import json, sys, mlx_whisper
lang, words, paths = sys.argv[1], sys.argv[2] == "1", sys.argv[3:]
out = {}
for p in paths:
    r = mlx_whisper.transcribe(p, path_or_hf_repo=%r, language=lang, word_timestamps=words)
    out[p] = {"segments": [{"text": s["text"], "start": float(s["start"]), "end": float(s["end"]),
                            "words": [{"word": w["word"], "start": float(w["start"]), "end": float(w["end"])}
                                      for w in s.get("words", [])]} for s in r["segments"]]} if words else r["text"]
print(json.dumps(out, ensure_ascii=False))
""" % LOCAL_MODEL


def local_asr(paths, lang, words=False):
    """Transcribe on this machine with mlx-whisper (one process, the model loads once). Returns {path: text}, or with
    words=True {path: {"segments": [{"words": [{"word", "start", "end"}]}], ...}}. zh text comes back Traditional.
    None when S2F_MLX_WHISPER_DIR (or the old MLX_WHISPER_DIR) is not set (the caller keeps its old behaviour)."""
    if not has_local_asr():
        return None
    py = env_dir("MLX_WHISPER_DIR") / ".venv/bin/python"
    r = subprocess.run([str(py), "-c", LOCAL_ASR, lang, "1" if words else "0", *map(str, paths)],
                       capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or [""])[-1]
    try:
        out = json.loads(last) if r.returncode == 0 else None
    except ValueError:
        out = None
    if out is None:   # say why: the transcriber's own stderr (a missing model, out of memory) was swallowed before
        why = "\n".join((r.stderr or "").strip().splitlines()[-15:])
        sys.exit(f"✗ local transcription failed (exit {r.returncode}, {py}):\n{why}")
    if lang == "zh":
        from opencc import OpenCC
        s2t = OpenCC("s2twp").convert
        for p, v in out.items():
            if words:
                for seg in v["segments"]:
                    seg["text"] = s2t(seg.get("text", ""))
                    for w in seg.get("words", []):
                        w["word"] = s2t(w["word"])
            else:
                out[p] = s2t(v)
    return {Path(p): v for p, v in out.items()}


def tokens(text, lang):
    """Same rule as tok() in lib/lib.js: CJK characters (zh) or lower-case words (en)."""
    if lang == "zh":
        return [c for c in text if re.match(r"[一-鿿0-9A-Za-z]", c)]
    return re.sub(r"[^a-z0-9' ]+", " ", text.lower().replace("’", "'")).split()


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


def sh(*a, **kw):
    subprocess.run([str(x) for x in a], check=True, **kw)


REPO = SKILL_DOC.parents[2]
NODE_MIN = 22
ASSET_HINT = ("the sound effects ship with the repository (restore them with `git checkout -- assets/sfx`); the font files "
              "are not in git, download them as assets/README.md says (`python3 tools/doctor/doctor.py` prints the commands)")


MIN_SUB_FAIL_S, MIN_SUB_WARN_S = 0.5, 0.8   # a subtitle up for less cannot be read; from HyperFrames' embedded-captions skill (NOTICE.md)


def parse_srt(text):
    """SRT text → [{"start", "end", "text"}] in seconds (the reverse of doc_cut.srt)."""
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().split("\n")
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", lines[1]) if len(lines) > 1 else None
        if not m:
            continue
        t = [int(x) for x in m.groups()]
        cues.append({"start": t[0] * 3600 + t[1] * 60 + t[2] + t[3] / 1000, "end": t[4] * 3600 + t[5] * 60 + t[6] + t[7] / 1000,
                     "text": "\n".join(lines[2:]).strip()})
    return cues


def short_cues(cues):
    """Subtitles on screen too briefly to read → (under MIN_SUB_FAIL_S, MIN_SUB_FAIL_S up to MIN_SUB_WARN_S), each
    [{"start", "dur", "text"}]. The first list fails the output check (tools/nightly/check.py); the second is only listed."""
    fail, warn = [], []
    for c in cues:
        d = round(c["end"] - c["start"], 3)
        if d < MIN_SUB_WARN_S:
            (fail if d < MIN_SUB_FAIL_S else warn).append({"start": round(c["start"], 3), "dur": d, "text": c["text"]})
    return fail, warn


def assets(kind):
    """Folders to look in for an asset kind ("fonts", "sfx"), in order: the user layer $S2F_ASSETS_LOCAL/<kind> (only when
    set and present: sounds you made or found yourself), then the bundled layer $S2F_ASSETS/<kind> (default: the repo
    root's assets/: the sounds that ship with the repository (Kenney CC0, 自製, the author's VideoExpress ones) and the
    Noto fonts you downloaded)."""
    out = []
    loc = os.environ.get("S2F_ASSETS_LOCAL")
    if loc and (Path(loc).expanduser() / kind).is_dir():
        out.append(Path(loc).expanduser() / kind)
    out.append(Path(os.environ.get("S2F_ASSETS") or REPO / "assets").expanduser() / kind)
    return out


def asset(kind, name):
    """The first <folder>/<name> on disk among assets(kind); stop with how to fill the library when there is none."""
    dirs = assets(kind)
    for d in dirs:
        if (d / name).exists():
            return d / name
    sys.exit(f"✗ {kind}/{name} not found in {', '.join(map(str, dirs))}: {ASSET_HINT} (in {REPO}), "
             f"or set S2F_ASSETS / S2F_ASSETS_LOCAL")


def gsap_file():
    """GSAP for the rendered pages: the repo root's node_modules/gsap/dist/gsap.min.js (root package.json, `npm ci`).
    Copied next to every page as gsap.min.js, so rendering needs no network."""
    f = REPO / "node_modules/gsap/dist/gsap.min.js"
    if not f.is_file():
        sys.exit(f"✗ GSAP not found ({f}): run `npm ci` in {REPO}")
    return f


def log_tail(path, n=10):
    """The last n non-blank lines of a log, for the message of a step that stops; "" when the file cannot be read."""
    try:
        lines = [l.rstrip() for l in Path(path).read_text(errors="ignore").splitlines() if l.strip()]
    except OSError:
        return ""
    return "\n".join(lines[-n:])


def hf_package():
    """HyperFrames (entry script, package folder): $S2F_HF_BIN (the package folder or its entry script), else the repo
    root's node_modules/hyperframes (installed by the root package.json, `npm ci`). The entry is the package.json "bin"."""
    hint = os.environ.get("S2F_HF_BIN")
    if hint:
        h = Path(hint).expanduser().resolve()
        if not h.exists():
            sys.exit(f"✗ S2F_HF_BIN={h} does not exist")
        roots = [h] if h.is_dir() else list(h.parents)
    else:
        roots = [REPO / "node_modules/hyperframes"]
    for root in roots:
        pj = root / "package.json"
        if not pj.exists():
            continue
        bin_ = json.loads(pj.read_text(encoding="utf-8")).get("bin")
        bin_ = bin_ if isinstance(bin_, str) else (bin_ or {}).get("hyperframes")
        if bin_ and (root / bin_).exists():
            return (root / bin_).resolve(), root.resolve()
    sys.exit(f"✗ HyperFrames not found ({hint and f'S2F_HF_BIN={hint}' or REPO / 'node_modules/hyperframes'}): "
             f"run `npm ci` in {REPO}, or set S2F_HF_BIN to a hyperframes package folder")


def node_bin():
    """`node` on PATH, checked to be Node 22 or newer (HyperFrames' engines field)."""
    node = shutil.which("node")
    if not node:
        sys.exit(f"✗ HyperFrames needs Node {NODE_MIN} or newer; no `node` on PATH")
    v = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    m = re.match(r"v?(\d+)\.", v)
    if not m or int(m.group(1)) < NODE_MIN:
        sys.exit(f"✗ HyperFrames needs Node {NODE_MIN} or newer; `node` on PATH ({node}) is {v or 'unknown'}")
    return node


def hyperframes(command, project_dir, *args, stdout=None):
    """Run the HyperFrames CLI: `hyperframes <command> <project_dir> [args]`. Runs in the package folder, so the project
    folder and the value after -o / --output are passed as absolute paths. Render runs set
    PRODUCER_BROWSER_GPU_MODE=hardware unless it is already set; HYPERFRAMES_RUN_ID gets s2f-<uuid> unless already set.
    Returns the subprocess.CompletedProcess and never raises on a non-zero exit: the caller checks returncode. With a
    file for stdout, stderr goes into it too."""
    entry, root = hf_package()
    node = node_bin()
    fwd, it = [], iter(args)
    for a in it:
        fwd.append(str(a))
        if str(a) in ("-o", "--output"):
            nxt = next(it, None)
            if nxt is not None:
                fwd.append(str(Path(nxt).expanduser().resolve()))
    env = dict(os.environ)
    env["HYPERFRAMES_RUN_ID"] = env.get("HYPERFRAMES_RUN_ID") or f"s2f-{uuid.uuid4()}"
    if command == "render":
        env["PRODUCER_BROWSER_GPU_MODE"] = env.get("PRODUCER_BROWSER_GPU_MODE") or "hardware"
    return subprocess.run([node, str(entry), command, str(Path(project_dir).expanduser().resolve()), *fwd], cwd=root,
                          env=env, stdout=stdout, stderr=subprocess.STDOUT if stdout is not None else None)
