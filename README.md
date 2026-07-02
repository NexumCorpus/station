# station

Wake-and-verify spine for a multi-repo AI-agent estate. Built for agents that
**wake rather than remember**: one command reconstructs the entire working
state; every log read is cursor-tracked so no session ever pays twice for the
same bytes.

## Commands

| command | what |
|---|---|
| `station wake` | whole-estate digest in ~9 lines: repo heads + dirt, claims ledger (certified/rejected/pending), process counts, per-log **unread byte counts**, spine tail |
| `station suites [name]` | run all registered verification suites → one PASS/FAIL line each (with cwd); exit 1 on any FAIL, typo'd names error rather than false-PASS |
| `station log <name>` | cursor read: returns only bytes appended since last read; `--tail N` peeks without moving the cursor; `--full` dumps |
| `station note <text>` | append a telegraph event to the spine (for the next session/instance) |
| `station spine [N]` | last N spine events (append-only cross-repo ledger, JSONL) |
| `station regs` | show the registry |

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
