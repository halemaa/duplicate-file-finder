# 4 — Where this pattern shows up for real

Once you've seen "hash the content, group by digest," you see it
everywhere. This note walks through the real systems that do what
this tool does — just at terabyte scale.

## Git

Every object Git stores (a file version, a commit, a tree) is
keyed by **SHA-1 of its content**. When you `git add` a file, Git
computes its SHA-1 and files the content under `.git/objects/XX/YYYY...`
(the first two hex digits are the folder; the rest is the filename).

This means:
- If you commit the exact same file content in two places, Git
  stores it **once**. Two branches with the same README reuse the
  same blob.
- Checking "did this file change?" is comparing SHA-1s — constant
  time.
- History is a tree of commits, each one pointing at a tree of
  blobs, each identified by its hash. You can verify any part of
  history by rehashing.

This is **content-addressable storage** — the file's address IS its
content fingerprint. Git invented a filesystem where you can't lie
about what a file contains.

The pattern in this repo (`by_hash[digest].append(path)`) is the
same pattern — we're just not storing the content, only the paths.

## rsync

rsync synchronises files between two machines efficiently. Instead
of transferring every byte, it:

1. Breaks each file into blocks of ~1 KB
2. Hashes each block on both sides (weak rolling hash + strong
   MD5)
3. Only transfers blocks whose hashes don't already exist on the
   destination

If you've ever rsync'd a 50 MB file after changing 3 lines in it,
you've watched the transfer take under a second because 99.99% of
blocks already matched.

Same idea. Just split into pieces, with hashes as the equality test.

## S3, Backblaze, Google Cloud Storage (deduplicated backup)

Most modern backup services do "client-side deduplication":

1. Split your files into chunks (fixed-size or content-defined)
2. Hash each chunk with SHA-256
3. Send the hash to the server
4. If the server already has that chunk (from you or any other
   customer), don't upload it

This is why "backup your photos" services can offer absurdly cheap
pricing — if ten million people all back up the same iPhone
screenshot, the server stores it **once**.

Backblaze's B2 and Borg Backup are two well-known implementations.

## IPFS, BitTorrent, Dat

Distributed file systems address content by hash, so anyone with the
hash can find and verify the content. BitTorrent breaks a file into
pieces, hashes each piece, puts them in a `.torrent` file. As you
download, each piece's hash is verified — a tampered piece is
rejected and re-requested.

The reason torrents are tamper-proof isn't trust — it's hashing.

## Docker image layers

A Docker image is a stack of layers. Each layer has a
**content-addressable digest** (SHA-256 of the layer's tar). When
you pull an image:

1. Docker checks which layer digests you already have locally
2. Only downloads the ones you're missing

This is why pulling `python:3.12-slim` the second time is almost
instant — the base layers are already cached.

Your `notes-api` repo uses this directly. Every push of your image
to GHCR reuses unchanged layers.

## Password storage (sort of — with a twist)

Storing a password? You never store the password itself — you store
a **salted hash** of it. When the user logs in, you hash their
submitted password with the same salt and compare the digests.

The twist: for passwords you want `bcrypt`, `argon2`, or `scrypt` —
*slow* hash functions designed to be hard to brute-force. SHA-256 is
too fast for password hashing; attackers can try billions per second.

## Browser caches, CDN caches

HTTP responses carry an `ETag` header: "if this resource's ETag is
unchanged, your cached copy is still valid." ETags are almost always
hashes of the response body. Same idea.

## Cheat detection in online games

Every binary your client uses gets hashed and sent to the server on
login. The server knows what hashes are legitimate and rejects
clients that don't match. Cheat engines that patch the binary are
caught by a hash mismatch.

## What this tool shows that you understand

If you walked an interviewer through this repo, you could honestly
say:

> "I built a deduplication tool. It's the same pattern Git, rsync,
> S3 dedup backups, Docker image layers, and CDNs use. I hash the
> content with SHA-256, group paths by hash in a dict, and report
> any hash with more than one path. I added a two-stage filter:
> group by file size first (metadata only, no reads), then hash
> only the files that have a size-twin — which skips maybe 80% of
> files on a typical disk. The pattern scales from 'my Downloads
> folder' to 'global content-addressable storage' with no change in
> approach."

That's a one-paragraph tour through five big real-world systems,
all unified by the same idea. The idea you can demonstrate in 150
lines of Python.

## The pattern, in one sentence

> If you can compare two things by comparing hashes of their
> contents, you've turned "comparing n² pairs" into "hashing n
> things once" — and that's often the whole game.
