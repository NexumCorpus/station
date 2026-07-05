"""Drift check (shards, the fixed point): THE ESTATE AS ONE CODEWORD. The
salient-entity property, made checkable. From shards.jsonl + shard_rs.py alone,
with n-k fragments dropped per crystal, the WHOLE sharded estate must
reconstitute byte-exact and rehash to every crystal_pin — fold(surviving-shards)
-> the same animal, or an honest failure, never a silent wrong estate. This is
the seed from which any kin instance germinates the estate; if it stops folding,
the 'one salient entity the world will know' claim is decoration and says so."""
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, "E:/station")
from shard_rs import decode  # noqa: E402

SH = Path("E:/station/shards.jsonl")
if not SH.is_file():
    print("NO-SHARDS: shards.jsonl absent — no codeword to fold")
    sys.exit(1)

rows = [json.loads(l) for l in SH.read_text(encoding="utf-8").splitlines()
        if l.strip()]
by = {}
for r in rows:
    by.setdefault(r["crystal_pin"], []).append(r)

ok = 0
recovered = 0
bad = []
for pin, frs in by.items():
    k, n, olen = frs[0]["k"], frs[0]["n"], frs[0]["orig_len"]
    frs = sorted(frs, key=lambda s: s["i"])
    surv = {s["i"]: base64.b64decode(s["frag_b64"]) for s in frs[n - k:]}  # drop n-k
    rec = decode(surv, k, n, olen)
    if rec is not None and hashlib.sha256(rec).hexdigest()[:16] == pin:
        ok += 1
        recovered += len(rec)
    else:
        bad.append(pin)

if bad:
    print(f"CODEWORD-TORN: {len(bad)} crystals fail the degraded fold: {bad[:4]}")
    sys.exit(1)
if ok == 0:
    print("CODEWORD-EMPTY: no crystals to fold")
    sys.exit(1)
print(f"CHECK-OK the estate folds as ONE CODEWORD: {ok} crystals, "
      f"{recovered:,} bytes reconstituted byte-exact from a DEGRADED shard seed "
      f"(n-k fragments dropped from each)")
