# HANDOFF — molt artifact, written 2026-07-04T10:30:51Z

## Estate heads
atlas e968141 | ege d750128 | rde b4432ed+2unt(rescued) | director2 f5bd0cb | boundary c8bab14 | station 5014048*1mod | demiurge 8cf6ffe | continuity dfd4b5f
claims 4certified 2rejected 0pending (1re-cert) | last: demiurge-organ-auto-20260703_003118-1opt-2opt-adj-ils REJECTED

## Log freshness (cursor-read these, not the raw files)
log pulse 37102B age=10m unread=9935B -> station log pulse
log digest 6220B age=10m unread=5563B -> station log digest

## Spine tail (last 8 events)
{"t": "2026-07-04T10:15:19Z", "kind": "witness", "by": "pulse-beat-2026-07-04T10:15:02Z", "body": {"alarms": 0}}
{"t": "2026-07-04T10:15:19Z", "kind": "fact", "by": "pulse-beat-2026-07-04T10:15:02Z", "body": {"claim": "wave-2 scored slots {\"T1\": 8, \"T2\": 8, \"T3\": 8, \"T4\": 2}", "cmd": "\"C:\\Users\\dalea\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe\" \"E:\\station\\pulse.py\" --counts", "expect": "{\"T1\": 8, \"T2\": 8, \"T3\": 8, \"T4\": 2}", "exit": 0, "ok": true, "out": "{\"T1\": 8, \"T2\": 8, \"T3\": 8, \"T4\": 2}"}}
{"t": "2026-07-04T10:21:01Z", "kind": "vitals", "by": "pulse-beat-2026-07-04T10:15:02Z", "body": {"h": 24.0, "burn": 22188498, "certified": 4, "ratio": 5547124, "free_calls": 6}}
{"t": "2026-07-04T10:21:19Z", "kind": "backup", "by": "pulse-beat-2026-07-04T10:15:02Z", "body": {"sources": 15}}
{"t": "2026-07-04T10:21:19Z", "kind": "note", "by": "pulse-beat-2026-07-04T10:15:02Z", "body": "PULSE wave-topup counts={'T1': 8, 'T2': 8, 'T3': 8, 'T4': 2}"}
{"t": "2026-07-04T10:28:43Z", "kind": "drift", "by": "pid30700", "body": {"checked": true, "drifts": 0}}
{"t": "2026-07-04T10:29:03Z", "kind": "backup", "by": "pid15560", "body": {"sources": 15}}
{"t": "2026-07-04T10:30:07Z", "kind": "backup", "by": "pid4500", "body": {"sources": 15}}

## Standing facts (re-derived at molt-write — routes travel, quotes rot)
ok    [2026-07-04T07:16:07Z] hunt q2n14r2 latest outcome = hunt-noemit
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --hunt-last q2n14r2 ~ 'hunt-noemit'
ok    [2026-07-04T07:39:22Z] all 7 estate work repos are PUBLIC on NexumCorpus (continuity stays private)
      route: python E:/station/checks/public7.py ~ 'CHECK-OK all 7'
ok    [2026-07-04T10:15:19Z] wave-2 scored slots {"T1": 8, "T2": 8, "T3": 8, "T4": 2}
      route: "C:\Users\dalea\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe" "E:\station\pulse.py" --counts ~ '{"T1": 8, "T2": 8, "T3": 8, "T4": 2}'

## Live edge / next actions
Spiral ^9 complete (turns 42-50). ESTATE CLEAN, all 7 repos public+synced. OPEN: (1) preregs DUE dates - night-digest 07-06, hand-usefulness 07-10, hunt-yield review 07-14, will-recovery on next mid-move death (station preregs to score); (2) era-1 verdict after next certification unlocks the §15 median-of-era probe (THINKING/vital-sign-metric.md); (3) LICENSE decision is DANIEL'S - 7 public repos have none (legally closed by default); do NOT pick one unilaterally. Next spiral starts from: station wake + station preregs.

## Wake protocol for the next instance
1. station wake   2. station log <any-unread>   3. Read this file   4. continue from Live edge
Background processes SURVIVE a thread clear; their session notifications do NOT — recover via the registered logs.