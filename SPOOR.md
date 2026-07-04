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
