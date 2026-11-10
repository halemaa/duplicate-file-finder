"""
Scan a folder for duplicate files and print a report.

Usage:
    python find_dupes.py                       # scans current folder
    python find_dupes.py C:\\Users\\me\\Downloads
    python find_dupes.py ~/Pictures --min-size 100000
    python find_dupes.py . --summary-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dedup import find_duplicates, format_bytes


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find duplicate files (byte-identical) in a folder tree."
    )
    parser.add_argument(
        "root", nargs="?", default=".",
        help="directory to scan (default: current folder)",
    )
    parser.add_argument(
        "--min-size", type=int, default=1,
        help="ignore files smaller than N bytes (default: 1)",
    )
    parser.add_argument(
        "--summary-only", action="store_true",
        help="just print totals, don't list each group",
    )
    parser.add_argument(
        "--follow-symlinks", action="store_true",
        help="follow symbolic links (default: do not)",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    print(f"Scanning {root}")
    print(f"  min-size: {args.min_size} bytes  ·  follow-symlinks: {args.follow_symlinks}")
    print()

    groups = find_duplicates(
        root,
        min_size=args.min_size,
        follow_symlinks=args.follow_symlinks,
    )

    if not groups:
        print("No duplicate files found.")
        return 0

    total_wasted = sum(g.wasted_bytes for g in groups)
    total_files = sum(len(g.paths) for g in groups)

    print(f"Found {len(groups)} duplicate group(s), "
          f"{total_files} files, "
          f"{format_bytes(total_wasted)} wasted space.")
    print()

    if args.summary_only:
        return 1

    for i, group in enumerate(groups, 1):
        print(
            f"Group {i}: {len(group.paths)} copies  ·  "
            f"{format_bytes(group.size_bytes)} each  ·  "
            f"{format_bytes(group.wasted_bytes)} wasted"
        )
        print(f"  sha256 {group.sha256[:16]}...")
        for path in group.paths:
            print(f"    {path}")
        print()

    return 1   # non-zero so this can gate a CI check or script


if __name__ == "__main__":
    sys.exit(main())
