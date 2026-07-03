# HANDOFF — molt artifact, written 2026-07-03T18:52:49Z

## Estate heads
atlas ed62ea5*1mod+2unt | ege 343f5db | rde b4432ed+2unt | director2 4d49336+43unt | boundary c8bab14
claims 5certified 2rejected 0pending | last: demiurge-organ-auto-20260703_003118-1opt-2opt-adj-ils REJECTED

## Log freshness (cursor-read these, not the raw files)
log wave2 3574B age=3m unread=3574B -> station log wave2

## Spine tail (last 8 events)
{"t": "2026-07-03T10:31:06Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 0}}
{"t": "2026-07-03T10:31:10Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 0}}
{"t": "2026-07-03T10:32:24Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 0}}
{"t": "2026-07-03T10:32:28Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 0}}
{"t": "2026-07-03T10:33:03Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 0}}
{"t": "2026-07-03T10:33:03Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 1}}
{"t": "2026-07-03T10:33:08Z", "kind": "suites", "body": {"boundary": "PASS", "_cached": 0}}
{"t": "2026-07-03T18:43:57Z", "kind": "note", "body": "WAVE 2 PAUSED on quota (3rd limit in 24h): 5 real organisms scored (+2 pilots), 11 excluded, dead workspaces cleaned. RESUME NEXT WINDOW: cd E:\\boundary\\mission1; python -u sweep_w2.py T1,T2,T3,T4 1,2,3,4,5,6,7,8 (skip-existing safe; clean non-scored w2_* dirs first if any). Registered analysis ONLY at n>=8/tier. NO mid-wave peeking at observables-vs-tier."}

## Live edge / next actions
wave2 remainder in flight (task bdva6ib74, log: station log wave2); at n>=8/tier run analyze_w2.py = registered P4-P7 verdict; then wave-2 report + possible molt

## Wake protocol for the next instance
1. station wake   2. station log <any-unread>   3. Read this file   4. continue from Live edge
Background processes SURVIVE a thread clear; their session notifications do NOT — recover via the registered logs.