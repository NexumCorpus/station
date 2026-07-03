"""TEMPLATE: build + gate an audit bundle (certify-claim skill's code half).
Bundle contract (atlas grader.cjs): claim.json {id, statement, check argv
with {seed}, claimed_seeds} + check.py exiting 0 iff the claim re-derives at
that seed. Doctrine: ordering assertions with margins ~4x under measured
gaps, never memorized values; statement quotes the DECLARED verdict
verbatim; trusted code imported from the domain, never reimplemented;
pin absolute venv python if the check needs deps."""
import json
import subprocess
from pathlib import Path

GATE = r"E:\atlas-station\scripts\claim-gate.mjs"

CHECK_SKELETON = '''\
"""Trusted-oracle check (grader contract). Usage: python check.py <seed>"""
import sys
REPO = r"{repo}"                      # the domain's own code — never reimplement

def main():
    seed = int(sys.argv[1])
    sys.path.insert(0, REPO)
    # from <domain> import <trusted oracle/generator/runner>
    # measured = <re-derive at seed>
    # FLOOR/ordering assertion with pre-declared margin:
    # return 0 if measured_ordering_holds else 1
    raise NotImplementedError

if __name__ == "__main__":
    sys.exit(main())
'''


def write_bundle(bundle: Path, claim_id: str, statement: str,
                 check_argv: list, claimed_seeds: list):
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "claim.json").write_text(json.dumps({
        "id": claim_id, "statement": statement,
        "check": check_argv, "claimed_seeds": claimed_seeds}, indent=1),
        encoding="utf-8")


def gate(bundle: Path, holdout_seeds: list) -> bool:
    """Driver-side only: holdouts must be chosen by someone who is NOT the
    claimant (crypto randomness for organs; fresh literals for analyses)."""
    proc = subprocess.run(["node", GATE, str(bundle)]
                          + [str(s) for s in holdout_seeds],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=1800)
    print(proc.stdout.strip())
    return proc.returncode == 0
