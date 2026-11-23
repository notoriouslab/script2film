"""YouTube channel report (Analytics API v2, read-only).

  <python> tools/youtube/yt_stats.py auth                 # once per channel: opens the browser, saves a read-only token
  <python> tools/youtube/yt_stats.py report [--days 90] [--top 20] [--out report.json]
  <python> tools/youtube/yt_stats.py retention <video ID> [--days 365]   # share of viewers still watching at each point

Thumbnail impressions and click-through rate are not in Analytics API queries (only in Studio or the
Reporting API's bulk reach reports), so this tool does not report them.

Uses its own token (youtube_analytics_token[_<YT_ACCOUNT>].json in the same folder as yt_upload.py),
so adding read scopes never invalidates the upload token. Needs "YouTube Analytics API" enabled
in the Google Cloud project that owns youtube_client_secret.json
(or youtube_client_secret_<YT_ACCOUNT>.json when that file exists).
"""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[2] / "tools/config"))
import s2f_config; s2f_config.load()
import argparse, datetime as dt, json, os, sys
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yt_paths import creds_dir  # noqa: E402

HOME = creds_dir(os.environ, Path.home())
_acct = os.environ.get("YT_ACCOUNT", "").strip()
# 各帳號可用自己的 OAuth 用戶端（youtube_client_secret_<名稱>.json）；沒有就用共用的那份
SECRET = next((p for p in [HOME / f"youtube_client_secret_{_acct}.json"] if _acct and p.exists()), HOME / "youtube_client_secret.json")
TOKEN = HOME / (f"youtube_analytics_token_{_acct}.json" if _acct else "youtube_analytics_token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]


def creds(interactive=False):
    c = Credentials.from_authorized_user_file(str(TOKEN)) if TOKEN.exists() else None
    if c and not set(SCOPES) <= set(c.scopes or []):
        c = None
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request())
        except RefreshError:
            c = None
    if not (c and c.valid):
        if not interactive:
            sys.exit("✗ not authorized: run yt_stats.py auth first")
        c = InstalledAppFlow.from_client_secrets_file(str(SECRET), SCOPES).run_local_server(port=0, prompt="consent")
    TOKEN.write_text(c.to_json())
    TOKEN.chmod(0o600)
    return c


def query(ya, start, end, metrics, **kw):
    """One Analytics query -> list of dicts. Returns None (and prints why) when a metric is not available."""
    try:
        r = ya.reports().query(ids="channel==MINE", startDate=start, endDate=end, metrics=metrics, **kw).execute()
    except HttpError as e:
        print(f"✗ query failed ({metrics}): {e.reason if hasattr(e, 'reason') else e}", file=sys.stderr)
        return None
    cols = [h["name"] for h in r.get("columnHeaders", [])]
    return [dict(zip(cols, row)) for row in r.get("rows", [])]


def main():
    ap = argparse.ArgumentParser(description="Read-only channel report: views, watch time, retention, traffic sources.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    rp = sub.add_parser("report")
    rp.add_argument("--days", type=int, default=90)
    rp.add_argument("--top", type=int, default=20)
    rp.add_argument("--out", default="")
    rt = sub.add_parser("retention")
    rt.add_argument("video_id")
    rt.add_argument("--days", type=int, default=365)
    a = ap.parse_args()
    a.days = max(1, min(a.days, 3650))
    if a.cmd == "report":
        a.top = max(1, min(a.top, 50))   # videos.list takes at most 50 IDs

    c = creds(interactive=a.cmd == "auth")
    yt = build("youtube", "v3", credentials=c)
    ch = yt.channels().list(part="snippet,statistics", mine=True).execute().get("items", [])
    if not ch:
        sys.exit("✗ no channel on this account")
    info = {"id": ch[0]["id"], "title": ch[0]["snippet"]["title"], "subscribers": ch[0]["statistics"].get("subscriberCount")}
    if a.cmd == "auth":
        print(json.dumps(info, ensure_ascii=False))
        return

    ya = build("youtubeAnalytics", "v2", credentials=c)
    end = dt.date.today()
    start = end - dt.timedelta(days=a.days)
    s, e = start.isoformat(), end.isoformat()
    if a.cmd == "retention":
        rows = query(ya, s, e, "audienceWatchRatio", dimensions="elapsedVideoTimeRatio", filters=f"video=={a.video_id}") or []
        for r in rows:
            print(f'{r["elapsedVideoTimeRatio"]:.2f}\t{r["audienceWatchRatio"]:.2f}')
        return
    watch = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained"
    out = {"channel": info, "range": [s, e],
           "totals": query(ya, s, e, watch),
           "traffic_sources": query(ya, s, e, "views,estimatedMinutesWatched",
                                    dimensions="insightTrafficSourceType", sort="-views"),
           "top_videos": query(ya, s, e, watch, dimensions="video", sort="-views", maxResults=a.top)}
    vids = out["top_videos"] or []
    if vids:
        meta = yt.videos().list(part="snippet,contentDetails", id=",".join(v["video"] for v in vids)).execute().get("items", [])
        names = {m["id"]: (m["snippet"]["title"], m["snippet"]["publishedAt"][:10], m["contentDetails"]["duration"]) for m in meta}
        for v in vids:
            v["title"], v["published"], v["duration"] = names.get(v["video"], ("?", "?", "?"))
    text = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
