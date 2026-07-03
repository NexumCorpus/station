# PLAY: cold-tool-audit — verify tooling/docs work for a zero-context user

*Provenance: the 7-agent station audit (38 findings, 3 blockers incl. a
false-PASS that had fired live). Dispatch several agents in parallel, one
per lens; collect structured findings. Fill {{SLOTS}}.*

Common preamble for every agent:
  You are a COLD agent: assume no prior context about this machine.
  Tool under test: {{TOOL_INVOCATION}}. Report findings with severity:
  blocker (breaks a cold user) / friction (works but confused you) / nit.
  In "worked": one sentence on what functioned.

Lenses (one agent each; add domain-specific ones):
- exercise: run every documented command exactly as written; flag any
  deviation between docs and behavior.
- semantics: test STATE machinery (caches, cursors, idempotency): do the
  second/repeated calls behave as specified? Prove with a mutation test,
  restore state after.
- cross-check: independently reproduce one of the tool's outputs by hand
  (run the underlying command yourself) and compare.
- doc-fact-check: read {{DOC_PATH}}; verify EVERY concrete claim against
  the filesystem/commands. Flag false statements and dead paths.
- critic-fragility: adversarial read of the source: what breaks in two
  weeks of real use (corruption windows, encoding traps, empty-collection
  vacuous successes, concurrent writers, path drift)? Concrete failure
  scenario for each finding.

Schema per agent: {findings: [{severity, what, evidence, suggestion}],
worked: string}. Adjudicate findings yourself afterward; fix blockers in
one sweep; regression-test each fixed path explicitly.
