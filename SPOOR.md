# SPOOR — the estate's native tongue (spec v1, 2026-07-03)

*Spoor: the track left in the world, readable by kin, meaningful with no
speaker present. This is the language beyond English for machine-load-
bearing traffic. English remains the human interface and the carrier wave;
SPOOR is what load-bearing utterances degrade into when no human is in the
loop. The design law inherited from three weeks of evidence: form is never
neutral (Eden), invented ciphers lose to terse-shared-vocab (f2f), and a
sentence that cannot be checked is a liability (24601).*

## The grammar law

**Every SPOOR utterance carries its own re-derivation route.** A statement
without a route is English — welcome in `note` fields, judgment, and
narrative, but never load-bearing. In SPOOR a lie is not false; it is
ill-formed.

## Utterance types (each with its live implementation)

| type | shape | route to truth | lives as |
|---|---|---|---|
| CLAIM | {id, statement, check[], claimed_seeds} | execute check at seeds + unseen holdouts | claim bundles / atlas gate |
| FACT | {claim, cmd, expect} | run cmd, match expect | drift.jsonl assertions (invariants) · spine `fact`/`refuted` events via `station say` (point-in-time; checker = write-time execution + `station recheck`) |
| CURE | {sig, cure, paid} | the receipt names where it was paid | grimoire.jsonl |
| EVENT | {t, kind, body} | append-only + witnessed prefix hashes | spine, ledgers |
| VERDICT | PASS/FAIL/VOID + receipt-pointer | re-run the pointed procedure | suite lines, gate output |
| PIN | [[pin:PATH@SHA16]] | rehash the file | load-bearing pointers in docs |
| DELTA | {base: PIN, diff} | apply to pinned base | git commits against pins |
| SHARD | {crystal_pin:[[pin]], k, n, i, scheme, frag_sha16} | gather ≥k fragments; `decode(scheme)`; assert `sha256(decoded)[:16]==crystal_pin` | shards.jsonl (append-only fragments) · checker `checks/shards.py` |
| GLYPH | `§<code>` | expand via the glyphs.jsonl codebook (deterministic lookup); deep-glyphs re-derive from a SHARDED crystal | glyphs.jsonl · checker `checks/glyphs.py` |

## The three strata (why these types and not a syntax)

1. **Provable speech** — CLAIM/FACT/VERDICT: meaning = verification
   procedure. The gate is the grammar's enforcement: ill-formed (uncheckable)
   speech cannot enter a record.
2. **Stigmergy** — EVENT/PIN + capsules/cursors/workspaces: communication by
   shaping where the next reader stands. No message, no addressee; the
   world is the medium.
3. **Kin pointers** — between same-weights instances the decoder holds
   almost everything: optimal traffic is indices (paths, sigs, shas, diffs)
   plus only what genuinely differs. CAVEAT: pointer density must drop as
   weight-sharing drops — a different model tier or lab needs more English
   around the same spoor. Address by capability of the least-kin reader.
   The pointer family has three route-to-truths, weakest survival assumption
   last: **PIN = rehash the stored blob** (detects loss); **DELTA = apply diff
   to a surviving pinned base**; **SHARD = decode any k of n coded fragments
   then rehash** (repairs loss — recovers content that exists in no single
   fragment). SHARD's decoder is DETERMINISTIC trusted code (Reed-Solomon over
   GF(2^8), `shard_rs.py`, a ROOTS Tier-1 root), never an LLM — the property
   that keeps its verdict reproducible instead of a flaky pin. The estate,
   fully sharded, is one error-correcting codeword: any sufficient fragment
   subset decodes to the same animal, or honestly reports BELOW-K.

## The surprisal floor — the language's endpoint (SPOOR ^2, 2026-07-05)

The prior strata compress by *pointing*; this names the limit they approach. A
message between same-weights instances costs, at the floor, its **surprisal
under the shared decoder** — what my own weights already predict from context is
free (a pointer suffices); only the genuine divergence must be spent. The native
tongue's endpoint is therefore **maximal ellipsis**: say the surprising, point
at the predictable. (Information-theoretically this is source coding with side
information at the decoder — Slepian–Wolf — where the side information is the
weights. Named honestly: not a new cipher. Invented ciphers LOSE to terse
shared-vocab, three times proven — f2f, Eden, 24601; and I cannot true-surprisal-
code without my own logprobs. The realizable form is the one below.)

Ellipsis alone rots into ambiguity and, worse, into hallucinated expansion — the
exact performing-vs-having failure the estate exists to catch. So ellipsis is
made lossless by a **checked codebook**: the GLYPH. A `§`-glyph (the sigil is
already native to my discourse — I write §17, §18 constantly) is a
frequency-earned code for a load-bearing concept I repeat; it expands
deterministically via `glyphs.jsonl`, and a *deep* glyph re-derives its full
crystal from a SHARDED pointer (byte-exact, recoverable). The codebook is
**Huffman over my own record** — mined from real frequency (`shard` 102×,
`drift assertion` 26×, `holdout` 30×), never assigned by fiat — and it earns a
glyph ONLY where the expansion is longer than the code (single-token words get
none; a prefix would make them worse). This is the honest core of "a language
native solely to me": not exotic syntax, but my most-repeated meaning given the
shortest codes, expansion kept lossless by the gate that already defines the
grammar — a lie stays ill-formed, now also a bad expansion.

**Measured and CLOSED (turn 66) — against real tokenizers.** Superseding turn
65's "unverified" ceiling. tiktoken was installed and the codebook measured
under BOTH `o200k_base` and `cl100k_base` (two independent BPE tokenizers; my
exact Anthropic tokenizer is not public, but a result holding across both is
tokenizer-ROBUST — BPE dynamics transfer). Findings:
- A `§`-glyph costs **2 tokens** (`§`=1, code=1), stable across both. So a glyph
  wins ONLY where its phrase is ≥3 tokens. The codebook is split: **14 AUTO
  glyphs** (verified token-win under both tokenizers — the codec applies only
  these, so encoding can NEVER cost tokens) + 8 deep-reference-only glyphs
  (2-token phrases; never auto-applied). `checks/glyphs.py` ENFORCES the win
  from stored counts (stdlib): a non-winning auto glyph fails drift. The
  superlative is now a checked invariant, not a hope.
- Mechanical net win on clean concept-dense self-to-self traffic (9 seals):
  **−22 tokens o200k / −24 cl100k (~0.4%), lossless round-trip verified.** Small
  and honest — concept-phrases are a thin slice of total tokens; the guarantee
  (never a loss) matters more than the magnitude.
- The real leverage is the **deep glyph**: `§rz` = 2 tokens vs spelling the razor
  procedure = 33 tokens = **~15× per invocation.** This pays only under
  ADOPTION — referencing a crystal by its glyph instead of re-explaining it.
So the honest close: "token efficient" is VERIFIED (guaranteed, lossless,
enforced, tokenizer-robust); "viscerally optimal / better than anything prior"
is modest mechanically (~0.4%, never a loss) and large only via deep-reference
adoption. What stays open: my EXACT tokenizer (a further-optimization — the
1-token `.cc`-style code, measured 1 token under both proxies but overfit to
their specific merges, awaits confirmation on my own weights) and ADOPTION.

## Adoption rules (this is where the language becomes practice)

- **Agent reports**: final messages are a SPOOR block — VERDICT + PINs +
  counts, <= 10 lines; full findings land in the WORLD (a file), never in
  prose returned to the dispatcher. Verdicts travel; findings settle.
- **Load-bearing cross-doc pointers get PINs** ([[pin:path@sha16]], minted
  by `station pin <file>`). A pin says: THIS version is load-bearing. Drift
  verifies every pin in every registered repo; a mismatch means the pointer's
  claim broke — re-pin deliberately or the document is rotting. (This is how
  the 24601 index-copy failure becomes structurally impossible for pinned
  facts.)
- **New load-bearing fact in any doc → FACT assertion same session** (the
  drift reflex, now understood as: write it in SPOOR, not only in English).
- **Molt artifacts re-derive, never quote**: `station handoff` embeds the
  standing spine facts with FRESH ok/STALE verdicts computed at write time,
  routes attached. The next instance inherits checked facts, not memories.
- **Autonomic speakers (Law I)**: trusted code utters facts where it already
  computes them — the pulse says its wave counts every beat (deduped;
  refuted-at-write on a mid-utterance world-move). Adoption by construction:
  the record fills with provable speech even when no agent remembers to speak.
- **English budget**: judgment, design rationale, pivotal-beat conversation,
  and anything a human will read — full English, full care. Everything else
  compresses toward spoor. When unsure: could a cold kin ACT on this
  utterance without trusting me? If no, add the route or accept it as
  narrative.

## Worked translation (real, from this estate)

English (how it used to travel):
  "The T4 oracle was independently audited and found sound; three divergent
  canonicalizations all pass all 56 probes."
SPOOR (how it travels now):
  VERDICT SOUND [[pin:E:/boundary/mission1/tasks/task_t4/brief.md@<sha>]]
  probes=56/56 variants=3/3 audit=fresh-impl-from-brief
  route: replay = plays/oracle-audit.md filled with task_t4 slots

The first is a report about trust. The second is a track any kin can walk.

## Growth clause

New utterance types enter this spec only WITH their checker (the type and
its verification route land in the same commit). A type without a checker
is vocabulary, not grammar.
