import pytest

from ve_wallcuts import join_filter, parse_piece, wall_spans


def test_span_found_with_blurriest_frame():
    v = [100] * 10 + [10, 5, 8, 12] + [100] * 10
    assert wall_spans(v, fps=2) == [(5.0, 7.0, 5.5)]


def test_short_dip_is_not_a_wall():
    v = [100] * 10 + [5, 5] + [100] * 10
    assert wall_spans(v, fps=24) == []


def test_two_walls_and_span_at_clip_end():
    v = [100] * 5 + [1] * 4 + [100] * 5 + [1] * 3
    assert [s[:2] for s in wall_spans(v, fps=1)] == [(5.0, 9.0), (14.0, 17.0)]


def test_empty_and_bad_fps():
    assert wall_spans([], fps=24) == []
    assert wall_spans([1, 2, 3], fps=0) == []


def test_parse_piece_end_and_errors():
    assert parse_piece("b.mp4:3.55:end", lambda c: 10.04) == ("b.mp4", 3.55, 10.04)
    assert parse_piece("a:b.mp4:0:6.2", lambda c: 0) == ("a:b.mp4", 0.0, 6.2)
    with pytest.raises(ValueError):
        parse_piece("a.mp4:5:2", lambda c: 10)


def test_join_filter_trims_and_concats_in_order():
    fc = join_filter([(0, 0, 6.2), (1, 3.55, 6.45)])
    assert "[0:v]trim=0:6.2" in fc and "[1:a]atrim=3.55:6.45" in fc
    assert "afade=t=out:st=2.85:d=0.05" in fc
    assert fc.endswith("[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")
