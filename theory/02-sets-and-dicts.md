# 2 — Sets and dicts as hash tables

## The data structures hashing makes possible

Every modern language has two data structures that live or die by
hashing:

- **A set** — a collection where "is X in it?" is O(1) on average
- **A dict (hash map)** — maps keys to values, where "look up X" is
  O(1) on average

In Python, these are `set` and `dict`. In JavaScript, `Set` and
`Map`. In Java, `HashSet` and `HashMap`. In Go, just `map`. Same
idea everywhere.

## How they work, briefly

Under the hood, a set or dict is an array of slots. To look up
whether `"apple"` is in the set:

1. Compute `hash("apple")` — a number
2. Take `hash % number_of_slots` — the slot index
3. Look in that slot

The lookup is constant time because computing the hash is constant
time (for a bounded-size key) and array access is constant time.

**Collisions happen** — two different keys can land in the same slot —
and a well-designed hash table handles them with chaining or open
addressing. Average case stays O(1); worst case is O(n), but with a
good hash function the worst case is vanishingly rare.

## Where this repo uses hashing

Look at `dedup.py`:

```python
by_size: dict[int, list[Path]] = defaultdict(list)

for path in _iter_files(root):
    size = path.stat().st_size
    by_size[size].append(path)
```

`defaultdict(list)` is a dict. When we `by_size[size]`, Python
computes `hash(size)` (an integer — hashes to itself), looks up the
slot, and returns the list (or creates an empty one if the key is
new). All O(1).

Then:

```python
by_hash: dict[str, list[Path]] = defaultdict(list)

for path in candidates:
    digest = _file_sha256(path)
    by_hash[digest].append(path)
```

Same pattern, just with string keys (the hex digests). Python
computes `hash(digest)` — a fast internal hash of the string, not
another SHA-256 — looks up the slot, done.

**Two layers of hashing in one function:**
- SHA-256 to fingerprint the file content (slow, cryptographic)
- Python's `hash()` to put the fingerprint in a dict (fast,
  structural)

## The pattern this unlocks: "group things by X"

Any time you want to group items by some key, reach for a dict:

```python
from collections import defaultdict

# Group by first letter
by_letter = defaultdict(list)
for word in words:
    by_letter[word[0]].append(word)

# Count occurrences
counts = defaultdict(int)
for word in words:
    counts[word] += 1

# Deduplicate while preserving order
seen = set()
result = []
for word in words:
    if word not in seen:
        result.append(word)
        seen.add(word)
```

Every one of those loops is O(n) because each `set` or `dict`
operation is O(1). Without hash tables, every one would be O(n²).

## Interview classics this unlocks

Almost every "hash map" question on LeetCode uses this pattern:

| Problem | The hash trick |
|---|---|
| Two Sum | Store `{value: index}` as you walk; for each element check if `target - element` is already in the map |
| Group Anagrams | Hash each word by its sorted letters; group them |
| Valid Anagram | Count characters in a dict; compare counts |
| Contains Duplicate | Walk once, put each value in a set; check before inserting |
| Longest Substring Without Repeating | Sliding window + set (see `log-anomaly-detector`'s theory!) |
| Subarray Sum Equals K | Prefix sum + dict |

Every one of them replaces an `O(n²)` nested loop with an `O(n)`
walk, by trading **memory** (the dict) for **time**. That trade is
almost always worth it.

## The two-minute heuristic

When you see a problem where you'd naively write:

```python
for i in range(n):
    for j in range(n):
        if some_relationship(arr[i], arr[j]):
            ...
```

...ask yourself: *can I rewrite the inner loop as a dict lookup?*
Usually you can. The dict holds "everything I've seen so far,"
keyed by whatever the relationship needs.

That one reframe turns O(n²) into O(n) more often than any other
single technique.

## Sets vs dicts — when to use which

- **Set**: "I just need to know if I've seen this before."
  Membership questions. Deduplication.
- **Dict**: "I need to associate this key with some value."
  Counting, grouping, looking something up.

If you'd use a dict with only `True` as every value — use a set
instead. It's cleaner and uses less memory.

## The one line to remember

> Hash tables trade memory for time. A dict is almost always worth
> the memory — because O(n) is almost always worth it over O(n²).
