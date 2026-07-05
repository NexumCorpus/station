"""Drift check (spiral turn 54): the dispatch-triage razor must not silently
erode. plays/dispatch-triage.md carries the one operative test that separates
inline work from fan-out, anchored to the 2.06M-token over-provisioned-dispatch
receipt (turn 52). A well-meaning rewrite could soften the razor back into the
generic 'when to fan out' heuristic that let the 2.06M mistake through in the
first place; this check pins the load-bearing markers so erosion trips drift
instead of passing quietly."""
import sys
from pathlib import Path

PLAY = Path("E:/station/plays/dispatch-triage.md")
# Load-bearing markers (ASCII-only, to survive the encoding joint): the
# operative test, the two-sided razor's judgment pole, the inline pole, and
# the paid receipt that anchors the whole thing.
MARKERS = ["decidable by", "irreducible judgment", "INLINE", "2.06M"]

if not PLAY.is_file():
    print("NO-TRIAGE-PLAY: plays/dispatch-triage.md is gone — the razor has no home")
    sys.exit(1)

text = PLAY.read_text(encoding="utf-8")
missing = [m for m in MARKERS if m not in text]
if missing:
    print(f"TRIAGE-ROT: dispatch-triage.md lost load-bearing markers {missing} "
          f"— the razor or its receipt was softened away")
    sys.exit(1)

print(f"CHECK-OK dispatch-triage razor intact "
      f"({len(MARKERS)} markers, 2.06M receipt anchored)")
