#!/usr/bin/env python3
"""Keep calling ve_runner.py until every requested shot is submitted.

A long run stops partway now and then: VE answers "Error. Please try again later" about once every ten clips, a candidate
carousel still loading fails the image pick, or the browser closes under the runner. Each time this waits (default 180 s),
reads every <run-dir>/*/submitted.json and sends only the shots not yet submitted. It stops when all are in, after
--rounds rounds, or after two rounds in a row that submitted nothing (a login page or a broken run sheet: retrying won't help).

  python3 ve_until_done.py x.md --run-dir <film>/ve-runs                       # every shot in the run sheet
  python3 ve_until_done.py x.md --run-dir <film>/ve-runs --shots 49-96 3 7     # ranges and single shots
  python3 ve_until_done.py x.md --run-dir <film>/ve-runs -- --auto-pick --masters m.json   # after --: passed to ve_runner

Each round is its own runs/<ts>/ folder: collect each with ve_collect.py --submitted <that folder>/submitted.json.
"""
import argparse, glob, json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sheet_shots(path):
    """Shot numbers of the run sheet, from its "## Shot N" headings (no Playwright import needed)."""
    return [int(m[1]) for m in re.finditer(r"^## Shot\s*(\d+)", Path(path).read_text(encoding="utf-8"), re.M)]


def expand(items):
    """["49-52", "7"] -> [49, 50, 51, 52, 7]"""
    out = []
    for it in items:
        a, _, b = str(it).partition("-")
        out += list(range(int(a), int(b) + 1)) if b else [int(a)]
    return out


def submitted_counts(run_dir):
    """{shot number: videos submitted} over every run under run_dir; labels are shotN or shotN_tK."""
    n = {}
    for f in glob.glob(str(Path(run_dir) / "*" / "submitted.json")):
        for x in json.loads(Path(f).read_text(encoding="utf-8")):
            m = re.match(r"shot(\d+)", x.get("label", ""))
            if m:
                n[int(m[1])] = n.get(int(m[1]), 0) + 1
    return n


def remaining(wanted, run_dir, takes=1):
    done = submitted_counts(run_dir)
    return [s for s in wanted if done.get(s, 0) < takes]


def main():
    argv = sys.argv[1:]
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[:argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser(description="Call ve_runner.py until every requested shot is submitted.")
    ap.add_argument("runsheet")
    ap.add_argument("--run-dir", required=True, help="parent of the runs/<ts>/ folders (ve_runner --run-dir)")
    ap.add_argument("--shots", nargs="*", help="shot numbers or ranges (49-96); default: every shot in the run sheet")
    ap.add_argument("--takes", type=int, default=1, help="ve_runner --takes: a shot counts as done when this many are in")
    ap.add_argument("--rounds", type=int, default=25)
    ap.add_argument("--wait", type=int, default=180, help="seconds between rounds")
    a = ap.parse_args(argv)
    wanted = expand(a.shots) if a.shots else sheet_shots(a.runsheet)
    Path(a.run_dir).mkdir(parents=True, exist_ok=True)
    stalled = 0
    for r in range(1, a.rounds + 1):
        left = remaining(wanted, a.run_dir, a.takes)
        if not left:
            print(f"all {len(wanted)} shot(s) submitted", flush=True)
            return 0
        print(f"{time.strftime('%T')} round {r}: {len(left)} left", flush=True)
        cmd = [sys.executable, str(HERE / "ve_runner.py"), str(Path(a.runsheet).resolve()), "--shots", *map(str, left),
               "--run-dir", str(Path(a.run_dir).resolve()), *(["--takes", str(a.takes)] if a.takes != 1 else []), *extra]
        rc = subprocess.run(cmd, cwd=HERE).returncode
        after = remaining(wanted, a.run_dir, a.takes)
        print(f"{time.strftime('%T')} round {r}: exit {rc}, {len(left) - len(after)} submitted", flush=True)
        stalled = stalled + 1 if len(after) == len(left) else 0
        if stalled >= 2:
            print(f"two rounds in a row submitted nothing: stopping (check the last run.log). left: {after}", flush=True)
            return 1
        if after:
            time.sleep(a.wait)
    left = remaining(wanted, a.run_dir, a.takes)
    print(f"gave up after {a.rounds} rounds. left: {left}" if left else f"all {len(wanted)} shot(s) submitted", flush=True)
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
