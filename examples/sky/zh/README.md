# 範本：天空為什麼是藍的？（Vox 拼貼，無主持人）

貼給 agent 這一句：

```
照文件把 examples/sky/zh 做成片
```

九句旁白、約 40 秒的科普短片：`collage` 剪紙拼貼風格，三張公有領域／CC0 照片加四個程式畫的圖解。不需要任何帳號。

## 兩條路

### 快的路：用預製旁白（不用等語音模型生成）

```
python3 tools/examples/fetch_premade.py examples/sky/zh
cp -R examples/sky/zh/premade/. examples/sky/zh/
python3 skills/ve-director/doc/scripts/doc_lint.py examples/sky/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_align.py examples/sky/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_lint.py examples/sky/zh/doc.json --beats examples/sky/zh/beats.json
python3 skills/ve-director/doc/scripts/doc_code.py examples/sky/zh/doc.json --render
python3 skills/ve-director/doc/scripts/doc_cut.py examples/sky/zh/doc.json --render
python3 tools/nightly/check.py examples/sky/zh/doc.json examples/sky/zh/cut_collage/output.mp4
```

- 第一行從 GitHub Release 下載旁白，比對 `premade.json` 裡的 SHA-256 後解到 `premade/`。下載失敗時它會印出 release 頁網址與手動解壓的指令。
- **不要跑 F2（配音）。** 預製旁白就是 F2 的產物；每一步做對了的樣子寫在 `docs/FLOW.md` 的 F1、F3 到 F6。
- 對時那一步要用到本機的語音轉錄（`docs/FLOW.md` F0 的安裝檢查會查）。

### 自己做的路：換題目、自己配音

照 `docs/FLOW.md` 從 F0 做到 F6。換題目就是改 `doc.json` 的 `lines` 與 `beats`，改了旁白要先給人核准才配音（F1）。

## 做完會看到什麼

- `cut_collage/output.mp4`：成片，長度落在 `expected.json` 的 `seconds` 範圍內。
- 第 1 拍封面 → 稜鏡照片 → 陽光撞上空氣分子的圖解 → 「波長 ÷ 2 → 散射 × 16」→ 紅藍長條 → 太空站看到的藍邊 → 為什麼不是紫色 → 夕陽照片 → 結尾大字「瑞利散射」。
- F6 的檢查退出碼是 0。

做片的產出都在 `.gitignore` 裡。要清掉：`git clean -ndX examples/sky/zh`（先看），`git clean -fdX examples/sky/zh`（刪）。

## 檔案

| 檔 | 內容 |
|---|---|
| `doc.json` | 九句旁白、九拍、主題 `collage` |
| `facts.md` | 每個畫面上的事實與出處（NASA Space Place、瑞利 1871、Physics FAQ） |
| `assets/` | 三張照片與四個圖示；來源與授權在 `assets/CREDITS.md` |
| `refs/narrator.wav`、`refs/narrator.txt` | 參考聲音：用文字描述設計的合成聲音，不是任何真人（`refs/voice_cast.json`） |
| `premade.json` | 預製旁白的下載位置、SHA-256 與大小 |
| `expected.json` | 做對了的樣子：拍數、句數、秒數範圍、旁白指紋 |
