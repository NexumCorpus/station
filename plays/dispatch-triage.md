# PLAY: dispatch-triage — inline or fan out, decided by one test

*Provenance: spiral turn 54 (2026-07-05), anchored to turn 52's capstone — 46
Opus auditors + refuters were fanned to run 23 grep-decidable kill-condition
checks: ~2.06M tokens, ~1e3x the inline cost (errata: over-provisioned-dispatch).
The token doctrine's own audit was the single least efficient act of the whole
spiral. Pairs with the dense-dispatch skill (which briefs the agent once fan-out
is already the right call).*

## The one test (the razor)

**Is each unit of work decidable by <=3 grep / git / read / `station llm` calls?**

- **YES -> INLINE** (or `station llm` for free local reasoning). Run 40 greps
  inline; never spawn 40 agents to run one grep each.
- **NO -> FAN OUT** — it needs irreducible judgment, or only the CONCLUSION
  (not the dumps) can be allowed into your context.

That is the whole razor. Everything below is why each side is a trap when crossed.

## Fan out ONLY for (the honest positive cases — the razor cuts both ways)

- Independent audit / review where a VERDICT, not raw output, returns — the
  review->verify pipeline. Conclusions travel; dumps don't.
- >3-file exploration per unit where the READING is the cost and the finding is small.
- Genuinely irreducible judgment: design alternatives, adversarial refutation,
  a call no grep can settle.
- Parallel MUTATION across many files (worktree isolation) that would collide inline.

## Paid anti-patterns (each is a receipt, not a caution)

- **A grep-shaped check in an agent costume.** If one agent's entire task is a
  single grep / git / existence check, it is inline work wearing ~90k tokens.
  (Turn 52: 23 such checks -> ~2.06M.)
- **"Be comprehensive" read as "fan out."** Thoroughness is COVERAGE, not which
  tool runs each unit. A standing "always use a workflow" pressure — an ultracode
  session, a habit — is not a reason to dispatch a grep. Run the 40 checks INLINE.
- **Fanning out when you will re-read the raw output anyway.** If the agent's dump
  has to come back into your context to be useful, you needed a grep, not an agent.
- **The inverse trap — UNDER-provisioning.** Answering a real design fork or an
  adversarial verification with one inline grep because dispatch "feels expensive."
  Irreducible judgment earns the fan-out; starving it is the same error mirrored.

## Kill condition

If a later session still fans grep-shaped work despite this test, it failed to
bind — raise it to a hard pre-dispatch gate, or the play is not being consulted at
dispatch time. If it instead makes an instance answer irreducible judgment inline
(under-provisioning), the razor is mis-cut — restore the positive cases. The drift
assertion `checks/dispatch_triage.py` pins the razor + the 2.06M receipt against
silent erosion (a softened razor is the exact rot that let the 2.06M mistake through).
