# Changelog

## 1.2.2 (2026-11-24)

- **Film check, first 30 s:** each beat start counts as a new picture (FORMAT §4c). Collage beats that grow out of the
  same blank paper were missed, so the longest gap read too long (15.8 s for the sky template; now 7.2 s). The same
  measure feeds the `pace` gate.
- The film check names FORMAT by its path (`skills/ve-director/doc/formats/vox-host/FORMAT.md`).
- `doc_lint` shows the "Bible quotes are compared only with facts.md" note only when the script has a scripture
  reference.

## 1.2.1 (2026-11-24)

Fixes from running each template once more from a clean clone:

- **king:** the title card is dark brown instead of pure black, so `film_check.py` passes (it reads a black card as a
  black gap); the README now runs `film_check.py` after `render`.
- **sky:** the photos on beats 6 and 8 are smaller, so their credit labels stay clear of the subtitles.
- **stock-bond:** the README says the host is in the circle for the first two lines (it said six).
- `.gitignore` covers the `.sha256` marker copied up from `premade/` and `film_check.py`'s `*.check.json` report.

The premade packs are unchanged and still come from the v1.2.0 release.

## 1.2.0 (2026-11-24)

- **Comic avatar host** (`"avatar"` in doc.json): a narrator's comic sticker pack instead of a TalkingPhoto host. A
  whole panel for the opening or the close, panels peeking in from an edge (depth worked out from the face, lower
  peeks only from the two corners so the subtitles stay clear), and a corner badge that flips faces. Burned into the
  `--render` film and, with `doc_cut.py --avatar-lane`, rendered alone as a transparent ProRes 4444 lane for Concat. `doc_avatar.py pack` / `check`
  cut and check a sticker sheet; `doc_lint` reminds on more than two panels, the same edge or the same face twice in a
  row (`avatar_mix`). Not allowed together with `pip`, `side` or a host clip beat. Concat projects with `side` or
  `pills` now get one more (empty) layer lane for the avatar.
- **The avatar talks:** with a second sheet of the same faces, mouths open (`doc_avatar.py open`), the avatar on
  screen opens and closes its mouth with the narration's loudness. Only the mouth is taken from the second sheet, so
  redrawn backgrounds do not flicker. `"talk": false` turns it off.
  A face drawn mid-laugh gets a closed frame with its mouth squeezed to half height (`doc_avatar.py shut`), so it
  still reads as talking in the small corner badge.
- **New scene `ui_steps`:** app steps drawn instead of recorded. A panel of simple parts (card, button, toggle, menu,
  check box, input, chips) changes state on the spoken word, and a cursor glides to each click. No screen recording,
  no account on screen, and it follows the theme's colours. The install-desktop example now uses it for the Desktop
  steps and ends with two lines on adding VideoExpress shots.

- **Four templates, each in Chinese and English** (`examples/<template>/<zh|en>/`): why the sky is blue (Vox-style
  collage), Claude Code Desktop in 35 seconds (comic avatar host), the 60/40 portfolio (talking host) and an engineer
  waking up as the King of France (short drama with light jazz). Paste one sentence to the agent; the narration, host
  clips and drama shots come from the v1.2.0 release through `tools/examples/fetch_premade.py` (SHA-256 checked), so
  none needs an account. `tools/examples/pack_premade.py` packs them.
- **Website and README:** the start section now comes right after the opening: three steps, then four template cards
  with an 8-second preview each. The English pages again carry the Google Flow text in English.
- **photo `color`:** `true` keeps a photo's own colours in the `collage` theme.
- **drama_cut:** `sub_size` and `font_weight` (a weight of a variable font); `check` counts Arabic digits in a Chinese
  line, so "1789" is no longer read as a cut-off line.
- **Fixes:** `tp_multi.py` finds uploads whose name has `_` (TP shows it with spaces); `doc_avatar` also finds a
  sticker pack one folder up (shared by a template's two languages); optional fonts download under their manifest names.

## 1.1.7 (2026-11-23)

- **Three experimental ve-director rules** (`skills/ve-director/rules/07-experimental.md`): a trial batch of one shot
  per kind before the full VideoExpress run (§3); for plots built from a premise, every shot follows from an earlier
  one and every setup pays off on screen (§4); in two-character dialogue, keep the listener in frame with two-shots,
  over-the-shoulder shots and one reaction cutaway (§5).
- **drama_sheet listener:** a `listener` field writes who speaks, the listener's closed mouth and one reaction for a
  two-person lipsync shot; a single that mentions someone off frame gets a warning.
- **ve_runner fix:** picking the second image candidate no longer stops the run.
- **Comparison cards carry pictures:** a `compare` card with no video under it and no host frame puts one still under
  each column from the start (`params.photos`, at 0.3 / 0.8). Words alone left a bare dividing line for seconds; with
  stills the user called it clearly better and made it the rule (`formats/vox-host/FORMAT.md` §7b). `doc_lint` lists
  words-only comparison cards (`bare_compare`, a reminder).
- **Occlusion one-take (VideoExpress, photoreal):** a sideways track where each wall passing the lens changes the
  place, the time or the clothes, measured on 11 clips: the prompt, up to four places or two changes of clothes per
  10 s, solid walls only (glass and slim posts turn into dissolves), a passer-by or a door as alternatives
  (`skills/ve-director/references/styles/live.md`). `tools/ve-runner/ve_wallcuts.py` finds the walls, makes a sheet
  to check them and joins several clips behind a wall, so a sequence can hold more changes than one clip.

## 1.1.6 (2026-11-22)

### Colour where colour is the content

- **Photos keep their colours:** `"photo_color": true` stops the collage theme from turning photos, paintings and the
  charts you draw into grey halftone. One episode's review found every chart and photo grey, the colours drawn into
  the charts included.
- **Colour paper collage:** `"collage_color": true` keeps the cut, tape, torn layers and halftone print but lets the
  cut-outs keep muted natural colours (`doc_themes.COLLAGE_COLOR_LAW`), for subjects such as food, cloth and dyes.
  It implies `photo_color`. Black and grey with one accent stays the default.

### Cards that never look broken

- **Quote cards:** with `photo_at` (e.g. 0.3) the stills come in first and the quote strip waits for the spoken quote.
  Before, a faint strip sat on screen for seconds until the voice reached the quote. The bare-paper check counts these
  stills.
- **Closing credits:** `roll` sets how many seconds the list takes to come to rest. Rolling for the whole beat kept a
  long list over the subtitles until the end.
- **Keyword pills:** each pill can set its own `fill` and `color`.
- **Layout notes from a frame-by-frame review** (`formats/vox-host/FORMAT.md` §7b):
  - With the host on the right, the diagram fills the left half.
  - A cover on a dark background does not take a dark title.
  - The round host frame sits above two-line subtitles.
  - Question pills are drawn into full-frame charts.
  - People in diagrams are small friendly figures, not dots.

### Tools

- `tools/tp/tp_wait.py` waits for a TalkingPhotos card in My Videos to finish rendering and downloads it, for any
  flow, Replicate Motion included.
- `ve_collect.py` no longer stops when `ve_runner` holds the browser profile. It copies the profile without its cache
  (about 24 MB), collects, then deletes the copy.
- `google-flow`: the credit price for 720p is recorded, and Omni cannot lip-sync your own narration.

## 1.1.4 (2026-11-21)

### Generated shots: Google Flow joins VideoExpress and H3

With a Google AI Plus, Pro or Ultra plan, a single shot can come from Google Flow (Omni 1.2 Flash, Veo). The new
`google-flow` skill drives Flow in your own signed-in Chrome, because Google refuses sign-in in browsers launched by
automation tools. `skills/google-flow/scripts/flow_ingest.py` puts the download at `ve_<look>/shotK.mp4` with a
`.flow.json` record (model, settings, prompt, source file, SHA-256) and a ten-frame sheet to look at before cutting.
`references/flow-video.md` holds the steps and what was measured: a reference image keeps faces and clothes, one
continuous action with one camera path flows better than timed blocks, selfie vlogs and bullet time work, large
martial-arts scenes do not, and which wording gets refused by policy.

### Music: a song from Google Flow Music

The same skill makes a song or an instrumental in Flow Music (included in Google AI Pro) from your lyrics and a style
line, and `flow_ingest.py --doc` sets it as the film's `bgm` with its credit. `references/flow-music.md` covers the
Compose panel, how to write the style line (describe a singer's style instead of naming them), and what the terms
do and do not say about commercial use.

### VideoExpress runs no longer stop on a late candidate

When VideoExpress adds a second candidate frame after `--auto-pick` has chosen the first, the run now keeps the
frame VideoExpress has selected, as long as it was made for this shot, instead of stopping the whole batch. A frame
left over from the previous shot still stops it.

## 1.1.2 (2026-11-20)

- **Every exported film is checked.** Concat exports run `tools/nightly/film_check.py`: length, black frames, loudness,
  sound effects in the mix, stale files. The release checklist uploads only the checked file.
- **Reminders that never fail a film:** too many generated shots (`peak_weight`), too close to the last three
  episodes (`vs_prev`), music that does not step aside (`quiet`), a slow opening (`first30`), the same theme three
  episodes in a row.
- **Side by side with a film you like:** `tools/sample/breakdown.py`.
- **New scene moves:** a quotation that comes out of a blur as it is read (`quote_card` `reveal`), a struck-out word
  rewritten (`formula` `strike.to`), a long timeline that slides (`timeline` `window` / `from`), a clue board
  (`relation` `look: "board"`).
- **Five new themes:** `dark-gold`, `newsroom`, `vintage-poster`, `editorial-serif`, `cinematic-dark`, each changing
  colours, shapes and ground (`themes/styles.json`).
- **Theme preview:** `doc_theme_preview.py` plays three themes on the episode's own beats before it is voiced
  (`docs/FLOW.md` optional G).
- **Optional fonts:** LXGW WenKai (TC and SC) and jf open-huninn, listed with their download links.
- **Local transcription is whisper.cpp** (set `S2F_WHISPER_CPP_MODEL`; `setup_voice.sh` does it).
- **Fixes:** an all-silent sound track no longer crashes the film check.

## 1.1.0 (2026-11-18)

- **MiniMax H3 and MiniMax Music 3 on your own Google Colab GPU (optional).** `tools/h3/h3_film.py` plans, runs and
  collects generated shots and a lip-synced host (the host keeps the narration as its voice); `tools/music3/music3_film.py`
  makes a song or an instrumental for `bgm.src`. The H3 licence excludes the US, the EU, the UK and South Korea, so
  the start checklist asks where you are and where the film is used (`h3-territory`).
- **Dialogue voices.** `lines[].speaker` picks a voice from `doc.json` `"voices"`, each with its own pitch; the
  speaker is part of the approved script.
- **Subtitles.** `subs.burn: "en"` burns English subtitles only over Chinese narration; an empty `"en"` line gives no
  English cue; `sub_highlight` colours chosen words in burned subtitles.
- **The picture runs on after the last word.** `end_hold` (default 1 s) keeps the last picture on screen so a face
  can settle; the host's last part ends in that silence too.
- **Host takes.** `clip_in` keeps lip sync when the narration was retimed after the host was made; TalkingPhotos
  segment names follow what TalkingPhotos shows (an underscore becomes a space).
- **Website.** The opencode + DeepSeek V4.1 Flash trial on the homepage; share previews in Chinese and English.
- **README.** Rewritten after the website: what is different, what it does with real frames, films made with it, the
  agent trials and the first film in three steps.

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
