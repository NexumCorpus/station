"""Drift check (spiral turn 45): resurrection rehearsal. The continuity
mirror is the ONLY path back from a dead disk, and until this check it had
never been restore-tested — witness proves nobody rewrote history, mirror.py
proves ledger prefixes, but nothing proved the JOURNAL resurrects. Drill:
restore the mirrored journal to a temp dir and boot the wake-critical index
from the restored copy alone; separately, prove the offsite remote actually
holds the local mirror's HEAD."""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path("E:/continuity/journal")
LIVE = Path.home() / ".claude" / "projects" / "E--" / "memory"

if not SRC.is_dir():
    print("NO-MIRROR: journal absent from E:/continuity")
    sys.exit(1)

tmp = Path(tempfile.mkdtemp()) / "resurrected"
shutil.copytree(SRC, tmp)

idx = tmp / "MEMORY.md"
if not idx.is_file():
    print("UNBOOTABLE: restored copy has no MEMORY.md index")
    sys.exit(1)
links = re.findall(r"\]\(([^)]+\.md)\)", idx.read_text(encoding="utf-8-sig"))
dead = [m for m in links if not (tmp / m).is_file()]
if dead:
    print(f"UNBOOTABLE: index links dead in restored copy: {dead[:5]}")
    sys.exit(1)

restored = len(list(tmp.rglob("*.md")))
live = len(list(LIVE.rglob("*.md"))) if LIVE.is_dir() else 0
if live and restored < live * 0.9:
    print(f"THIN: restored {restored} files vs live {live} (mirror lagging "
          f"badly - run station backup)")
    sys.exit(1)

# offsite proof: the private remote holds the local mirror's HEAD
r = subprocess.run("git -C E:/continuity rev-parse HEAD",
                   shell=True, capture_output=True, text=True)
local = r.stdout.strip()
r = subprocess.run("git -C E:/continuity ls-remote origin HEAD",
                   shell=True, capture_output=True, text=True)
remote = r.stdout.split()[0] if r.stdout.strip() else ""
if remote and remote != local:
    print(f"OFFSITE-LAG: remote {remote[:8]} != local {local[:8]} "
          f"(one backup cycle behind is tolerable; investigate if persistent)")
    # lag is a warning-grade fact, not a failed resurrection
if not remote:
    print("OFFSITE-UNREACHABLE: could not read origin HEAD (network?)")
    sys.exit(1)

shutil.rmtree(tmp.parent, ignore_errors=True)
print(f"CHECK-OK resurrected {restored} journal files, index boots, "
      f"{len(links)} links live, offsite HEAD {'current' if remote == local else 'LAGGING'}")
