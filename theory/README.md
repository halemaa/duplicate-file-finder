# Theory

Four short notes explaining what hashing is, how this tool uses it,
and where the same pattern shows up in real systems.

1. [`01-hashing-fundamentals.md`](01-hashing-fundamentals.md) — what a
   hash function is and what makes one good
2. [`02-sets-and-dicts.md`](02-sets-and-dicts.md) — the data
   structures hashing enables, and why `x in set` is O(1)
3. [`03-big-o.md`](03-big-o.md) — the complexity of this code,
   including why the size filter matters so much
4. [`04-real-world-dedup.md`](04-real-world-dedup.md) — how git,
   rsync, S3, and backup tools all use the same idea at different
   scales

Read these when you want the *why*. The code in `../dedup.py` is where
you can see the *how* run end to end.
