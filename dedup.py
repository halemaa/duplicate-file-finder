"""
Find duplicate files in a directory tree.

A file is a "duplicate" of another when their contents are
byte-for-byte identical, regardless of filename or location.

Strategy (two-stage, fast):

  1. Walk the tree once. Group files by SIZE. Files with no size-twin
     cannot possibly be duplicates — skip them. This is the O(n) win:
     we avoid hashing most files on a typical disk.

  2. For each size group with >1 file, hash the contents (SHA-256,
     read in chunks so a 5 GB video doesn't blow out memory). Group
     by hash. Any hash group with >1 file is a real duplicate set.

Returns a list of groups, each group containing paths to files
with identical contents.
"""

from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class DuplicateGroup:
    """A set of files with identical contents."""
    size_bytes: int
    sha256: str
    paths: list[Path]

    @property
    def wasted_bytes(self) -> int:
        """Space you'd reclaim by keeping one copy and deleting the rest."""
        return self.size_bytes * (len(self.paths) - 1)


def _iter_files(root: Path, follow_symlinks: bool = False) -> Iterator[Path]:
    """Yield every regular file under `root`, depth-first."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                if p.is_file() and not p.is_symlink():
                    yield p
            except OSError:
                # permission denied, bad symlink, race with deletion — skip
                continue


def _file_sha256(path: Path, chunk_size: int = 64 * 1024) -> str:
    """Compute SHA-256 of a file by streaming it in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(
    root: Path,
    min_size: int = 1,
    follow_symlinks: bool = False,
) -> list[DuplicateGroup]:
    """
    Walk `root`, return groups of files that are byte-for-byte
    identical.

    Args:
        root: directory to scan
        min_size: ignore files smaller than this (default 1 byte, so
            empty files don't dominate the output)
        follow_symlinks: default False, safer — avoid infinite loops
            and accidentally traversing out of the intended tree

    Returns: a list of DuplicateGroup, sorted so the biggest
    space-savers come first.
    """
    # --- Stage 1: group by size -------------------------------------
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in _iter_files(root, follow_symlinks=follow_symlinks):
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size < min_size:
            continue
        by_size[size].append(path)

    # --- Stage 2: hash only files that have a size-twin -------------
    duplicates: list[DuplicateGroup] = []
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue   # unique size → cannot be a duplicate

        by_hash: dict[str, list[Path]] = defaultdict(list)
        for path in candidates:
            try:
                digest = _file_sha256(path)
            except OSError:
                continue
            by_hash[digest].append(path)

        for digest, group in by_hash.items():
            if len(group) >= 2:
                duplicates.append(
                    DuplicateGroup(size_bytes=size, sha256=digest, paths=sorted(group))
                )

    # Biggest space-savers first — most useful ordering for humans
    duplicates.sort(key=lambda g: g.wasted_bytes, reverse=True)
    return duplicates


def format_bytes(n: int) -> str:
    """Human-friendly byte count: 1234 -> '1.2 KB'."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} PB"
