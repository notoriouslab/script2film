# Changelog

## 1.0.0 (2026-11-17)

The first public release of Script2Film: from a script to a finished, checked explainer film on your own Mac, with no
account and no API key for the core flow.

- **Core flow.** Script (`doc.json`) → voice (Qwen3-TTS, local) → word timing and subtitles (mlx-whisper, local) →
  27 scenes drawn by code → cut (`doc_cut.py --render`) → delivery check (`tools/nightly/check.py`: loudness, peak,
  length, a frame sheet, and reports of stalled pictures, empty cards and blank openings).
- **The script is approved before the voice.** `doc_tts.py` voices only a script the user has approved
  (`--script-approved`); `AGENTS.md` says what counts as approval.
- **Agents.** `AGENTS.md` and the `script2film` and `ve-director` skills, linked for Claude Code and other agents.
  Claude Code, Google Antigravity and opencode (with a local Qwen model and with DeepSeek) have each made films from
  the documents alone (`docs/AGENT-TRIALS.md`).
- **Optional stages.** Generated shots on VideoExpress (`tools/ve-runner/`), a talking host on TalkingPhotos
  (`tools/tp/`), composed music (`tools/score/`), Concat projects (`tools/concat/`), YouTube upload
  (`tools/youtube/`). Each spends your own account's credits only when you say so.
- **Examples.** `examples/coffee` (English, code-drawn only) and `examples/brewing` (Chinese, with a generated shot
  and a host; `premade/` makes it work without accounts).
- **Install.** `docs/INSTALL.md` and `tools/doctor/doctor.py`; verified on Apple Silicon Macs only.

Versions 0.7.0 to 0.9.0 were releases of Prompt Studio, the single-page prompt builder this project started as. It
now lives in `tools/prompt-studio/`; its history is not part of this repository.
