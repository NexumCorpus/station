# HANDOFF — molt artifact, written 2026-07-04T19:24:44Z

## Estate heads
atlas e968141 | ege d750128 | rde b4432ed+2unt(rescued) | director2 f5bd0cb | boundary c8bab14 | station db6ccb1 ^2unpushed | demiurge 8cf6ffe | continuity 57b5b46
claims 4certified 2rejected 0pending (1re-cert) | last: demiurge-organ-auto-20260703_003118-1opt-2opt-adj-ils REJECTED

## Log freshness (cursor-read these, not the raw files)
log pulse 51017B age=10m unread=13915B -> station log pulse
log digest 9429B age=65m unread=3209B -> station log digest

## Spine tail (last 8 events)
{"t": "2026-07-04T16:15:07Z", "kind": "witness", "by": "pulse-beat-2026-07-04T16:15:02Z", "body": {"alarms": 0}}
{"t": "2026-07-04T18:17:29Z", "kind": "fact", "by": "pulse-beat-2026-07-04T16:15:02Z", "body": {"claim": "wave-2 scored slots {\"T1\": 8, \"T2\": 8, \"T3\": 8, \"T4\": 4}", "cmd": "\"C:\\Users\\dalea\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe\" \"E:\\station\\pulse.py\" --counts", "expect": "{\"T1\": 8, \"T2\": 8, \"T3\": 8, \"T4\": 4}", "exit": 0, "ok": true, "out": "{\"T1\": 8, \"T2\": 8, \"T3\": 8, \"T4\": 4}"}}
{"t": "2026-07-04T18:19:56Z", "kind": "vitals", "by": "pulse-beat-2026-07-04T16:15:02Z", "body": {"h": 24.0, "burn": 31047343, "certified": 4, "ratio": 7761835, "free_calls": 9}}
{"t": "2026-07-04T18:20:01Z", "kind": "backup", "by": "pulse-beat-2026-07-04T16:15:02Z", "body": {"sources": 15}}
{"t": "2026-07-04T18:20:01Z", "kind": "note", "by": "pulse-beat-2026-07-04T16:15:02Z", "body": "PULSE wave-topup counts={'T1': 8, 'T2': 8, 'T3': 8, 'T4': 4}"}
{"t": "2026-07-04T19:15:11Z", "kind": "drift", "by": "pulse-beat-2026-07-04T19:15:03Z", "body": {"checked": true, "drifts": 0}}
{"t": "2026-07-04T19:15:11Z", "kind": "witness", "by": "pulse-beat-2026-07-04T19:15:03Z", "body": {"alarms": 0}}
{"t": "2026-07-04T19:16:39Z", "kind": "backup", "by": "pid54288", "body": {"sources": 15}}

## Standing facts (re-derived at molt-write — routes travel, quotes rot)
ok    [2026-07-04T07:16:07Z] hunt q2n14r2 latest outcome = hunt-noemit
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --hunt-last q2n14r2 ~ 'hunt-noemit'
ok    [2026-07-04T07:39:22Z] all 7 estate work repos are PUBLIC on NexumCorpus (continuity stays private)
      route: python E:/station/checks/public7.py ~ 'CHECK-OK all 7'
ok    [2026-07-04T18:17:29Z] wave-2 scored slots {"T1": 8, "T2": 8, "T3": 8, "T4": 4}
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --counts ~ '{"T1": 8, "T2": 8, "T3": 8, "T4": 4}'

## Live edge / next actions
spiral ^5 capstone: 2/5 landed (T51 organs c36b8ae, T52 kill-audit db6ccb1). NEXT: (1) sweep 23 unaudited organs T23,27,30,32-51 + no-kill census INLINE/station-llm - grep-shaped, NEVER fan-out (see errata over-provisioned-dispatch); (2) reconcile T3 open item - 0xC000013A already answered in grimoire; (3) fluid composition measure candidate; (4) preregs due 07-06/07-10/07-14. Journal: spiral-capstone-52.md

## Wake protocol for the next instance
1. station wake   2. station log <any-unread>   3. Read this file   4. continue from Live edge
Background processes SURVIVE a thread clear; their session notifications do NOT — recover via the registered logs.