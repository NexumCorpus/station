# station

Wake-and-verify spine for a multi-repo AI-agent estate. Built for agents that
**wake rather than remember**: one command reconstructs the entire working
state; every log read is cursor-tracked so no session ever pays twice for the
same bytes.

## Commands

| command | what |
|---|---|
| `station wake` | whole-estate digest: repo heads + dirt (with rescue grading), claims ledger, process counts, §15 era verdict, open THINKING ledgers, per-log **unread byte counts**, testament, spine tail |
| `station suites [name]` | all registered verification suites → one PASS/FAIL line each; verdict **cached by tree-hash** (FAIL never cached); typo'd names error rather than false-PASS |
| `station log <name>` | cursor read: only bytes appended since last read; glob paths resolve the newest file with per-file cursors; `--tail N` peeks, `--full` dumps |
| `station say / recheck / retire` | **provable speech**: a claim's re-derivation route runs at write (false claims land as `refuted`, never fact); facts are re-walked autonomically — newest-per-route, moment-facts retirable, world-moves alarm as `stale` |
| `station seal <ledger>` | clock-stamped attributed ledger append (stdin JSON; hand-typed timestamps are discarded — they drifted +48 min in practice) |
| `station market` | evidence-bound commercial hypotheses; `pack` renders a hash-carrying scope note and `PAID` is legal only with a local receipt pointer |
| `station immune` | pre-registered one-site lesions against a registered suite, applied only to a disposable copy; a result is current only while the wounded source hash still matches |
| `station burn / eras / vitals / quota` | persistent daily burn counter + **per-certification-era accounting**: the "metered tokens per certified claim, trending down" vital sign in decidable form |
| `station drift / witness / backup / rescue` | executable cross-reference assertions · append-only notary (alarms on history rewrite) · continuity mirror · offsite snapshots of *untracked* work |
| `station note / spine / tally / map / cure / errata / pin` | telegraph · filtered event reads · ledger stats · AST outlines · grimoire lookup · self-error ledger · content-hash pointers |
| `station will / handoff / molt` | testament (intent-at-death) · molt artifact with facts re-derived at the seam · the whole session seal in one call |
| `station llm / hand / wsl` | free local-model call · stigmergic tasking of a jailed WSL agent · bytes-not-quotes WSL script runner |
| `station regs` | show the registry |

All shared-ledger appends are lock-serialized (plain append-mode writes
measurably tore/lost data under multi-process contention). The full verb
list with usage lives in `station help`; the dense agent briefing in
`CAPSULE.md` (drift-checked against the code so neither can rot silently).

## Design principles

- **Stigmergy** — state lives in the world in machine-dense form, not in
  anyone's memory of a conversation.
- **Cursors** — lossless token efficiency: old bytes are never re-read, and
  nothing is summarized away.
- **Spine** — one append-only event ledger across every repo and tool;
  "what happened while I was gone" is a single read.
- **Dense wire** — fixed one-line-per-fact output schemas, built for LLM
  parsing rather than human prettiness.

## Setup

Stdlib-only, any Python 3.10+. Put the directory on PATH (`station.cmd`
wraps `python station.py`). Everything is driven by `station.json` —
repos, suites, logs — which sits in the same trust domain as the code
(the shell=True in the runner is deliberate and bounded to that file).

## Provenance

Hardened by a 7-agent cold-context audit at founding (38 findings; 3 blockers
fixed and regression-tested, including a typo'd-suite-name false-PASS that
had already fired once in live use).
