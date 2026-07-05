"""Drift check (the shard turns): the SHARD primitive's life-or-death gate, and
SPOOR's growth-clause checker for the SHARD utterance type. Every sharded
crystal must reconstitute BYTE-EXACT from EVERY k-of-n subset of its surviving
fragments and rehash to its crystal_pin — the property that makes a shard a
repair, not just a checksum. Rejects k>=n (a pin wearing shard costume).
Positive control: at least one crystal must reconstitute, or the check is
vacuous (exit 1, per vacuity_audit doctrine). A mis-decode fails the rehash and
is reported, never silently accepted."""
import base64
import hashlib
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, "E:/station")
from shard_rs import decode  # noqa: E402

SHARDS = Path("E:/station/shards.jsonl")
if not SHARDS.is_file():
    print("NO-SHARDS: shards.jsonl absent — the primitive minted nothing")
    sys.exit(1)

rows = [json.loads(l) for l in SHARDS.read_text(encoding="utf-8").splitlines()
        if l.strip()]
by_pin = {}
for s in rows:
    by_pin.setdefault(s["crystal_pin"], []).append(s)

MAXPAT = 64          # cap k-subsets tested per crystal
reconstituted = 0
bad = []
for pin, frs in by_pin.items():
    k, n, olen = frs[0]["k"], frs[0]["n"], frs[0]["orig_len"]
    if k >= n:
        bad.append(f"{pin} k>=n (pin in shard costume)")
        continue
    # fragment integrity: each stored fragment hashes to its frag_sha16
    frags = {}
    for s in frs:
        fb = base64.b64decode(s["frag_b64"])
        if hashlib.sha256(fb).hexdigest()[:16] != s["frag_sha16"]:
            bad.append(f"{pin} frag#{s['i']} corrupt")
            continue
        frags[s["i"]] = fb
    if len(frags) < k:
        bad.append(f"{pin} BELOW-K {len(frags)}/{k}")
        continue
    ok = True
    for sub in list(itertools.combinations(sorted(frags), k))[:MAXPAT]:
        rec = decode({i: frags[i] for i in sub}, k, n, olen)
        if rec is None or hashlib.sha256(rec).hexdigest()[:16] != pin:
            bad.append(f"{pin} subset{sub} FAILED rehash")
            ok = False
            break
    if ok:
        reconstituted += 1

if bad:
    print("SHARD-ROT: " + " | ".join(bad[:5]))
    sys.exit(1)
if reconstituted == 0:
    print("SHARD-VACUOUS: no crystal reconstituted (positive control empty)")
    sys.exit(1)
print(f"CHECK-OK {reconstituted} crystals reconstitute byte-exact from every "
      f"tested k-of-n subset and rehash to their pin (a shard repairs, not just detects)")
