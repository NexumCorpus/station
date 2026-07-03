# PLAY: oracle-audit — adversarial verification of a hand-written test oracle

*Provenance: produced the T3 (54/54 SOUND) and T4 (56/56 SOUND, three-variant
canonical-form proof) verdicts, and the Specimen 0 exoneration. Dispatch as a
fresh general-purpose agent. Fill {{SLOTS}}.*

Adversarial audit of a hand-written test oracle for a pre-registered
experiment. Spec: {{BRIEF_PATH}} ({{ONE_LINE_DOMAIN_SUMMARY}}). Hidden
probes: {{PROBES_GLOB}} — each has run(mod) returning (name, passed) checks
with hand-derived expected values.

THE RISK: a probe with a WRONG expected value (or one that over-constrains
to ONE arbitrary choice where the spec permits alternatives) will fail a
CORRECT subject and corrupt the experiment. Catch those.

Method:
1. Read the spec fully; extract exact semantics ({{DANGER_SEMANTICS}}).
2. Write your OWN faithful implementation from the spec ALONE (scratch file
   {{SCRATCH_PATH}}) — never derive from the probes (avoids inheriting their
   errors).
3. Run every probe against YOUR implementation; for each failure decide via
   hand-calculation whether the PROBE or YOUR impl is wrong.
4. For any family asserting exact outputs: verify the spec UNIQUELY forces
   them. If multiple valid outputs exist, prove non-over-constraint by
   running divergent-but-valid variant implementations through all probes.
5. Re-derive {{N_SPOT}} expected values independently; confirm.

Deliverable (self-contained final message): (a) does a faithful impl pass
ALL probes — list failures with hand calcs; (b) over-constraint verdict;
(c) spot-check table; (d) spec ambiguities that could unfairly fail a
correct subject; (e) verdict: SOUND or the fix list. Report absences as
plainly as findings. Delete scratch files. Do NOT modify any probe, spec,
or test. Do NOT git commit.
