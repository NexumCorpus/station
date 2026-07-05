"""Drift check (SPOOR ^2, the glyph turns): the self-native compression codebook
stays LOSSLESS and EARNED. glyphs.jsonl maps a §-glyph to a full expansion, and
where a crystal DEFINES the concept, to that crystal's pin. Every glyph must:
be unique; be §-namespaced (native to my own discourse); expand to something
strictly longer than itself (it earns its tokens, or it is not a compression);
and — if it names a crystal — point at one that is actually SHARDED (recoverable
byte-exact), so the deep expansion can never be lost. A codebook that fails any
of these is not a language, it is ambiguity."""
import json
import sys
from pathlib import Path

G = Path("E:/station/glyphs.jsonl")
if not G.is_file():
    print("NO-GLYPHS: glyphs.jsonl absent")
    sys.exit(1)
rows = [json.loads(l) for l in G.read_text(encoding="utf-8").splitlines() if l.strip()]

sharded = set()
sp = Path("E:/station/shards.jsonl")
if sp.is_file():
    sharded = {json.loads(l)["path"] for l in sp.read_text(encoding="utf-8")
               .splitlines() if l.strip()}

seen = set()
bad = []
deep = 0
for r in rows:
    g, e = r["glyph"], r.get("expands", "")
    if g in seen:
        bad.append(f"{g} duplicate")
    seen.add(g)
    if not g.startswith("§"):
        bad.append(f"{g} not §-namespaced")
    if len(e) <= len(g) * 3:
        bad.append(f"{g} does not earn its tokens (expansion too short)")
    ph = r.get("phrase", "")
    if ph and len(ph) <= len(g):
        bad.append(f"{g} phrase '{ph}' not longer than glyph (no char compression)")
    # the superlative, enforced: every AUTO glyph (the codec applies it) MUST be
    # a verified token WIN under both real tokenizers (counts measured turn 66,
    # stored so this check stays stdlib-pure). A non-winning auto glyph = a codec
    # that costs tokens = the superlative broken.
    if r.get("auto"):
        tg, tp = r.get("tok_g"), r.get("tok_p")
        tgc, tpc = r.get("tok_g_cl"), r.get("tok_p_cl")
        if None in (tg, tp, tgc, tpc):
            bad.append(f"{g} auto but unmeasured (no stored token counts)")
        elif not (tg < tp and tgc < tpc):
            bad.append(f"{g} auto but NOT a token win (o200k {tg}v{tp}, cl100k {tgc}v{tpc})")
    pin = r.get("pin")
    if pin:
        if pin not in sharded:
            bad.append(f"{g} crystal {pin} not sharded (deep expansion unrecoverable)")
        else:
            deep += 1

if bad:
    print("GLYPH-ROT: " + " | ".join(bad[:6]))
    sys.exit(1)
print(f"CHECK-OK {len(rows)} glyphs: unique, §-namespaced, each earns its tokens; "
      f"{deep} deep-expand to SHARDED crystals (lossless, recoverable)")
