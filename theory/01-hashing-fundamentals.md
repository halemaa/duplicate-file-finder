# 1 — Hashing fundamentals

## What a hash function is

A **hash function** takes any input (a string, a file, a Python
object, a photograph) and returns a fixed-size number — the "hash"
or "digest."

```
"hello world"           ---> 7f83b1657ff1fc53b92dc181...
some 5 GB video file    ---> a948904f2f0f479b8f8197...
the number 42           ---> ba5ec51d07a4ac0e951608...
```

The output is always the same length. For SHA-256, it's 256 bits — 64
hex characters. The input can be any length at all.

## What makes a hash function "good"

Three properties, in rough order of importance:

**1. Deterministic.** The same input always produces the same output.
Hash `"hello"` today, hash it in ten years, same result.

**2. Uniform.** Different inputs produce outputs that look random and
spread evenly across the output space. Two slightly different inputs
should produce very different outputs:

```
"hello world"      ---> 7f83b1657ff1fc53b92dc18148a1d65...
"hello world!"     ---> 7509e5bda0c762d2bac7f90d758b5b22...
```

A one-character change produces a completely different digest. This
is called the **avalanche effect** and it's what makes hashes useful
as "fingerprints."

**3. Collision-resistant.** It should be computationally infeasible
to find two different inputs that produce the same output. For
SHA-256, nobody has ever found such a pair, and nobody is expected to
before the heat death of the universe.

(Older hashes like MD5 and SHA-1 are not collision-resistant anymore
— you can forge them. They're fine for detecting accidental
corruption, not for security.)

## Why we use hashing to find duplicates

Comparing two files byte by byte requires reading both in full and
comparing position by position. That's fine for two files. For
10,000 files, you'd have to compare ~50 million pairs — `n choose 2`.

Comparing two *hashes* requires looking up a 256-bit number. That's
constant time. We read each file once, compute its hash, and then
every comparison is cheap:

```
"Files A and B have the same hash?" → yes → they're duplicates
"Files A and C have the same hash?" → no  → they're not
```

Going from `n²` pairwise comparisons to `n` hash computations is the
whole point.

## SHA-256 vs Python's built-in `hash()`

Python's `hash(obj)` and SHA-256 look similar — both turn inputs into
numbers — but they're for different jobs:

| | **Python `hash()`** | **SHA-256** |
|---|---|---|
| Purpose | Fast set / dict keys | Content fingerprinting, security |
| Output size | Platform int (64 bits) | 256 bits |
| Deterministic across runs | Not for strings (hash randomisation) | Yes, always |
| Collision-resistant | No | Yes |
| Speed | ~ns per hash | ~GB/sec on modern CPUs |
| When to use | In-memory data structures | Files, passwords (with salt), IDs |

In this repo:
- `dedup.py` uses SHA-256 to fingerprint file contents (persistent,
  comparable across runs)
- The `defaultdict(list)` we group files into uses Python's built-in
  `hash()` under the hood (fast, in-memory)

**Both are hashes. Both let us put things in buckets. They just
operate at different scales.**

## The one thing to remember

> If two inputs produce the same SHA-256, they're the same input.
> If two inputs produce different SHA-256, they're different inputs.

That's the whole contract. Everything else — Git's object storage,
BitTorrent's chunk verification, IPFS's content addressing — is
built on top of that one promise.
