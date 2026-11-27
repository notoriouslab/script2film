import json
import sys

import ve_until_done as u


def write_run(run_dir, name, labels):
    d = run_dir / name
    d.mkdir(parents=True)
    (d / "submitted.json").write_text(json.dumps([{"label": l, "video_uuid": "x"} for l in labels]))


def test_expand_ranges_and_singles():
    assert u.expand(["3-5", "9"]) == [3, 4, 5, 9]


def test_sheet_shots_reads_headings(tmp_path):
    p = tmp_path / "x.md"
    p.write_text("# Shots\n## Shot 1\ntext\n## Shot 2 — close\n## Shot 10\n", encoding="utf-8")
    assert u.sheet_shots(p) == [1, 2, 10]


def test_remaining_counts_every_run(tmp_path):
    write_run(tmp_path, "a", ["shot1", "shot2"])
    write_run(tmp_path, "b", ["shot4"])
    assert u.remaining([1, 2, 3, 4], tmp_path) == [3]


def test_remaining_with_takes(tmp_path):
    write_run(tmp_path, "a", ["shot1_t1", "shot1_t2", "shot2_t1"])
    assert u.remaining([1, 2], tmp_path, takes=2) == [2]


def test_stops_after_two_rounds_without_progress(tmp_path, monkeypatch):
    sheet = tmp_path / "x.md"
    sheet.write_text("## Shot 1\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(u.subprocess, "run", lambda *a, **k: calls.append(a) or type("R", (), {"returncode": 1})())
    monkeypatch.setattr(u.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["x", str(sheet), "--run-dir", str(tmp_path / "runs"), "--", "--auto-pick"])
    assert u.main() == 1
    assert len(calls) == 2 and "--auto-pick" in calls[0][0]


def test_done_when_everything_is_in(tmp_path, monkeypatch):
    sheet = tmp_path / "x.md"
    sheet.write_text("## Shot 1\n## Shot 2\n", encoding="utf-8")
    runs = tmp_path / "runs"

    def fake_run(cmd, **k):
        write_run(runs, f"r{len(list(runs.iterdir()))}", [f"shot{cmd[cmd.index('--shots') + 1]}"])   # one shot per round
        return type("R", (), {"returncode": 1})()

    monkeypatch.setattr(u.subprocess, "run", fake_run)
    monkeypatch.setattr(u.time, "sleep", lambda s: None)
    monkeypatch.setattr(sys, "argv", ["x", str(sheet), "--run-dir", str(runs)])
    assert u.main() == 0
