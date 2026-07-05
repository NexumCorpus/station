# PLAY: publish-prep — stage a public artifact to the decision gate

*Provenance: RDE field-report prep (2026-07-05), the estate's FIRST PUBLISH-beat
execution. Every rule below cost real rework this session, not designed. Pairs
with the PUBLISH pivotal beat in the north-star map. Next consumer: the EGE
preprint.*

## The shape (6 acts, stop at the human's go)

1. **ISOLATE on a working copy** — not the repo. For an untracked / self-contained
   artifact, a copy beats a worktree (the artifact isn't in the tree yet). Repo
   stays untouched; nothing pushed.
2. **VERIFY-THEN-EDIT** — verify every checkable claim against the repo BEFORE
   editing prose about it. A public artifact cannot rest on a subagent's say-so.
   Correct stale/false claims (this run: a "pending experiment" that had already run).
3. **VERIFY NUMBERS at ship state** — run the artifact's own checks (tests,
   check_claims) and confirm every headline figure. A number a public artifact's
   own cited source contradicts is a self-inflicted dunk.
4. **RED-TEAM adversarially** — 3 distinct lenses (fact-check vs repo, overclaim
   audit, hostile-outsider). Diversity catches what redundancy can't; single-lens
   misses the failure mode it doesn't hold.
5. **STAGE THE VERIFICATION BUNDLES *with* the artifact** — secret-scan them first.
6. **DECISION-GATE** — stop at the human's go. Irreversible/outward acts (publish,
   announce, repo-public) are the human's; prep is everything up to them.

## Paid anti-patterns (each cost real rework or a caught exposure this session)

- **"Available on request" for the proof bundle on a verifiability-branded piece
  = the highest-damage dunk.** Ship the bundle. (An edit meant to soften an
  overclaim CREATED the estate's single worst exposure — the red-team's #1 attack.)
- **Editing prose about a claim before verifying the claim** — the "not launched"
  line was false; the run had happened and produced a below-human null.
- **Bare future-dated model IDs unglossed** read as fabricated → date + source
  them in-repo.
- **Citing a non-public artifact whose numbers lag** (README count 138/97 vs live
  169) → don't cite what the reader can't check, or fix the lag first.
- **"We invented X" with zero prior-art** → reframe to "honest composition of
  known parts + the negative result" (attackable → bulletproof).

## +repo prerequisites (before making a research repo public)

Rotate live keys · bump stale self-reported counts to match the artifact ·
quarantine flaky tests · add a LICENSE. All mandatory before repo-public.

## Kill condition

If a published artifact ever ships with (a) a number its own cited source
contradicts, or (b) a withheld proof-bundle, the play failed to gate it — the
pre-flight is too loose or the red-team stage is decoration. Retire/tighten.
