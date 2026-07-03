"""Drift check: every SPOOR pin ([[pin:PATH@SHA16]]) in registered-repo
markdown resolves and its hash matches. A broken pin = a load-bearing
pointer whose claim rotted (the 24601 index-copy failure class, made
structurally detectable)."""
import hashlib
import json
import re
import sys
from pathlib import Path

REG = json.loads(Path("E:/station/station.json").read_text(encoding="utf-8-sig"))
PIN = re.compile(r"\[\[pin:([^@\]]+)@([0-9a-f]{16})\]\]")

bad = []
scanned = 0
for repo in REG.get("repos", {}).values():
    for md in Path(repo).rglob("*.md"):
        if "node_modules" in md.parts or "runs" in md.parts:
            continue
        try:
            text = md.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        for path, sha in PIN.findall(text):
            scanned += 1
            target = Path(path)
            if not target.is_file():
                bad.append(f"{md.name}->{path}:GONE")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()[:16]
            if actual != sha:
                bad.append(f"{md.name}->{path}:STALE({actual})")

print("OK" if not bad else "BROKEN-PINS:" + str(bad[:5]),
      f"({scanned} pins scanned)")
sys.exit(0 if not bad else 1)
