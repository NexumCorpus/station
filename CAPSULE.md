# CAPSULE — station (dense agent briefing)

IDENTITY: wake-and-verify spine for the E:\ estate. Stdlib-only python, on
user PATH (`station`; this-session shells: python E:\station\station.py).
Registry station.json = same trust domain as code (repos/suites/logs).

COMMANDS:
  wake                     estate digest: repos+dirt, claims (atlas
                           CLAIMS.json), procs, log unread-bytes, spine tail
  suites [name] [--force]  all verification suites -> verdict lines; verdict
                           CACHE by tree-hash (identical tree = cached PASS,
                           FAIL never cached); typo'd name = exit 1
  log <name> [--tail N]    CURSOR read: only new bytes since last read
  tally <jsonl> [field]    dense per-group stats of any ledger
  map <file.py>            AST outline (defs/classes + lines) -> surgical Reads
  note <text> / spine [N]  append-only cross-instance telegraph

FILES: spine.jsonl (event ledger), cursors/ (offsets + suites.cache.json).
DESIGN: stigmergy (state in world), cursors (never pay twice for bytes),
  spine (one nervous system), dense wire (one line per fact).
INVARIANTS: suites empty-run or unknown-name must exit 1 (false-PASS was a
  live bug, fixed); registry read utf-8-sig; cursor writes atomic.
PROVENANCE: 7-agent cold audit at founding (38 findings, 3 blockers fixed).