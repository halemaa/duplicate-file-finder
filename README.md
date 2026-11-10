# duplicate-file-finder

A command-line tool that scans a folder tree and finds files with
byte-for-byte identical contents. Useful when your Downloads folder
is a mess, or when you've backed up the same photos to three places
over the years.

Written in pure Python, no dependencies. Demonstrates **hashing and
hash sets** — the technique behind content-addressable storage,
caches, and every "detect duplicates" system in computing.

## See it work

Scan your current folder:

```bash
python find_dupes.py
```

Scan your Downloads folder (Windows):

```bash
python find_dupes.py C:\Users\me\Downloads
```

Scan your pictures (Linux / macOS):

```bash
python find_dupes.py ~/Pictures
```

Only report duplicates over 100 KB:

```bash
python find_dupes.py ~/Pictures --min-size 100000
```

Example output:

```
Scanning /home/me/Pictures
  min-size: 1 bytes  ·  follow-symlinks: False

Found 3 duplicate group(s), 8 files, 15.2 MB wasted space.

Group 1: 4 copies  ·  3.8 MB each  ·  11.4 MB wasted
  sha256 7f3a9c2e4b1d8f6a...
    /home/me/Pictures/holiday-2024/beach-01.jpg
    /home/me/Pictures/holiday-2024-backup/beach-01.jpg
    /home/me/Pictures/sent-to-mum/beach-01.jpg
    /home/me/Pictures/whatsapp-dump/IMG-20241203-WA0012.jpg

Group 2: 2 copies  ·  2.1 MB each  ·  2.1 MB wasted
  ...
```

The tool only *reports* duplicates. It never deletes anything. Deletion
is your decision to make, file by file.

## How it's fast

The naive approach is to hash every file and compare hashes — O(n)
reads of every byte on disk. On a drive with 100,000 files that is
slow.

This tool uses a two-stage filter:

1. **Group by file size.** Walk the tree once, record each file's
   size. Files with no size-twin cannot possibly be duplicates — they
   are skipped entirely. On a real drive this eliminates ~95% of
   files from any hashing work.
2. **Hash only the survivors.** For each size group with more than
   one file, read the contents and hash them with SHA-256. Group
   by hash. A hash group of size ≥2 is a real duplicate set.

The hashing is streamed in 64 KB chunks, so a 5 GB video file uses
~64 KB of RAM to hash, not 5 GB.

## What's in the box

```
dedup.py                core: file walking, hashing, grouping
find_dupes.py           CLI
tests/test_dedup.py     9 passing tests
theory/                 written notes — hashing, big O, where this
                        pattern appears in the real world
```

## Read the theory

1. [Hashing fundamentals](theory/01-hashing-fundamentals.md) — what a
   hash function is, what makes one "good," the difference between
   SHA-256 and `hash()`
2. [Sets and dicts as hash tables](theory/02-sets-and-dicts.md) — where
   hashing shows up in everyday Python code, and why `x in set` is O(1)
3. [Big O of this code](theory/03-big-o.md) — why the size filter
   matters, line-by-line complexity
4. [Real-world dedup](theory/04-real-world-dedup.md) — how git,
   rsync, S3, and backup tools all use the same idea at different
   scales

## Try it

Run it on your Downloads folder. You will find things.

```bash
python find_dupes.py ~/Downloads --min-size 1000000
```

(`--min-size 1000000` = ignore files under 1 MB, so the report focuses
on space-wasters.)

## Extending

- **Delete mode** — add `--delete-and-keep-newest` or similar.
  Dangerous. Confirm with the user. Keep a trash folder.
- **Partial-content hash first** — for huge files, hash the first
  64 KB before hashing the rest. If two 2 GB files differ in the
  first 64 KB, we've saved reading 4 GB of disk.
- **Multithreaded hashing** — I/O bound, so threads help a lot
  on SSDs.
- **Across devices** — index each machine, upload the index to a
  central place, find duplicates across machines.
- **Fuzzy duplicates** — two JPEGs that are the same image but
  different encodings. This tool only finds byte-identical files;
  perceptual hashing (`imagehash` library) finds similar ones.

## Safety

- Does not follow symbolic links by default (avoids infinite loops
  and accidentally traversing out of the tree you asked about)
- Does not delete anything — it only reports
- Skips files it can't read (permission errors, race with deletion)
  silently rather than crashing
- Handles large files via streamed hashing — won't OOM on video files
