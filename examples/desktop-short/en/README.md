# Template: Claude Code Desktop in 35 seconds (tutorial, comic avatar host)

Paste this sentence to your agent:

```
Follow the docs and make examples/desktop-short/en into a film.
```

A six-line tutorial of about 34 seconds, hosted by a comic avatar instead of a talking host: 阿華, a made-up
character, peeks in at the start and the end and keeps a badge in the corner (`"avatar"` in `doc.json`). The app steps
are drawn by code with the `ui_steps` scene (simplified parts, not real screenshots). It needs no account and no key.

## Two ways

### The quick way: use the premade narration (no waiting for the voice model)

```
python3 tools/examples/fetch_premade.py examples/desktop-short/en
cp -R examples/desktop-short/en/premade/. examples/desktop-short/en/
python3 skills/ve-director/doc/scripts/doc_lint.py examples/desktop-short/en/doc.json
python3 skills/ve-director/doc/scripts/doc_align.py examples/desktop-short/en/doc.json
python3 skills/ve-director/doc/scripts/doc_lint.py examples/desktop-short/en/doc.json --beats examples/desktop-short/en/beats.json
python3 skills/ve-director/doc/scripts/doc_code.py examples/desktop-short/en/doc.json --render
python3 skills/ve-director/doc/scripts/doc_cut.py examples/desktop-short/en/doc.json --render
python3 tools/nightly/check.py examples/desktop-short/en/doc.json examples/desktop-short/en/cut_lecture-tech/output.mp4
```

- The first line downloads the narration from the GitHub Release, checks it against the SHA-256 in `premade.json`
  and unpacks it into `premade/`. If the download fails it prints the release page and the commands to unpack by hand.
- **Do not run F2 (voicing).** The premade narration is what F2 produces; what each step looks like when it went
  right is in `docs/FLOW.md`, F1 and F3 to F6.

### The full way: your own steps, your own voice, your own avatar

Follow `docs/FLOW.md` from F0 to F6. To use your own sticker pack, cut it with `doc_avatar.py pack` and change
`avatar.pack` in `doc.json` (format in `skills/ve-director/doc/README.md`, "Comic avatar host").

## What you will see when it is done

- `cut_lecture-tech/output.mp4`: the film, its length inside the `seconds` range of `expected.json`.
- Beat 1 cover with 阿華 peeking in from the left → sign in → Code, Local, empty folder → the one sentence typed in
  → "Packages → Fonts → Voice model → ✓ ready to go" → closing cover, 阿華 waves from the right. From beat 2 on, a small badge sits lower right.
- The F6 check exits with 0.

Everything the run makes is in `.gitignore`. To clear it: `git clean -ndX examples/desktop-short/en` (look first),
`git clean -fdX examples/desktop-short/en` (delete).

## Files

| File | What it is |
|---|---|
| `doc.json` | six narration lines, six code beats, the `lecture-tech` palette, the avatar moments |
| `facts.md` | where each step comes from (same steps as `examples/install-desktop`) |
| `../avatar/ahua/` | the sticker pack, shared by the zh and en versions (`doc_avatar.py` also looks one folder up) |
| `refs/narrator.wav`, `refs/narrator.txt` | the reference voice: a synthetic voice designed from a text description, not any real person (`refs/voice_cast.json`) |
| `premade.json` | where the premade narration is, its SHA-256 and size |
| `expected.json` | what a right result looks like: beats, lines, length range, narration fingerprint |

The Chinese version is in `examples/desktop-short/zh`.
