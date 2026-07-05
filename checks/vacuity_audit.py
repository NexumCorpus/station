"""Meta-drift (spiral turn 59): AUDIT THE AUDITORS. The wave-2 catch was a
verdict-emitter that printed PASS on a null — analyze_w2.py's rising/falling:
`all(b >= a ...)` is True on an all-zeros series, so it certified a null as a
confirmation. That failure GENERALIZES: any PASS gated on a universal quantifier
(`all(`) or a negated existential (`not any(`) over a collection can fire
VACUOUSLY when the collection is empty / flat / degenerate, unless it is paired
with a guarantee the collection is non-degenerate (non-empty, effect cleared
zero/noise).

This scans the estate's verdict-emitters — the station drift auditors AND the
Boundary science analyzers — and surfaces every such site for REVIEW (a risk
pattern, not a proof of vacuity). Its own validity is RECURSIVE: it MUST flag
the known wave-2 bug (positive control) or the auditor of auditors is itself
vacuous and must not be trusted. Full proof of discrimination needs mutation
testing (corrupt the subject, confirm the check flips) — named as the heavier
follow-up; this closes the cheap, general, static layer."""
import re
import sys
from pathlib import Path

EMITTERS = [p for p in sorted(Path("E:/station/checks").glob("*.py"))
            if p.name != "vacuity_audit.py"] + [   # the auditor is not its own auditee
    Path("E:/boundary/mission1/analyze_w2.py"),
    Path("E:/boundary/mission1/analyze.py"),
]
RISK = re.compile(r"\ball\s*\(|\bnot\s+any\s*\(")
POS_CONTROL = Path("E:/boundary/mission1/analyze_w2.py")

flags = []
for f in EMITTERS:
    if not f.is_file():
        continue
    for i, ln in enumerate(f.read_text(encoding="utf-8", errors="replace")
                           .splitlines(), 1):
        if RISK.search(ln) and not ln.strip().startswith("#"):
            flags.append((f, i, ln.strip()[:72]))

pos = [x for x in flags if x[0] == POS_CONTROL]
for f, i, s in flags:
    tag = "POS-CTRL" if f == POS_CONTROL else "review "
    print(f"  [{tag}] {f.name}:{i}  {s}")

if not pos:
    print("VACUITY-AUDITOR-BROKEN: positive control (analyze_w2 monotonicity) "
          "NOT flagged — the auditor of auditors does not discriminate")
    sys.exit(1)

n_emitters = len({f for f, _, _ in flags})
print(f"CHECK-OK vacuity auditor valid: flagged its positive control "
      f"({len(pos)} hits in analyze_w2) + {len(flags)} universal-quantifier "
      f"PASS sites across {n_emitters} emitters — each must pair with a "
      f"non-empty/effect-cleared guard (REVIEW, not proof)")
