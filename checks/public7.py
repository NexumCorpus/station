"""Route target: the 7 estate work repos are PUBLIC on NexumCorpus —
verified UNAUTHENTICATED (an anonymous observer can fetch them; 404 =
private/absent). Continuity is deliberately absent: the journal stays
private. No gh dependency (gh keyring auth dies in python subprocess —
grimoire 2026-07-04)."""
import json
import sys
import urllib.request

WANT = ["station", "boundary", "Demiurge", "director2", "atlas-station",
        "emergent-geometry-engine", "recursive-discovery-engine"]
public = []
for name in WANT:
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/NexumCorpus/{name}",
            headers={"User-Agent": "station-drift-check"})
        with urllib.request.urlopen(req, timeout=30) as r:
            if not json.loads(r.read()).get("private", True):
                public.append(name)
    except OSError:
        pass
if len(public) == len(WANT):
    print(f"CHECK-OK all {len(public)} work repos public")
else:
    print(f"NOT-PUBLIC: {sorted(set(WANT) - set(public))}")
    sys.exit(1)
