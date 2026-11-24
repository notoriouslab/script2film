# 範本：35 秒學會 Claude Code Desktop（教學片，漫畫頭貼代主持）

貼給 agent 這一句：

```
照文件把 examples/desktop-short/zh 做成片
```

六句旁白、約 35 秒的教學短片，不用真人主持人，改由漫畫頭貼代班：虛構角色阿華在開頭與結尾探頭，中間在角落掛一個小徽章（`doc.json` 的 `"avatar"`）。App 的操作步驟由程式用 `ui_steps` 場景畫出來（簡化的示意，不是真的截圖）。不需要任何帳號。

## 兩條路

### 快的路：用預製旁白（不用等語音模型生成）

```
python3 tools/examples/fetch_premade.py examples/desktop-short/zh
cp -R examples/desktop-short/zh/premade/. examples/desktop-short/zh/
python3 skills/ve-director/doc/scripts/doc_lint.py examples/desktop-short/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_align.py examples/desktop-short/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_lint.py examples/desktop-short/zh/doc.json --beats examples/desktop-short/zh/beats.json
python3 skills/ve-director/doc/scripts/doc_code.py examples/desktop-short/zh/doc.json --render
python3 skills/ve-director/doc/scripts/doc_cut.py examples/desktop-short/zh/doc.json --render
python3 tools/nightly/check.py examples/desktop-short/zh/doc.json examples/desktop-short/zh/cut_lecture-tech/output.mp4
```

- 第一行從 GitHub Release 下載旁白，比對 `premade.json` 裡的 SHA-256 後解到 `premade/`。下載失敗時它會印出 release 頁網址與手動解壓的指令。
- **不要跑 F2（配音）。** 預製旁白就是 F2 的產物；每一步做對了的樣子寫在 `docs/FLOW.md` 的 F1、F3 到 F6。

### 自己做的路：換步驟、自己配音、換自己的頭貼

照 `docs/FLOW.md` 從 F0 做到 F6。要換成自己的表情包：用 `doc_avatar.py pack` 切好，改 `doc.json` 的 `avatar.pack`（格式見 `skills/ve-director/doc/README.md` 的 Comic avatar host）。

## 做完會看到什麼

- `cut_lecture-tech/output.mp4`：成片，長度落在 `expected.json` 的 `seconds` 範圍內。
- 第 1 拍封面，阿華從左邊探頭 → 下載登入 → 點 Code、選 Local、開空資料夾 → 打進那一句話 → 「安裝套件 → 字型 → 語音模型 → ✓ 可以開始了」→ 結尾封面，阿華從右邊揮手。第 2 拍起右下角掛小徽章。
- F6 的檢查退出碼是 0。

做片的產出都在 `.gitignore` 裡。要清掉：`git clean -ndX examples/desktop-short/zh`（先看），`git clean -fdX examples/desktop-short/zh`（刪）。

## 檔案

| 檔 | 內容 |
|---|---|
| `doc.json` | 六句旁白、六個程式畫面、`lecture-tech` 配色、頭貼出場時機 |
| `facts.md` | 每個步驟的出處（與 `examples/install-desktop` 同一套步驟） |
| `../avatar/ahua/` | 表情包，中英兩版共用（`doc_avatar.py` 也會往上一層找） |
| `refs/narrator.wav`、`refs/narrator.txt` | 參考聲音：用文字描述設計的合成女聲，不是任何真人（`refs/voice_cast.json`） |
| `premade.json` | 預製旁白的下載位置、SHA-256 與大小 |
| `expected.json` | 做對了的樣子：拍數、句數、秒數範圍、旁白指紋 |

英文版在 `examples/desktop-short/en`。
