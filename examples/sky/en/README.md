# Template: why is the sky blue? (Vox-style collage, no host)

Paste this sentence to your agent:

```
Follow the docs and make examples/sky/en into a film.
```

A science short of nine narration lines, about 46 seconds: the `collage` cut-paper look, three public-domain / CC0
photos and four diagrams drawn by code. It needs no account and no key.

## Two ways

### The quick way: use the premade narration (no waiting for the voice model)

```
python3 tools/examples/fetch_premade.py examples/sky/en
cp -R examples/sky/en/premade/. examples/sky/en/
python3 skills/ve-director/doc/scripts/doc_lint.py examples/sky/en/doc.json
python3 skills/ve-director/doc/scripts/doc_align.py examples/sky/en/doc.json
python3 skills/ve-director/doc/scripts/doc_lint.py examples/sky/en/doc.json --beats examples/sky/en/beats.json
python3 skills/ve-director/doc/scripts/doc_code.py examples/sky/en/doc.json --render
python3 skills/ve-director/doc/scripts/doc_cut.py examples/sky/en/doc.json --render
python3 tools/nightly/check.py examples/sky/en/doc.json examples/sky/en/cut_collage/output.mp4
```

- The first line downloads the narration from the GitHub Release, checks it against the SHA-256 in `premade.json`
  and unpacks it into `premade/`. If the download fails it prints the release page and the commands to unpack by hand.
- **Do not run F2 (voicing).** The premade narration is what F2 produces; what each step looks like when it went
  right is in `docs/FLOW.md`, F1 and F3 to F6.
- The timing step uses local speech transcription (the F0 install check in `docs/FLOW.md` looks for it).

### The full way: your own topic, your own voice

Follow `docs/FLOW.md` from F0 to F6. A new topic means new `lines` and `beats` in `doc.json`; changed narration is
reviewed by a person before it is voiced (F1).

## What you will see when it is done

- `cut_collage/output.mp4`: the film, its length inside the `seconds` range of `expected.json`.
- Beat 1 cover → prism photo → sunlight hitting air molecules → "shorter wave → more scattering" → red and blue
  bars → the blue rim seen from orbit → why not violet → sunset photo → the closing words "Rayleigh scattering".
- The F6 check exits with 0.

Everything the run makes is in `.gitignore`. To clear it: `git clean -ndX examples/sky/en` (look first),
`git clean -fdX examples/sky/en` (delete).

## Files

| File | What it is |
|---|---|
| `doc.json` | nine narration lines, nine beats, the `collage` theme |
| `facts.md` | every fact on screen and where it comes from (NASA Space Place, Rayleigh 1871, the Physics FAQ) |
| `assets/` | three photos and four icons; sources and licences in `assets/CREDITS.md` |
| `refs/narrator.wav`, `refs/narrator.txt` | the reference voice: a synthetic voice designed from a text description, not any real person (`refs/voice_cast.json`) |
| `premade.json` | where the premade narration is, its SHA-256 and size |
| `expected.json` | what a right result looks like: beats, lines, length range, narration fingerprint |

The Chinese version is in `examples/sky/zh`.
