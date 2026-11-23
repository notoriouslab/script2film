# Example: install Script2Film with Claude Code Desktop

An English install guide of about 88 seconds, hosted by a comic avatar instead of a talking host: 阿華, a made-up
character, peeks in from the edges and keeps a badge in the corner (`"avatar"` in `doc.json`; format in
`skills/ve-director/doc/README.md`, "Comic avatar host"). Every picture is drawn by code (the app steps with the `ui_steps` scene: simplified parts that click, switch and tick on the spoken word); no account and no key. The last two lines show how to ask for VideoExpress shots.

## How to make it

Follow F0 to F6 in `docs/FLOW.md` with `<project>` replaced by this folder (`examples/install-desktop`). The script is
already reviewed: F2 runs without `--script-approved` (`expected.json` holds the narration's fingerprint).
For a Concat project, run F5 as `doc_cut.py examples/install-desktop/doc.json --render --avatar-lane` and pass
`--layers cut_lecture-tech/layers.json` to `tools/concat/plan2concat_mcp.py`.

Everything the steps write is in the repository's `.gitignore`; `git clean -fdX examples/install-desktop` removes it.

## Files

| File | What it is |
|---|---|
| `doc.json` | fourteen lines, fourteen code beats, the `lecture-tech` palette, the avatar moments |
| `facts.md` | where each on-screen fact comes from (the Claude Code Desktop quickstart page and `docs/INSTALL.md`) |
| `avatar/ahua/` | the sticker pack: ten faces cut with `doc_avatar.py pack` and their face centres in `faces.json` |
| `refs/` | the synthetic English voice from `examples/coffee` (designed from a text description, not a real person) |
| `expected.json` | the number of beats and lines, the range the film's length falls in, the approved script's fingerprint |
