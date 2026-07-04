# HANDOFF — molt artifact, written 2026-07-04T07:25:21Z

## Estate heads
atlas e968141 | ege 343f5db | rde b4432ed+2unt(rescued) | director2 4d49336+43unt(rescued) | boundary c8bab14 | station 7bd496b | demiurge 8cf6ffe | continuity 1d64271
claims 5certified 2rejected 0pending | last: demiurge-organ-auto-20260703_003118-1opt-2opt-adj-ils REJECTED

## Log freshness (cursor-read these, not the raw files)
log pulse 26594B age=2m unread=582B -> station log pulse

## Spine tail (last 8 events)
{"t": "2026-07-04T07:21:56Z", "kind": "wake", "by": "pid9040", "body": {"repos": 8}}
{"t": "2026-07-04T07:22:15Z", "kind": "backup", "by": "pid14528", "body": {"sources": 14}}
{"t": "2026-07-04T07:23:19Z", "kind": "fact", "by": "pid3168", "body": {"claim": "wave-2 scored slots {\"T1\": 8, \"T2\": 8, \"T3\": 3, \"T4\": 0}", "cmd": "\"C:\\Users\\dalea\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe\" \"E:\\station\\pulse.py\" --counts", "expect": "{\"T1\": 8, \"T2\": 8, \"T3\": 3, \"T4\": 0}", "exit": 0, "ok": true, "out": "{\"T1\": 8, \"T2\": 8, \"T3\": 3, \"T4\": 0}"}}
{"t": "2026-07-04T07:23:37Z", "kind": "backup", "by": "pid7072", "body": {"sources": 14}}
{"t": "2026-07-04T07:23:58Z", "kind": "stale", "by": "pid36756", "body": {"n": 3, "claims": ["wave-2 scored slots: T1=8 T2=6 T3=3 T4=0 (13 remain)", "wave-2 scored slots {\"T1\": 8, \"T2\": 6, \"T3\": 3, \"T4\": 0}", "wave-2 total scored slots = 17"]}}
{"t": "2026-07-04T07:24:36Z", "kind": "retired", "by": "pid44596", "body": {"claims": ["wave-2 scored slots: T1=8 T2=6 T3=3 T4=0 (13 remain)"], "match": "T1=8 T2=6"}}
{"t": "2026-07-04T07:24:36Z", "kind": "retired", "by": "pid48612", "body": {"claims": ["wave-2 total scored slots = 17"], "match": "total scored slots = 17"}}
{"t": "2026-07-04T07:24:55Z", "kind": "backup", "by": "pid48832", "body": {"sources": 14}}

## Standing facts (re-derived at molt-write — routes travel, quotes rot)
ok    [2026-07-04T07:16:07Z] hunt q2n14r2 latest outcome = hunt-noemit
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --hunt-last q2n14r2 ~ 'hunt-noemit'
STALE [2026-07-04T07:23:19Z] wave-2 scored slots {"T1": 8, "T2": 8, "T3": 3, "T4": 0}
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --counts ~ '{"T1": 8, "T2": 8, "T3": 3, "T4": 0}'
      now: ...{"T1": 8, "T2": 8, "T3": 4, "T4": 0} <- world moved since said; re-say before trusting

## Live edge / next actions
spiral turns 32-41 sealed (32 rescue / 33 locked-appends / 34 capsule / 35 hunt-speaker / 36 backup-lock / 37 pulse-tests / 38 spiral-turn-play / 39 dirt-grading / 40 same-beat-news / 41 supersession-walk). In flight: 07:15Z beat still sweeping T3/T4 (say_counts will speak autonomously when counts move). Open: coggate A/B trial of plays/spiral-turn.md when budget allows; era verdict after next certification; DANIEL DECISION pending: commit director2's 566 untracked research files properly (rescued to continuity/rescue meanwhile)

## Wake protocol for the next instance
1. station wake   2. station log <any-unread>   3. Read this file   4. continue from Live edge
Background processes SURVIVE a thread clear; their session notifications do NOT — recover via the registered logs.