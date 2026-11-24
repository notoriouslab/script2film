# Template: an engineer wakes up as the King of France (short drama, lip-synced actors)

Paste this sentence to your agent:

```
Follow the docs and make examples/king/en into a film.
```

A comedy of eight shots, about 33 seconds: a black title card, then two made-up characters (the king and his minister)
speak every line on screen, with English subtitles and a light-jazz score under them. No narrator.

## Two ways

### The quick way: use the premade shots (no VideoExpress account)

```
python3 tools/examples/fetch_premade.py examples/king/en
cp -R examples/king/en/premade/. examples/king/en/
curl -fL -o assets/fonts/CormorantGaramond-Variable.ttf 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf'
python3 tools/drama/drama_cut.py check examples/king/en/cut.json
python3 tools/drama/drama_cut.py render examples/king/en/cut.json
```

- The first line downloads the eight clips and the score from the GitHub Release, checks them against the SHA-256 in
  `premade.json` and unpacks them into `premade/`; the second puts `clips/` and `music.wav` next to `cut.json`.
- The subtitle font is optional in this repository (OFL 1.1; `assets/README.md`, "Optional fonts"). Skip the `curl`
  if `assets/fonts/CormorantGaramond-Variable.ttf` is already there.
- `check` transcribes each line with local whisper.cpp and compares it with the subtitles; it must end with
  `✓ passed`. Burned-in text is only a reminder.

### The full way: your own story, your own actors

1. Plan the shots with the `ve-director` skill: `plan.md` is this film's plan (six blocks, passed `plan_lint.py`
   and the continuity review). `drama.json` holds the spoken shots; `drama_sheet.py` turns it into `storyboard.md`.
2. Make the two actors in VideoExpress from the portrait descriptions at the top of `storyboard.md`, put their ids in a
   `masters.json` of your own (`{"Actor 1": <id>, "Actor 2": <id>}`), then send the shots with
   `tools/ve-runner/ve_runner.py` and download them with `ve_collect.py` into `clips/` (steps in `skills/ve-director/SKILL.md` and `tools/ve-runner/`).
3. Compose the score: from `tools/score`, run
   `uv run python score.py --work ../../examples/king/score make ../../examples/king/en/score_events.json`, then copy
   `examples/king/score/outputs/king-en.wav` to `examples/king/en/music.wav`. `score_events.json` puts a section start
   on the title card, the first line, the desk scene, the minister's fright and the last shot.
4. Fix the in-points and subtitle times in `cut.json` to your clips, then `check` and `render` as above.

## What you will see when it is done

- `king_en.mp4` and `king_en.srt` next to `cut.json` (if they exist, `render` writes `king_en_v2`, …).
- Title card → the king wakes in a wig → "Your Majesty, today is the thirteenth of July, 1789." → "Tomorrow they
  storm the Bastille!" → the locks → "No more locks. We fix the budget." → cutting the palace spending in half → "But
  the Queen's ball…" → "We'll hold… a national engineering fair!"
- The music sits about 13 dB under the dialogue (`cut.json`: dialogue `db` −18, music `db` −31).

Everything the run makes is in `.gitignore`. To clear it: `git clean -ndX examples/king/en` (look first),
`git clean -fdX examples/king/en` (delete).

## Files

| File | What it is |
|---|---|
| `cut.json` | the timeline: title card, eight shots with in-points, speakers, subtitles, font and music (format in `tools/drama/README.md`) |
| `drama.json`, `storyboard.md` | the spoken shots and the VideoExpress prompts made from them |
| `score_events.json` | the sections of the score (`tools/score`, style `lounge`) |
| `../plan.md` | the shot plan shared by both languages |
| `../facts.md` | the history the comedy leans on, and what is made up |
| `../masters_preview.jpg` | the two actors (AI-generated, not real people) |
| `premade.json` | where the premade clips and score are, their SHA-256 and size |

The Chinese version is in `examples/king/zh`.
