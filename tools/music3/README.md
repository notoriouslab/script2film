# tools/music3：MiniMax Music 3（需要有 Google Colab 帳號）

選用。用 MiniMax Music 3 生成一首有歌詞的歌或一段純配樂，生成在你自己 Google 帳號的 Colab GPU 上跑。做好的 WAV 照 Optional C 的方式當成片的背景音樂（`doc.json` 的 `bgm.src`）。

目前只有手動流程：在 Colab 開一份 notebook，貼下面的程式。還沒有像 `tools/h3` 那樣的轉接程式。

## 先讀授權

MiniMax-Music3 Community License（MIT 式）**沒有地區限制**。要遵守的：

- 保留版權聲明，遵守使用政策。公開發布的成品要標示是 AI 生成（YouTube 上傳加 `--synthetic`）。
- 歌詞的著作權要是你的。別人的詩歌、歌詞不能拿來生成。
- 年營收超過 2,000 萬美元要另外取得授權；把它包成服務給別人用，要有防濫用機制。

全文：https://huggingface.co/MiniMaxAI/MiniMax-Music3

## 要什麼

| | |
|---|---|
| 訂閱 | **Google AI Pro**（附 Colab 運算單元） |
| 執行階段 | L4（24 GB，程式會自動開 CPU offload）或 A100 |
| 這台電腦 | 不需要顯示卡。模型每次開機下載到 Colab 上 |

## 用法

在 Colab 新增 notebook，執行階段選 L4 或 A100，依序執行：

```python
!pip install -q git+https://github.com/huggingface/diffusers transformers accelerate soundfile
```

```python
import torch, numpy as np, soundfile as sf
from diffusers import ModularPipeline, ComponentsManager

if torch.cuda.get_device_properties(0).total_memory < 40e9:      # L4：模型分批放進顯示卡
    manager = ComponentsManager(); manager.enable_auto_cpu_offload(device="cuda")
    pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3", components_manager=manager)
    pipe.load_components(dtype=torch.bfloat16)
else:
    pipe = ModularPipeline.from_pretrained("MiniMaxAI/MiniMax-Music3")
    pipe.load_components(dtype=torch.bfloat16); pipe.to("cuda")
```

```python
LYRICS = "[Intro]\n[Instrumental]\n\n[Verse]\n（你的歌詞）\n\n[Chorus]\n（你的歌詞）\n"
CAPTION = ("Global Metadata: ...（曲風、速度、情緒）\n\n"
           "Vocal Details: ...（人聲；純配樂就寫 No vocals at all）\n\n"
           "Arrangement: ...（每一段用什麼樂器、怎麼起伏）")
audio = pipe(prompt=CAPTION, lyrics=LYRICS, audio_duration=60.0,
             generator=torch.Generator("cuda").manual_seed(7), output="audios")[0]
wav = audio.T.detach().cpu().float().numpy() if torch.is_tensor(audio) else np.asarray(audio).T
sf.write("/content/song.wav", wav, pipe.sampling_rate)
```

- 歌詞用 `[Verse]`、`[Chorus]`、`[Bridge]`、`[Instrumental]` 這類段落標記。純配樂只放 `[Instrumental]`。
- `CAPTION` 分三段寫：整體（曲風、BPM、情緒）、人聲、編曲。寫得越具體越好控制。
- 做完從左邊的檔案欄把 `song.wav` 下載回來，然後**到「執行階段」選「中斷連線並刪除執行階段」**，不然會一直扣運算單元。

## 接回片子

把 WAV 放進片的資料夾，`doc.json` 的 `bgm.src` 指向它，`bgm.credit` 寫「MiniMax Music 3（AI 生成）」。其他步驟見 `docs/FLOW.md` 的 Optional C。

## 花費與時間（2026-11-18，L4）

| | |
|---|---|
| 裝套件、下載並載入模型 | 約 4 分鐘（載入 103 秒） |
| 60 秒的歌 | 約 5 分鐘（每秒音樂約 5 秒），顯示卡記憶體峰值 19.4 GB |
| 4 分鐘的歌（推估） | 約 20 分鐘 |
| 一次開機、生成一首 60 秒 | 約 0.3–0.5 點 |

輸出是 44.1 kHz 立體聲 WAV。

## 已知

- 台語歌詞唱得出來，但要能用還得多試幾個 seed、改寫 `CAPTION`。第一次就能用的機率不高。
- Mac 本機（MPS）還沒有成熟的跑法，2026-11-18 不建議。
