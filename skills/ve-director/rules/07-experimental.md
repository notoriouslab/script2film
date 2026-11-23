# 07 — Experimental rules (skill only, not part of the HTML tool)

Rules here are NOT validated on VideoExpress yet. Each one says where it came from and how many takes back it. Use an experimental rule only when it clearly fits; when you use one, say so in one line at CP1 and at delivery so the user knows the shot is a test. Promote a rule into 01/02 only after takes confirm it; delete it if takes refute it.

## §1 Hard-cut pair — two framings in one generation (plan side)

Status: EXPERIMENTAL · 1 test, 3 takes (2026-10-03, watercolor, 中景 → 臉部近景): 2 of 3 cut cleanly, kept face and costume, sound continuous; the cut did not land exactly on the labelled second · idea from an external community VE skill, rewritten here.

**What it is.** One VE generation holds two framings joined by a single hard cut (e.g. 中景 0-4s, then 近景 4-8s). It saves a T2I image and a generation when a beat needs a size change but no camera move.

**Precedence.** For a row that uses it, this suspends the plan rule "one framing per shot; a framing change needs a camera move". Everything else in the plan rules still applies.

**Use it only when all of these hold:**
- **The second framing is a closer view of what the first frame already shows clearly**, from the same camera side and the same screen direction. VE sees only the first frame (the T2I draws 鏡頭一 alone), so anything the second framing shows that the first frame does not show well, it invents.
- **A face close-up after the cut needs that face clearly visible before it**: 鏡頭一 at 中景 (waist up) or closer with the face lit and turned toward camera. 遠景 → 臉部特寫 is out of scope until tested.
- Same place, same Actors, same side of every boundary, no time jump. No Actor appears or leaves at the cut. No reverse angle, no new space.
- Exactly one cut, two sub-shots, each at least 3 s, total 6-10 s. The cut lands near, not on, the labelled second: never time a sound or an action to the exact cut point, and expect about one re-roll in three. At most one action step per sub-shot (the row's two-step cap still holds overall).
- Fits a REACT or REVEAL beat: 中景 of the Actor → 近景 of their reaction; 中景 of the Actor → 特寫 of a prop already lit in their hands or on the table.

**Notation (one table row per generation, so the checks keep working):**
- 秒數: the generation total (e.g. `8`).
- 景別: `中景 0-4s｜硬切｜近景 4-8s`.
- 構圖與左右位置 / 運鏡: one entry per sub-shot, separated by `｜` (e.g. 運鏡 `固定｜固定`).
- 開始狀態 is 鏡頭一's first frame; 結束狀態 is 鏡頭二's last frame. The ledger has the usual two lines; nothing about the entity changes at the cut.
- 任務 gets the suffix `（硬切實驗）`.

## §2 Hard-cut pair — rendering (I2V side)

Status: EXPERIMENTAL, see §1. Applies only to a plan row whose 景別 contains `｜硬切｜`.

**Precedence.** For that row only, these replace parts of the `02-modes.md` §0.1 template:
1. `[REFERENCE USE]`: the image controls 鏡頭一 only. Use: `以提供的圖片作為本次生成的精確開場畫面；它決定鏡頭一的構圖、世界、光線與取景，鏡頭二沿用同一個地點、色調、光線與角色。`
2. `[IDENTITY / CONTINUITY]`: replace `整支為單一連續鏡頭，不剪接。` with `本次生成由兩個鏡頭組成，中間只有一次硬切，依下文順序。` Mouth locks cover every visible face in either sub-shot.
3. The single trailing `[CAMERA]` + `[LIGHT AND IMAGE]` becomes one trio per sub-shot, in this order: `[ACTION 0-<a>s] 鏡頭一。…` `[CAMERA] …` `[LIGHT AND IMAGE] …` `[ACTION <a>-<N>s] 鏡頭二。…` `[CAMERA] 硬切至<景別>：<鏡頭二畫面裡有什麼>，與鏡頭一同一側、同一軸線；…` `[LIGHT AND IMAGE] …`, then `[PRODUCTION SOUND]` and `[NEGATIVES]` once.
4. `[PRODUCTION SOUND]`: add `聲音跨越硬切連續不中斷。`
5. `[NEGATIVES]`: start with `除上述一次硬切外不剪接、` and keep the style's list.

Everything else (語言規則, Actor Alias, locks, the style's `[LIGHT AND IMAGE]` and `[NEGATIVES]`, sound convention) is unchanged. The check script enforces the shape (L8).

## §3 Trial batch before the full run (run side)

Status: EXPERIMENTAL · not yet tested as a step. Faults that repeat across shots (a room that drifts, a master that forces the framing, a kind of shot VE misreads) show up in the first few shots; finding them before the full run saves re-rolling the whole batch.

**When.** A story film (SKILL.md, "Story films go through the flow above"), after the plan is approved and `lint.py` passes, before the whole storyboard goes to VE. Skip it when the film has 4 shots or fewer, or when it reuses a style, location and masters already run in an earlier film unchanged; say in one line that it was skipped and why. Sending the trial needs the same go-ahead as any VE run.

**Pick the trial shots: one per kind of shot the plan uses**, from this list, usually 3-5 shots:
- a wide or full shot that sets up the location;
- a close shot (中近景 or closer) of a character in that location;
- a shot with a spoken line;
- a shot with no person in it (an object, an insert, a view of the ceiling);
- a shot of a body part only (a hand, the back of a head);
- in a two-character scene, a line and the cut to the other character's response (two consecutive shots).

Where a kind has several shots, take the one the continuity review flagged as riskiest. Name the trial shots in the CP1 plan.

**Run.** `python3 tools/ve-runner/ve_runner.py storyboard.md --shots <n …> --takes 2` with the film's masters. Collect the clips, put them in story order and watch at normal speed.

**Judge each fault by its cause.**
- The cause is shared with other shots in the plan (the same master, the same location wording, the same framing, the same kind of line or prop): fix the plan or the masters for every shot with that cause, run `plan_lint.py` and `lint.py` again, and re-trial only the shots that showed the fault.
- The fault is a one-off of VE (an extra braid, burned-in text, one odd take): note it, pick around it at QC, and go on.

Then run the rest with `--shots` for the remaining shots; trial takes that passed are kept, not re-made.

**Record it** in the film's notes: the trial shots, each fault found (shared or one-off), what changed in the plan before the full run, and after the full run how many shots were re-rolled and why. Promote this section to the plan rules after two films where the trial caught at least one shared fault; delete it if two films show none and the full run needed as many re-rolls as before.

## §4 Story chain — a premise built into a plot (plan side)

Status: EXPERIMENTAL · not validated yet.

Applies only when the plot is yours to build (the user gave a premise, not a source text). A source text's events stand: this rule never adds events to a source.

1. **Dramatic question and decisive choice.** Before the shot table, decide one question the audience wants answered by the end, the protagonist's decisive choice (an act seen on screen, not a feeling), and what that choice costs or changes, shown in a later shot rather than stated.
2. **Every beat follows from an earlier one.** Each shot after the opening exists because of an earlier shot: a choice someone made, something someone discovered, or the consequence of either. "And then" links (one event simply after another) are not allowed; "so" and "but" links are. An opening ESTABLISH shot is exempt.
3. **What is set up pays off.** Every prop, line or piece of information the plan makes the audience notice (an insert, a close-up on it, a line about it) is used again later and changes something. Cut what is not paid off, or pay it off.
4. **The ending answers the question.** The last beats answer it. A closing hook may open a new question only after the main one is answered.
5. **Every link is on screen.** A link counts only when a shot shows it: the cause is seen before the effect, a state change (food eaten, a device charged, a door unlocked) has a shot where it happens or a shot that shows its result plainly, and an unusual action (holding a watch to the ear) has a shot before it that makes it the natural thing to do. A link that lives only in your reasoning is a gap.

Checking: write the chain as a review-only line after `連戲檢查：` — `因果鏈：` with `N ← M（選擇／發現／後果）` for each shot after the first, then the setups with the shot where each pays off. The continuity review (or, without a subagent, your own re-read as that reviewer) checks each link against the table's cells only, not against this line, and lists a link with no shot as **阻斷**. When you use this rule, say so in one line at CP1.

## §5 The listener stays in the scene (dialogue between two characters)

Status: EXPERIMENTAL · not validated yet.

A dialogue cut only from singles of each speaker reads as two people talking alone. Put the listener in frame for part of the exchange.

- **Mix the framings.** In a two-character dialogue, use at least one two-shot or over-the-shoulder shot where the listener is visible, besides any singles. A silent reaction cutaway of the listener works too, but not on every line: in a short exchange, one reaction cutaway plus one over-the-shoulder reads better than a cutaway on each line.
- **Two-shot with one spoken line (Lipsync).** The single line always goes to Actor 1's script, so the video prompt defines Actor 1 as the speaker, whichever reference slot that person is in: `Actor 1 is the man on the right; Actor 2 is the woman on the left.` The listener gets the mouth-lock sentence (`01-core.md` §11) and one small reaction with the eyes, head or hands while the line is spoken.
- **Over-the-shoulder.** The listener is the out-of-focus back of the head and one shoulder in the foreground; write `exactly two people in the frame` in the image prompt.
- **Singles.** Never write that the speaker looks at someone off frame: VE draws that someone. Give the eye direction (`eyes looking toward frame right`) and add `Only this one person is in the frame; the rest of the frame is the plain wall and the table, empty.` Check the head count in the first frame at QC.
- **Edit.** Trim each dialogue clip to its speech window (`plan-rules.md` § Edit pass); full-length clips leave gaps between lines.

`scripts/drama_sheet.py` writes the Actor 1 line, the listener's lock and the reaction from a shot's `listener` field (format in its docstring), and warns when a single mentions someone off frame.
