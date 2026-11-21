"""等 TP My Videos 裡某張卡渲染完並下載（任何送出流程都可用，2026-11-21 為 Replicate Motion 寫）。
用法：python3 tp_wait.py <輸出.mp4> <TP 專案名>
最多等 60 分鐘；渲染失敗就以錯誤結束。用 tp_host 的找卡、下載函式，會反覆重新整理 TP 分頁，等待期間別在同一分頁操作。
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tp_host as t
label, out = sys.argv[2], Path(sys.argv[1])
t.go("#/my-videos", 5)
t0 = time.time()
while time.time() - t0 < 3600:
    t.ev("(()=>{location.reload();return 1})()"); time.sleep(8)
    c = t.card(label)
    if c is None: print("no card yet", flush=True); time.sleep(30); continue
    if t.busy(c): time.sleep(30); continue
    if any(w in c["text"].lower() for w in ("fail", "error")): sys.exit(f"FAILED {c['text']}")
    for _ in range(3):
        x, y = c["buttons"][1]; t.tp("download", x, y, out, timeout=300)
        if out.exists(): break
        time.sleep(5); c = t.card(label) or c
    print("DONE", out, out.exists(), f"{(time.time()-t0)/60:.0f} min"); break
