# Facts: Install Script2Film with Claude Code Desktop

Checked 2026-11-23. Claude Code Desktop steps from the official docs page; Script2Film steps from `docs/INSTALL.md`
(measured 2026-11-17) and a run in Claude Code Desktop on 2026-11-23 (an empty folder, the request on B7, Auto mode: about
7 minutes to `✓ ready to go`, the voice step skipped because that machine already had it).

| On screen | Tier | Source | Excerpt | Note |
|---|---|---|---|---|
| Code tab: paid plan (B4 chip) | primary | code.claude.com/docs/en/desktop-quickstart, read 2026-11-23 | Claude Code requires a Pro, Max, Ultra, Team, or Enterprise subscription. | B4 |
| Node.js, Claude Code CLI struck out; Claude Code: already in the app (B5) | primary | code.claude.com/docs/en/desktop-quickstart, read 2026-11-23 | The desktop app includes Claude Code, so you don't need to install Node.js or the CLI to use the Code tab. | B5 |
| Chat/Code menu, Cloud/Local switch, Open folder…, an empty folder (B6; drawn, not the app's real layout: the app lists environments in a menu with a Local group) | primary | code.claude.com/docs/en/desktop-quickstart, read 2026-11-23 | click the Code tab at the top of the sidebar; select the top entry in the Local group; select Open folder… | B6 |
| Clone https://github.com/notoriouslab/script2film into this folder and follow docs/INSTALL.md to install it. | primary | the request typed in the 2026-11-23 run | (the request itself) | B7 |
| 20 | primary | docs/INSTALL.md, measured 2026-11-17 | bash tools/doctor/setup_voice.sh … the voice model (about 6 GB) … 20 to 25 minutes | B10 stat |
| Auto / Manual switch; keeps going, asks before each command (B8) | primary | code.claude.com/docs/en/desktop-quickstart, read 2026-11-23; Auto seen as the default in the 2026-11-23 run | Auto: a classifier reviews actions in the background and blocks the risky ones instead of asking you. Manual: Claude asks before editing files or running commands. | B8 |
| ✓ ready to go | primary | tools/doctor/doctor.py, last line on success | ✓ ready to go | B11 |
| Make this script into a film, with VideoExpress shots. | primary | docs/FLOW.md, "Optional A: generated shots (VideoExpress)" (read 2026-11-24) | Beats with `source` set to `ve` are written into a run sheet, and the script prints the `tools/ve-runner/ve_runner.py` command to run next. | B12, the request is an example wording |
| Shot prompts → VideoExpress → Clips → Your film | primary | docs/FLOW.md (read 2026-11-24): run sheet, `ve_runner.py` submits, `ve_collect.py` collects, F5 cuts | `all N shot(s) submitted` is followed by the `ve_collect.py` command to use | B13 |
