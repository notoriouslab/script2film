# Script2Film

**English** · [繁體中文](./README.zh-TW.md)

From a script to a finished film, one stage at a time: script → voice → timing → pictures → assembly → publishing.
Each stage has a default tool and a file contract, so a tool can be swapped without touching the other stages.

> **Status.** The core flow (voice, timing, drawn scenes, assembly, check) runs on your own machine with no account
> and no API key. It was installed from an empty home folder and a fresh clone on 2026-11-17 and made the first example
> film; the steps and measured times are in [docs/INSTALL.md](./docs/INSTALL.md). It has only been verified on Apple
> Silicon Macs.

## Start here

- **Installing on a new machine:** [docs/INSTALL.md](./docs/INSTALL.md). About 30 minutes and about 7 GB of downloads
  the first time, most of it the voice step (`bash tools/doctor/setup_voice.sh`, 20 to 25 minutes, about 6 GB).
  `python3 tools/doctor/doctor.py` checks everything and prints the fix for each missing part. The Python packages go
  in `.venv`; the scripts switch to it by themselves, so you keep typing `python3`.
- **AI agents:** open this folder itself as the workspace (agents load `AGENTS.md` and the skills from the workspace
  root). [AGENTS.md](./AGENTS.md) holds the always-on rules, and the `script2film` skill
  ([skills/script2film/SKILL.md](./skills/script2film/SKILL.md)) is linked into `.agents/skills/` and
  `.claude/skills/`. On Windows the links need git `core.symlinks`.
- **The steps, with commands:** [docs/FLOW.md](./docs/FLOW.md).
- **Which agents have made a film from the documents alone** (Claude Code, Google Antigravity, and opencode with a
  local model or with DeepSeek), and what to do when one gets stuck: [docs/AGENT-TRIALS.md](./docs/AGENT-TRIALS.md).

## Examples

- [examples/coffee/](./examples/coffee/): the first film to make. Four lines in English, about 25 seconds, four
  scenes drawn by code. No account and no key.
- [examples/brewing/](./examples/brewing/): five lines in Chinese, about 23 seconds, with a generated shot and a
  lip-synced host (its README is in Chinese). Its `premade/` folder holds the generated files, so it also needs no
  account.

## The stages

| Stage | In → out | Default | Optional |
|---|---|---|---|
| Script | topic and material → `doc.json` (lines and beats) | written by hand from the format guide | an AI agent following the skill |
| Voice | lines → one audio file per line, then the joined narration | Qwen3-TTS, on your machine | your own recording |
| Timing | narration → `beats.json`, subtitles | mlx-whisper, on your machine | Groq, ElevenLabs Scribe |
| Pictures: drawn | beats and parameters → one mp4 per beat | the scene engine in `skills/ve-director/doc/` (27 scenes) | |
| Pictures: footage | photos and clips → the picture of a beat | photos with a licence record | VideoExpress, driven by `tools/ve-runner/` |
| Host | narration → a presenter video | no host | TalkingPhotos |
| Sound | beats → sound marks, music | the effects that ship in `assets/sfx/` (CC0, self-made, VideoExpress-generated); music composed by `tools/score/` | CC BY tracks (credit required); your own VideoExpress sounds (`tools/assets/gen_sfx_ve.py`) |
| Assembly | everything above → the film | `doc_cut.py --render` | Concat (recommended), for overlay layers (host in a side frame, keyword pills, chapter labels, photo credits) |
| Publishing | the film → a platform | upload by hand | YouTube API |

From voice to a rendered film, the defaults need no other editing software and no API key
(`tools/check-standalone.sh` checks this in a clean environment).

## What is where

| Path | What it is |
|---|---|
| `skills/script2film/` | the skill an agent follows to make an explainer film; it routes to `docs/FLOW.md` |
| `skills/ve-director/` | the storyboard skill for VideoExpress: plans a scene as a shot table, then renders checked prompts. Its rules live in `skills/ve-director/rules/` |
| `skills/ve-director/doc/` | doc mode: narrated explainer films. Narration, word timing, 27 drawn scenes, themes, fact checks, cutting. Start with its `README.md` |
| `tools/doctor/`, `tools/config/` | the install check, the voice setup (`setup_voice.sh`) and the per-machine settings file |
| `tools/tts/` | designing a voice, voiced lines for several characters, speaker similarity |
| `tools/nightly/`, `tools/checklist/`, `tools/qa/` | checks: the delivery check (`check.py`), the start and release checklists, frame-by-frame motion checks |
| `tools/ve-runner/` | runs a storyboard on VideoExpress in a browser and collects the clips |
| `tools/tp/` | makes a talking host on TalkingPhotos |
| `tools/assemble/`, `tools/concat/` | lays clips into a timeline; builds a Concat project from it |
| `tools/drama/` | cuts a lip-synced short drama (no narrator) from one timeline file, with or without Concat |
| `tools/score/` | composed background music that follows the picture, rendered offline from a SoundFont |
| `tools/assets/` | makes your own sound effects on your VideoExpress account; copies fonts and sounds from an older library |
| `tools/youtube/` | upload, schedule and retitle on your own channel |
| `tools/prompt-studio/` | Prompt Studio, a single-file HTML prompt builder for VideoExpress (the tool this repository started as) |
| `tools/agents/`, `tools/site/` | links the skills where each agent looks for them; builds the English website pages and the website copy of Prompt Studio |
| `examples/` | the two example films |
| `assets/` | the bundled sound effects (in git) and the two fonts (downloaded; see `assets/README.md`) |
| `docs/` | the documents above and the project website: home, tools, scenes and palettes, and the Prompt Studio page with an online copy (`docs/studio.html`); English pages in `docs/en/` |

## Requirements and accounts

It has only been verified on Apple Silicon Macs. The default transcription (mlx-whisper) runs only on Apple Silicon;
Windows, Linux and Intel Macs have not been tried (see "Not covered" in [docs/INSTALL.md](./docs/INSTALL.md)).

No account or key is needed for the core flow: voice, timing, drawn scenes, `doc_cut.py --render` and the check.
The optional parts use your own accounts: VideoExpress (generated shots, sound effects), TalkingPhotos (host), YouTube
(upload), and both a Groq and an ElevenLabs key for cloud transcription. Concat is a separate app you install. Each is
described where it is used in [docs/FLOW.md](./docs/FLOW.md).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Security issues: [SECURITY.md](./SECURITY.md).

## Licence

[MIT](./LICENSE). Where ideas, wording and assets came from, and the licence of every third-party component, is in
[NOTICE.md](./NOTICE.md).
