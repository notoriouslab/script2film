# 範本：理工男重生法國國王（短劇，演員對嘴）

貼給 agent 這一句：

```
照文件把 examples/king/zh 做成片
```

八個鏡頭、約 33 秒的喜劇：黑底片名卡之後，兩個虛構角色（國王與大臣）在畫面上說出每一句台詞，配中文字幕，底下墊一段輕爵士。沒有旁白。

## 兩條路

### 快的路：用預製鏡頭（不需要 VideoExpress 帳號）

```
python3 tools/examples/fetch_premade.py examples/king/zh
cp -R examples/king/zh/premade/. examples/king/zh/
curl -fL -o assets/fonts/jf-openhuninn-2.1.ttf 'https://github.com/justfont/open-huninn-font/releases/download/v2.1/jf-openhuninn-2.1.ttf'
python3 tools/drama/drama_cut.py check examples/king/zh/cut.json
python3 tools/drama/drama_cut.py render examples/king/zh/cut.json
```

- 第一行從 GitHub Release 下載八個鏡頭與配樂，比對 `premade.json` 裡的 SHA-256 後解到 `premade/`；第二行把 `clips/` 與 `music.wav` 放到 `cut.json` 旁邊。
- 字幕字型（粉圓）在本倉庫是選用字型（OFL 1.1，見 `assets/README.md` 的 Optional fonts）。`assets/fonts/jf-openhuninn-2.1.ttf` 已經在就跳過 `curl`。
- `check` 用本機 whisper.cpp 逐句轉錄、跟字幕比對，最後一行要是 `✓ passed`；畫面上的字只是提醒。

### 自己做的路：換故事、換演員

1. 用 `ve-director` skill 規劃鏡頭：`../plan.md` 就是這支片的規劃（六個區塊，通過 `plan_lint.py` 與連戲審查）。有台詞的鏡頭寫在 `drama.json`，`drama_sheet.py` 把它轉成 `storyboard.md`。
2. 照 `storyboard.md` 開頭的定裝描述在 VideoExpress 做出兩位演員，把 id 寫進自己的 `masters.json`（`{"Actor 1": <id>, "Actor 2": <id>}`），用 `tools/ve-runner/ve_runner.py` 送出鏡頭、`ve_collect.py` 下載到 `clips/`（步驟見 `skills/ve-director/SKILL.md` 與 `tools/ve-runner/`）。
3. 作曲：在 `tools/score` 底下跑 `uv run python score.py --work ../../examples/king/score make ../../examples/king/zh/score_events.json`，再把 `examples/king/score/outputs/king-zh.wav` 複製成 `examples/king/zh/music.wav`。`score_events.json` 讓段落分別從片名卡、第一句台詞、書桌那場、大臣驚恐、最後一鏡開始。
4. 依自己的鏡頭改 `cut.json` 的入點與字幕時間，再照上面 `check`、`render`。

## 做完會看到什麼

- `cut.json` 旁邊出現 `king_zh.mp4` 與 `king_zh.srt`（已經有了，`render` 會寫成 `king_zh_v2`⋯）。
- 片名卡 → 國王醒來摸假髮 →「陛下，今天是一七八九年七月十三日。」→「明天巴士底監獄就要被攻破了！」→ 修鎖 →「不修鎖了，先修財政。」→ 宮裡開銷砍一半 →「可是王后的舞會⋯」→「改辦一場⋯全國工程師大會！」
- 配樂比台詞小約 13 dB（`cut.json`：對白 `db` −18、配樂 `db` −31）。

做片的產出都在 `.gitignore` 裡。要清掉：`git clean -ndX examples/king/zh`（先看），`git clean -fdX examples/king/zh`（刪）。

## 檔案

| 檔 | 內容 |
|---|---|
| `cut.json` | 時間軸：片名卡、八個鏡頭的入點、說話者、字幕、字型與配樂（格式見 `tools/drama/README.md`） |
| `drama.json`、`storyboard.md` | 有台詞的鏡頭，與由它產生的 VideoExpress 提示詞 |
| `score_events.json` | 配樂的分段（`tools/score`，風格 `lounge`） |
| `../plan.md` | 中英共用的鏡頭規劃 |
| `../facts.md` | 這齣喜劇借用的史實，以及哪些是編的 |
| `../masters_preview.jpg` | 兩位演員（AI 生成，不是真人） |
| `premade.json` | 預製鏡頭與配樂的下載位置、SHA-256 與大小 |

英文版在 `examples/king/en`。
