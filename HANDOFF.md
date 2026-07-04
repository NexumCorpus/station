# HANDOFF — molt artifact, written 2026-07-04T06:59:40Z

## Estate heads
atlas e968141 | ege 343f5db | rde b4432ed+2unt | director2 4d49336+43unt | boundary c8bab14 | station ea4ed45*1mod | demiurge 8cf6ffe | continuity 3eb7947
claims 5certified 2rejected 0pending | last: demiurge-organ-auto-20260703_003118-1opt-2opt-adj-ils REJECTED

## Log freshness (cursor-read these, not the raw files)
log pulse 18529B age=7m unread=0B -> station log pulse

## Spine tail (last 8 events)
{"t": "2026-07-04T06:53:31Z", "kind": "backup", "by": "pid50568", "body": {"sources": 14}}
{"t": "2026-07-04T06:54:32Z", "kind": "retired", "by": "pid6852", "body": {"claims": ["station repo HEAD is c6ed974 (turn 9 seal)"], "match": "HEAD is c6ed974"}}
{"t": "2026-07-04T06:54:47Z", "kind": "backup", "by": "pid15084", "body": {"sources": 14}}
{"t": "2026-07-04T06:56:45Z", "kind": "wake", "by": "pid51184", "body": {"repos": 8}}
{"t": "2026-07-04T06:57:06Z", "kind": "backup", "by": "pid54868", "body": {"sources": 14}}
{"t": "2026-07-04T06:57:52Z", "kind": "drift", "by": "pid50080", "body": {"checked": true, "drifts": 0}}
{"t": "2026-07-04T06:58:09Z", "kind": "backup", "by": "pid5468", "body": {"sources": 14}}
{"t": "2026-07-04T06:59:39Z", "kind": "drift", "by": "pid52360", "body": {"checked": true, "drifts": 0}}

## Standing facts (re-derived at molt-write — routes travel, quotes rot)
ok    [2026-07-04T05:59:12Z] wave-2 scored slots: T1=8 T2=6 T3=3 T4=0 (13 remain)
      route: python -c "import sys; sys.path.insert(0,'E:/station'); import pulse; print(pulse.scored_counts())" ~ "{'T1': 8, 'T2': 6, 'T3': 3, 'T4': 0}"
ok    [2026-07-04T06:10:37Z] wave-2 scored slots {"T1": 8, "T2": 6, "T3": 3, "T4": 0}
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --counts ~ '{"T1": 8, "T2": 6, "T3": 3, "T4": 0}'
ok    [2026-07-04T06:19:18Z] wave-2 total scored slots = 17
      route: python -c "import sys; sys.path.insert(0,'E:/station'); import pulse; print(sum(pulse.scored_counts().values()))" ~ '17'

## Live edge / next actions
spiral turns 22-31 sealed (ledger E:/station/spiral.jsonl); next: (1) 07:15Z beat = first fully-autonomous say_counts utterance + first non-dry beat with burn/recheck steps - verify both landed, (2) after next certification: evaluate station eras verdict on a real era pair (THINKING/vital-sign-metric.md), (3) turn-11 hunt-exit speaker still open

## Wake protocol for the next instance
1. station wake   2. station log <any-unread>   3. Read this file   4. continue from Live edge
Background processes SURVIVE a thread clear; their session notifications do NOT — recover via the registered logs.