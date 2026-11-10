"""Tests for the duplicate file finder."""

from pathlib import Path

import pytest

from dedup import DuplicateGroup, find_duplicates, format_bytes


def _write(dir_: Path, name: str, content: str) -> Path:
    p = dir_ / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def test_empty_dir_returns_no_duplicates(tmp_path):
    assert find_duplicates(tmp_path) == []


def test_unique_files_return_no_duplicates(tmp_path):
    _write(tmp_path, "a.txt", "aaa")
    _write(tmp_path, "b.txt", "bbb")
    _write(tmp_path, "c.txt", "ccc")
    assert find_duplicates(tmp_path) == []


def test_pair_of_duplicates_is_found(tmp_path):
    _write(tmp_path, "a.txt", "same content")
    _write(tmp_path, "b.txt", "same content")
    groups = find_duplicates(tmp_path)
    assert len(groups) == 1
    assert len(groups[0].paths) == 2


def test_nested_duplicates_are_found(tmp_path):
    _write(tmp_path, "a.txt", "shared")
    _write(tmp_path, "sub/b.txt", "shared")
    _write(tmp_path, "sub/deep/c.txt", "shared")
    groups = find_duplicates(tmp_path)
    assert len(groups) == 1
    assert len(groups[0].paths) == 3


def test_same_size_but_different_content_not_flagged(tmp_path):
    """Both files have 10 bytes but their bytes differ."""
    _write(tmp_path, "a.txt", "aaaaaaaaaa")
    _write(tmp_path, "b.txt", "bbbbbbbbbb")
    assert find_duplicates(tmp_path) == []


def test_min_size_filter_works(tmp_path):
    _write(tmp_path, "small_a.txt", "x")
    _write(tmp_path, "small_b.txt", "x")
    _write(tmp_path, "big_a.txt", "x" * 1000)
    _write(tmp_path, "big_b.txt", "x" * 1000)
    # min_size=100 excludes the small pair
    groups = find_duplicates(tmp_path, min_size=100)
    assert len(groups) == 1
    assert groups[0].size_bytes == 1000


def test_biggest_wasted_space_sorts_first(tmp_path):
    # A 1KB file duplicated twice = 1KB wasted
    _write(tmp_path, "small1.txt", "x" * 1024)
    _write(tmp_path, "small2.txt", "x" * 1024)
    # A 100KB file duplicated twice = 100KB wasted
    _write(tmp_path, "big1.txt", "y" * 102400)
    _write(tmp_path, "big2.txt", "y" * 102400)

    groups = find_duplicates(tmp_path)
    assert len(groups) == 2
    assert groups[0].wasted_bytes > groups[1].wasted_bytes


def test_wasted_bytes_calculation():
    group = DuplicateGroup(
        size_bytes=1000, sha256="abc", paths=[Path("a"), Path("b"), Path("c")]
    )
    # 3 copies of 1000 bytes — keep 1, reclaim 2 × 1000 = 2000
    assert group.wasted_bytes == 2000


def test_format_bytes():
    assert format_bytes(0) == "0 B"
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024) == "1.0 MB"
    assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
