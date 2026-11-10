# 3 — Big O of this code

## The headline

- **Time**: O(n + B) where n = number of files, B = total bytes read
- **Space**: O(n)

The interesting part is that `B` — the bytes we actually read from
disk — is far smaller than "all bytes on disk" because of the
size-filter trick.

## Why the naive version would be too slow

**Naive: hash every file.**

- Walk the tree: O(n)
- For each file, hash its full contents: O(file_size)
- Total bytes read: everything on disk

If your disk has 100 GB of files, the naive version reads 100 GB.
At ~500 MB/sec on an SSD, that's 200 seconds. Tolerable for a toy,
annoying for daily use.

**Even worse: pairwise comparison.**

- For every pair of files `(i, j)` where `i < j`, read both and
  compare byte by byte
- With 100,000 files, that's ~5 billion pairs
- Completely unusable at scale

## What this tool does instead

**Stage 1 — size filter: O(n) time, no disk reads.**

```python
by_size: dict[int, list[Path]] = defaultdict(list)
for path in _iter_files(root):
    size = path.stat().st_size            # metadata only — no read
    by_size[size].append(path)            # O(1) dict insert
```

`stat()` is a filesystem metadata call. It doesn't read file
contents — it reads the inode. Blazing fast, hundreds of thousands
per second.

After stage 1:
- Every file has been visited once: O(n)
- No file contents have been read: 0 bytes read
- We have a dict grouping files by size

**Stage 2 — hash only the survivors: O(S × avg_group_size + B') time.**

```python
for size, candidates in by_size.items():
    if len(candidates) < 2:
        continue   # unique size → can't be a duplicate, SKIP ENTIRELY
    for path in candidates:
        digest = _file_sha256(path)       # reads file contents
        by_hash[digest].append(path)
```

Here's the magic: we skip the `continue` branch entirely for files
with a unique size. On a typical disk with photos, videos, documents
— most files have unique sizes. So only a small fraction of files
make it past the filter.

Let `B'` = bytes we actually read (hashing cost). On a disk where
80% of files have a unique size, `B' ≈ 0.2 × B`. We skip 80% of the
reading entirely.

## Measured difference

Imagine 100,000 files totalling 100 GB.

| Strategy | Files hashed | Bytes read | Time (SSD at 500 MB/s) |
|---|---|---|---|
| Naive (hash every file) | 100,000 | 100 GB | ~200 seconds |
| Pairwise bytes compare | 100,000² / 2 | astronomical | days |
| **This tool** | ~15,000 (survivors) | ~15 GB | **~30 seconds** |

Order-of-magnitude speedup from one simple filter.

## Why the size filter works

Two files can have the same content only if they have the same
size. Different sizes → different content → not duplicates. That's
a necessary condition, not sufficient — two files can share a size
and still differ.

The size filter is a **cheap pre-check** that prunes the expensive
check. Pattern: whenever you have an expensive test, look for a
cheap necessary condition first.

This pattern shows up everywhere:
- **Bloom filters** before database lookups
- **Content-type header** check before parsing a file
- **Cached ETag** before downloading a resource
- **Index scan** before a full table scan

## Hash cost, specifically

SHA-256 processes ~500 MB/sec on modern CPUs. For an N-byte file,
hashing is O(N) in the file size. We read the file in 64 KB chunks
so memory stays bounded at 64 KB regardless of file size — a 5 GB
video hashes with 64 KB of RAM.

**Why chunked?** Reading the whole file with `path.read_bytes()`
would allocate N bytes of RAM for an N-byte file. On a 2 GB file
that's a 2 GB allocation, which might OOM on constrained machines
or just be rude. Streaming is cheap insurance.

## Space complexity

- `by_size` dict: O(n) entries, each pointing to a list of paths
- `by_hash` dict: at most O(n) entries across all size groups
- `_file_sha256` streaming buffer: O(1) — 64 KB constant
- Output list of DuplicateGroups: at most O(n)

**Total: O(n).**

## How to narrate this in an interview

> "I used a two-stage filter. Stage 1 groups files by size using
> stat() metadata only — no file reads. Files with a unique size
> can't possibly be duplicates, so I skip them. Stage 2 hashes only
> files that have a size-twin, using SHA-256 streamed in 64 KB
> chunks to bound memory. The hash function determines content
> equality in O(1) comparisons after the hash is computed.
>
> Overall: O(n) time plus O(B') for hashing, where B' is the bytes
> of files-that-might-be-duplicates — typically much less than total
> disk space. Space is O(n) for the two hash maps."

That's a senior-sounding analysis of a 100-line function.

## The meta-lesson

**Big O analysis isn't about the dominant term alone.** It's about
understanding *which* inputs make your algorithm slow and whether
you can prune them cheaply. The size filter doesn't change this
tool's asymptotic complexity — it's still O(n + B). But the
*constants* in front of B are dramatically smaller, and in
engineering the constants matter.
