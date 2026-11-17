# Script2Film

[English](./README.md) · **繁體中文**

從一份稿做到一支成片，一個環節接一個環節：稿 → 聲音 → 對時 → 畫面 → 組裝 → 發佈。
每個環節有一個預設工具和一份檔案約定，換工具不用動其他環節。

> **現況。** 核心流程（配音、對時、程式畫面、組裝、檢查）在自己的電腦上跑，不用帳號，也不用 API 金鑰。
> 2026-11-17 用空的家目錄與全新複本從頭裝過一次，並做出第一支範例片；步驟與實測時間在 [docs/INSTALL.md](./docs/INSTALL.md)（英文）。
> 目前只在 Apple Silicon 的 Mac 上驗證過。

## 從這裡開始

- **在新機器上安裝**：[docs/INSTALL.md](./docs/INSTALL.md)（英文）。第一次約 30 分鐘、下載約 7 GB，大部分是配音那一步
  （`bash tools/doctor/setup_voice.sh`，20 到 25 分鐘、約 6 GB）。`python3 tools/doctor/doctor.py` 會全部檢查一遍，
  缺什麼就印出對應的修法。Python 套件裝在 `.venv`，腳本會自己換用它，所以照樣打 `python3` 就好。
- **AI agent**：把這個資料夾本身開成工作區（agent 從工作區根目錄載入 `AGENTS.md` 與 skill）。
  [AGENTS.md](./AGENTS.md) 是每一輪都生效的規則；`script2film` skill（[skills/script2film/SKILL.md](./skills/script2film/SKILL.md)）
  用符號連結接到 `.agents/skills/` 與 `.claude/skills/`，Windows 要開 git 的 `core.symlinks`。
- **步驟與命令**：[docs/FLOW.md](./docs/FLOW.md)（英文）。
- **哪些 agent 只靠文件做出過片**（Claude Code、Google Antigravity、opencode 搭本機模型或 DeepSeek），以及卡住時怎麼排除：
  [docs/AGENT-TRIALS.md](./docs/AGENT-TRIALS.md)（英文）。

## 範例

- [examples/coffee/](./examples/coffee/)：第一支先做的片。四句英文旁白、約 25 秒、四個程式畫的場景，說明也是英文。
  不用帳號，也不用金鑰。
- [examples/brewing/](./examples/brewing/)：五句中文旁白、約 23 秒，有一個外部生成的鏡頭與對嘴的主持人（說明是中文）。
  生成好的檔附在 `premade/`，所以同樣不用帳號。

## 環節

| 環節 | 輸入 → 輸出 | 預設 | 選用 |
|---|---|---|---|
| 稿 | 題目與素材 → `doc.json`（台詞與拍） | 照格式文件手寫 | AI 代理照 skill 寫 |
| 聲音 | 台詞 → 每句音檔，再接成旁白 | Qwen3-TTS，在自己的電腦上跑 | 自己錄音 |
| 對時 | 旁白 → `beats.json`、字幕 | mlx-whisper，在自己的電腦上跑 | Groq、ElevenLabs Scribe |
| 畫面：程式畫面 | 拍與參數 → 每拍一支 mp4 | `skills/ve-director/doc/` 的場景引擎（27 個場景） | |
| 畫面：素材 | 照片與影片 → 某一拍的畫面 | 附授權紀錄的照片 | VideoExpress，由 `tools/ve-runner/` 操作 |
| 主持人 | 旁白 → 主持人影片 | 不放主持人 | TalkingPhotos |
| 音效配樂 | 拍 → 音效標記、配樂 | 隨倉庫附帶的音效 `assets/sfx/`（CC0、自製、VideoExpress 生成）；`tools/score/` 程式作曲的配樂 | CC BY 曲（要署名）；用自己的 VideoExpress 帳號生成音效（`tools/assets/gen_sfx_ve.py`） |
| 組裝 | 以上全部 → 成片 | `doc_cut.py --render` | Concat（推薦），用來加疊加層（側框主持人、關鍵字標籤、章節標示、照片出處） |
| 發佈 | 成片 → 平台 | 手動上傳 | YouTube API |

從配音到出片，預設路徑不需要其他剪輯軟體，也不需要任何 API 金鑰（`tools/check-standalone.sh` 在乾淨環境裡驗這件事）。

## 東西在哪

| 路徑 | 是什麼 |
|---|---|
| `skills/script2film/` | agent 做解說片時照著走的 skill；它把步驟導到 `docs/FLOW.md` |
| `skills/ve-director/` | VideoExpress 的分鏡 skill：先把一場戲排成分鏡表，再產出檢查過的提示詞。規則在 `skills/ve-director/rules/` |
| `skills/ve-director/doc/` | doc 模式：有旁白的解說片。配音、逐字對時、27 個程式畫面場景、主題、事實檢查、剪輯。先讀它的 `README.md` |
| `tools/doctor/`、`tools/config/` | 安裝檢查、配音環境安裝（`setup_voice.sh`）、每台機器一份的設定檔 |
| `tools/tts/` | 設計聲音、多角色配音、語者相似度比對 |
| `tools/nightly/`、`tools/checklist/`、`tools/qa/` | 檢查：出片檢查（`check.py`）、開工與出片清單、逐格的動態檢查 |
| `tools/ve-runner/` | 在瀏覽器裡把分鏡送到 VideoExpress 執行並收回片段 |
| `tools/tp/` | 用 TalkingPhotos 做會說話的主持人 |
| `tools/assemble/`、`tools/concat/` | 把片段排成時間軸；再依它建 Concat 專案 |
| `tools/drama/` | 剪對嘴短劇（沒有旁白）：一份時間軸檔，有沒有 Concat 都能出片 |
| `tools/score/` | 跟著畫面走的程式作曲配樂，用 SoundFont 離線渲染 |
| `tools/assets/` | 用自己的 VideoExpress 帳號生成音效；從舊的素材庫複製字型與音效 |
| `tools/youtube/` | 在自己的頻道上傳、排定、改標題 |
| `tools/prompt-studio/` | Prompt Studio：給 VideoExpress 用的單檔 HTML 提示詞工具（這個倉庫最早的樣子） |
| `tools/agents/`、`tools/site/` | 把 skill 接到各家 agent 會找的位置；產生網站的英文頁與網站上的 Prompt Studio 複本 |
| `examples/` | 兩支範例片 |
| `assets/` | 隨倉庫附帶的音效（在 git 裡）與兩套字型（要下載，見 `assets/README.md`） |
| `docs/` | 上面那些文件，以及專案網站：首頁、工具、場景與色版、Prompt Studio 介紹頁與線上版（`docs/studio.html`）；英文頁在 `docs/en/` |

## 需求與帳號

目前只在 Apple Silicon 的 Mac 上驗證過。預設的轉錄（mlx-whisper）只能在 Apple Silicon 上跑；Windows、Linux 與 Intel Mac
都沒有試過（見 [docs/INSTALL.md](./docs/INSTALL.md) 的「Not covered」）。

核心流程不用任何帳號或金鑰：配音、對時、程式畫面、`doc_cut.py --render` 與檢查。選用的部分用你自己的帳號：VideoExpress
（生成鏡頭、音效）、TalkingPhotos（主持人）、YouTube（上傳），雲端轉錄要 Groq 與 ElevenLabs 兩把金鑰。Concat 是另外安裝的軟體。
每一項在 [docs/FLOW.md](./docs/FLOW.md) 用到的地方都有說明。

## 參與貢獻

見 [CONTRIBUTING.md](./CONTRIBUTING.md)（英文）。安全問題：[SECURITY.md](./SECURITY.md)（英文）。

## 授權

[MIT](./LICENSE)。想法、文字與素材從哪裡來，以及每個第三方元件的授權，都記在 [NOTICE.md](./NOTICE.md)。
