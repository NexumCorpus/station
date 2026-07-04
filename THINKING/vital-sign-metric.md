# REASONING LEDGER: the vital sign cannot yet falsify §15

## Problem
§15's one number — *metered tokens per certified claim, trending down* — is
implemented as `24h-burn / lifetime-certified` (station vitals). In that
form it cannot support §15's own kill condition. Solved = a metric + armed
prereg such that "the architecture is decoration" is a decidable verdict.

## Current best hypothesis
Per-ERA accounting: cumulative metered burn between certification events
(numerator resets at each certified claim). Rising unboundedly = sickness
visible; certifications ratchet it down. Confidence: medium. Sharpest doubt:
no persistent cumulative burn counter exists — quota windows are 5h/24h
snapshots, integration across samples double-counts overlapping windows.

## Evidence ledger
- [2026-07-04] baseline sample 04:00Z ratio 4,044,813 declared "a MAXIMUM"
  (ALIEN-ARCHITECTURE §15); next sample 05:32Z ratio 4,114,230 — rising, no
  alarm anywhere fired. Receipt: `station spine 5 vitals`.
- [2026-07-04] turn 16 made sampling autonomic (8/day via beat) — the raw
  series now exists regardless of which metric interprets it.

## Hypotheses killed (and by what)
- H: "arm a 7-day deadline prereg: some sample must fall below baseline."
  KILLED BY: metric shape — ratio = 24h-burn / lifetime-certified, so ONE
  quiet day (low burn) passes the test trivially with zero new capability.
  The prereg would certify sleep, not health. (2026-07-04, turn-sketch.)
- H: "compare consecutive samples as the trend." KILLED BY: activity
  confounding — build nights legitimately spike burn; punishing building is
  the wrong incentive, §15 explicitly expects numerator-heavy eras.

## Open probes (cheapest-decisive first)
- [ ] does the Claude quota store expose a lifetime/cumulative counter
      (station quota source)? If yes, era-accounting is one subtraction.
- [ ] else: derive cumulative burn from the 8/day samples via
      non-overlapping 24h windows (1 sample/day at fixed hour) — loses
      resolution, gains correctness.
- [ ] median-of-era vs median-of-prior-era on the existing ratio: does it
      survive the activity-confound objection for QUIET-era pairs at least?

## Constraints & invariants discovered
- Any metric must not punish build eras (§15 text) nor reward idleness
  (the quiet-day exploit above).
- FAIL must halt something visible (drift alarm) — a dashboard nobody reads
  is decoration measuring decoration.
- The raw vitals samples are honest regardless; only the INTERPRETATION is
  unsolved. Never let the metric debate stop the sampling.

## Session log
- 2026-07-04 (spiral turns 7-21 session): problem identified while designing
  a vitals-trend drift assertion; two hypotheses killed before build — the
  assertion was NOT built precisely because it would have been theater.
  Ledger opened instead (this file). Next instance: start at Open probes.
