# 範本：股六債四（財經解說，對嘴主持人）

貼給 agent 這一句：

```
照文件把 examples/stock-bond/zh 做成片
```

七句旁白、約 32 秒的財經解說：圖表全由程式畫，主持人前六句在左下圓框、最後一句全版。主持人是 AI 生成的虛構人物，聲音是用文字描述設計出來的合成聲音，不是任何真人。預製包附好了旁白與主持人片段，不需要任何帳號。

## 兩條路

### 快的路：用預製旁白與主持人（不用 TalkingPhotos 帳號）

```
python3 tools/examples/fetch_premade.py examples/stock-bond/zh
cp -R examples/stock-bond/zh/premade/. examples/stock-bond/zh/
python3 skills/ve-director/doc/scripts/doc_lint.py examples/stock-bond/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_align.py examples/stock-bond/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_lint.py examples/stock-bond/zh/doc.json --beats examples/stock-bond/zh/beats.json
python3 skills/ve-director/doc/scripts/doc_code.py examples/stock-bond/zh/doc.json --render
python3 skills/ve-director/doc/scripts/doc_host.py join examples/stock-bond/zh/doc.json
python3 skills/ve-director/doc/scripts/doc_cut.py examples/stock-bond/zh/doc.json --render
python3 tools/nightly/check.py examples/stock-bond/zh/doc.json examples/stock-bond/zh/cut_lecture-finance/output.mp4
```

- 第一行從 GitHub Release 下載旁白與主持人片段，比對 `premade.json` 裡的 SHA-256 後解到 `premade/`。下載失敗時它會印出 release 頁網址與手動解壓的指令。
- **不要跑 F2（配音）。** 附上的主持人是照預製旁白對嘴的；重新配音之後嘴型和長度都對不上，主持人就要自己重做。
- `doc_host.py join` 要在對時（`doc_align.py`）之後跑，它要用到對時產出的旁白。

### 自己做的路：換題目、換主持人

照 `docs/FLOW.md` 從 F0 做到 F6，加上選用 B（主持人）。

- 主持人的造型圖是 `refs/host_look.jpg`。要換成別人，照選用 B「The look image」的規則先做候選圖、挑定了再上傳；換了人，聲音也要換成配得上的（`refs/voice_cast.json` 是設計聲音用的描述）。
- 換了造型圖，`doc.json` 的 `pip.crop` 要跟著調到圓框對到臉。
- 數字改了，`facts.md` 要一起改、附出處。

## 做完會看到什麼

- `cut_lecture-finance/output.mp4`：成片，長度落在 `expected.json` 的 `seconds` 範圍內。
- 封面「股債比的黃金比例」→ 股六債四圓餅 → −37% → 2008 年股債長條 → 2022 年股債一起跌 → 「不賠」被劃掉改成「壞年份跌得淺一點」→ 主持人全版說資料來源。
- F6 的檢查退出碼是 0。

做片的產出都在 `.gitignore` 裡。要清掉：`git clean -ndX examples/stock-bond/zh`（先看），`git clean -fdX examples/stock-bond/zh`（刪）。

## 檔案

| 檔 | 內容 |
|---|---|
| `doc.json` | 七句旁白、七拍、`lecture-finance` 配色、圓框位置 `pip.crop` |
| `facts.md` | 每個數字的出處（紐約大學 Damodaran 的歷年報酬資料） |
| `refs/host_look.jpg` | 主持人造型圖（AI 生成，不是真人） |
| `refs/narrator.wav`、`refs/narrator.txt` | 參考聲音：用文字描述設計的合成聲音（`refs/voice_cast.json`） |
| `premade.json` | 預製旁白與主持人片段的下載位置、SHA-256 與大小 |
| `expected.json` | 做對了的樣子：拍數、句數、秒數範圍、旁白指紋 |

英文版在 `examples/stock-bond/en`。這不是投資建議。
