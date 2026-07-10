# Temporal witness — an organism that can be wrong in public

## The future is the only blind grader that arrives for free

The estate can now test a nearby broken body, but it still narrates its own
expectations about the world after the fact. A forecast becomes evidence only
when it is committed while the event is still unavailable, has a mechanical
resolution route, and changes what the organism does in each possible future.

```
forecast (sealed before due) ── time passes ── mechanical observation
       │                                           │
       └─ p, YES action, NO action ────────────────┴─> Brier receipt + review
```

This is not the old ATLAS prediction note. That note is useful personal
bookkeeping, but it rewrites a prior record and lets a caller supply its own
outcome. The temporal witness is a separate, stricter organ: `forecast` and
`resolution` are append-only events; routes are small local file/JSONL
observations rather than shell commands; the station clock refuses an early
resolution. A future event can embarrass the forecaster without asking its
permission.

## Admission contract

A forecast names: a question; `p` in [0,1]; a due date strictly after today; a
local mechanical route; and two non-identical action branches (`if_yes`,
`if_no`). A branch is a decision commitment, not a generic apology. The route
is frozen at arm time. Resolution stores the source hash, observation, and
quadratic/Brier loss `(p-y)^2`; it does not rewrite the forecast. A resolved
forecast remains `UNREVIEWED` until an actor records which branch it actually
used or why it declined both.

## Scope

One score is not calibration. A low mean Brier score over a biased handful of
easy forecasts is also not calibration. This organ proves only that a specified
future question was bound before its due time and was later read through its
frozen local route. It does not judge causal quality, create demand, or turn a
probability into certainty.

The initial value is stranger and smaller: the organism gains a memory of its
*future selves' obligations*. It can no longer say "I expected that" without
leaving an earlier, timestamped body that either names the same expectation or
does not.
