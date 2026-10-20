<div align="center">
  <img src="./nexum-hero.svg" alt="Station: a continuity tool for AI-agent work across local repositories" width="100%" />

  <p><strong>A command-line tool that rebuilds working state from files and re-checks old claims, so the next session starts from evidence instead of notes.</strong></p>

  <p><a href="#quickstart">Quickstart</a> · <a href="#commands">Commands</a> · <a href="#what-station-does-not-claim">Limits</a> · <a href="./CAPSULE.md">Agent capsule</a> · <a href="https://github.com/NexumCorpus">Nexum Corpus</a></p>
</div>

---

## What it is

Station is a standard-library Python tool for people who run AI coding agents across several local git repositories. It does three things:

1. **Rebuilds state in one call.** `station wake` prints a short digest: each registered repository's HEAD and uncommitted files, claim and ledger summaries, running processes, and how many unread bytes each registered log has.
2. **Keeps append-only records.** Events and ledgers are JSON Lines files written under a file lock. A log is read through a cursor, so a second read returns only the bytes added since the first.
3. **Re-checks claims.** `station say` stores a claim together with a shell command that re-derives it. The command runs when the claim is written and again on `station recheck`, so a claim that stops being true is flagged as `stale`.

## Why it exists

Long-running agent work loses state. Logs get read twice, summaries drop exact values, and a note written last week keeps being believed after the thing it describes has changed. Station keeps state in files, hashes and cursors that a new session can verify, rather than in a summary of an earlier conversation.

## What Station does not claim

- **It is not a sandbox.** Registry and claim commands run with `shell=True`. The registry sits in the same trust domain as the code, so only run a registry you trust. `station.json` is the author's own registry and runs commands such as `npm`, `pytest` and `.venv\Scripts\python.exe` against `E:/` paths. If `station.local.json` does not exist, Station falls back to it, so run `examples/init_local.py` first (see Quickstart).
- **It is tested on Windows and Linux, not macOS.** CI runs the tests on `windows-latest` and `ubuntu-latest` with Python 3.10, 3.12 and 3.13. macOS has never been run.
- **Some verbs need things this repository does not provide** (see [Requirements by verb](#requirements-by-verb)).
- **This repository contains the author's real working data** (see [What is in this repository](#what-is-in-this-repository)), so some output on a fresh clone describes the author's work, not yours.
- **The founding audit cannot be checked from here** (see [Evidence](#evidence)).
- **There is no license file yet.** Until the owner adds one, no right to reuse the code is granted.

## Quickstart

Standard library only, Python 3.10 or newer. On Linux and macOS, type `python3` where the commands below say `python`.

```text
git clone https://github.com/NexumCorpus/station && cd station
python tests_station.py            # about 50 tests, under 10 s, written to a temporary directory
python examples/init_local.py      # writes station.local.json: a registry that points at THIS checkout
python station.py wake             # state digest for that registry
python station.py suites           # runs the registered suites, one PASS/FAIL line each
```

To type `station <verb>` instead of `python station.py <verb>`, put the checkout directory on `PATH`. `station.cmd` (Windows) and `station` (Linux and macOS) are small wrappers that run the `station.py` next to them.

`station.py` prefers `station.local.json` when it exists, and `STATION_REGISTRY=<path>` overrides both registries, so a first run never edits tracked files. The one thing a run does write into the checkout is the ledgers, which are created next to `station.py` (`spine.jsonl`, `cursors/` and `station.local.json` are gitignored; verbs that append to a tracked ledger such as `errata.jsonl` will show up in `git status`).

## Commands

`station help` lists every verb with usage; [CAPSULE.md](./CAPSULE.md) is the dense briefing written for agents. `checks/verbs.py` fails if a verb is missing from `help` and `checks/capsule.py` fails if one is missing from `CAPSULE.md`; CI runs both.

| command | what it does |
|---|---|
| `station wake` | One digest of registered repositories (HEAD and uncommitted files), claim and ledger summaries, process counts, token-use accounting, open notes in `THINKING/`, unread bytes per log, the pending `WILL.md`, and the tail of the event log. |
| `station suites [name]` | Runs the registered test commands and prints one PASS/FAIL line each. A PASS is cached by the git tree hash of the suite's directory; a FAIL is never cached. An unknown suite name is an error, never a PASS. |
| `station log <name>` | Cursor read: prints only bytes appended since the last read. A glob path resolves to the newest matching file, with one cursor per file. `--tail N` previews without moving the cursor; `--full` prints everything. |
| `station say / recheck / retire` | Claims with proof. `say "<claim>" --cmd "<command>" [--expect "<text>"]` runs the command first. It exits 0 and (if `--expect` is given) prints the text: recorded as `fact`. Otherwise it is recorded as `refuted` and the exit code is 1. `recheck` re-runs the stored commands and reports a changed result as `stale`. `retire` removes a fact from rechecks while keeping it in the record. |
| `station seal <ledger>` | Appends one JSON object (from stdin) to a ledger with the timestamp and author taken from Station's own clock. A `t` field supplied in the input is discarded. |
| `station market` | Tracks commercial hypotheses. `pack` renders a scope note carrying a hash. A hypothesis can be marked `PAID` only with a pointer to a local receipt file. |
| `station immune` | Pre-registered one-line "lesions" (deliberate small breakages) applied to a disposable copy of a registered suite. A result counts only while the damaged source still has the hash that was recorded. |
| `station forecast` | Append-only predictions with a probability, a frozen command that observes the outcome, a date before which they cannot be resolved, a Brier score on resolution, and a mandatory review. |
| `station horizon` | A single ranked list of open obligations (integrity checks, preregistrations, market items, forecasts). Each item shows its evidence, who may act on it, and the next command. It only reads; it never acts. |
| `station graft` | Copies the files named in a hash-pinned manifest into an empty temporary directory and runs a fixed check there. This detects hidden dependencies on surrounding files. It is not a security sandbox. Exits 1 if a manifest's source files are missing or changed. |
| `station burn / eras / vitals / quota` | Counts daily token use from the running user's Claude Code transcripts (`~/.claude/projects/**/*.jsonl`) and groups it into eras between recorded claim certifications. `quota` shows the last few hours. Without those transcripts the figures are empty. |
| `station drift` | Runs the assertions in `drift.jsonl` and exits 1 if any fails. An assertion passes only if its command exits 0 and (when given) prints the expected text. See [drift.jsonl](#what-is-in-this-repository). |
| `station witness` | Records a hash for every entry of the append-only ledgers named in the registry and raises an alarm (exit 1) if an earlier entry later changes. |
| `station backup` / `station rescue <repo>` | Copy ledgers and the author's journal into a separate continuity git repository (`backup`), or zip a repository's untracked files into it (`rescue`). Both need a continuity directory; see below. |
| `station note / spine / tally / map / cure / errata / pin` | `note` appends a free-text event. `spine` reads events with filters. `tally` prints per-group statistics of a JSONL file. `map` prints an outline of a Python file so you can read exact line ranges. `cure` searches `grimoire.jsonl`, a lookup of past errors and fixes. `errata` is a ledger of the tool's own mistakes. `pin` prints `[[pin:path@sha16]]`, a pointer to a file's exact content hash. |
| `station will / handoff / molt` | `will` writes a short file of intent for whoever continues if the session ends. `handoff` writes a handoff note and re-runs the standing claims. `molt` does handoff, will and backup in one call. |
| `station hermes ask <file> "<question>"` | Asks a question about a large file by splitting it and querying an external model. |
| `station llm / hand / wsl` | `llm` sends one prompt to a local model server. `hand` queues tasks for an agent running in a WSL distribution. `wsl` runs a script file inside WSL. |
| `station regs` | Prints the active registry. |

Appends to the shared ledgers go through one function that takes an exclusive file lock (`msvcrt` on Windows, `flock` on POSIX). See [Evidence](#evidence) for the test.

## Requirements by verb

| verb | needs |
|---|---|
| everything not listed below | Python 3.10+ and git |
| `hand`, `wsl` | Windows with WSL and a distribution named `Ubuntu`; `hand` also needs the author's forager set up inside it. On other systems both print a one-line message and exit 1. |
| `llm` | An [Ollama](https://ollama.com) server at `localhost:11434` (default model `qwen2.5-coder:7b`). Without it the command prints a message and exits 1. |
| `hermes` | An external model backend. The default is the authenticated Codex CLI, which is metered against that account, not free. Set `HERMES_BACKEND=ollama` to use a local model. |
| `backup`, `rescue` | A continuity directory: `STATION_CONTINUITY` (an absolute path), defaulting to the author's `E:/continuity`. `rescue` also requires that directory to be a git repository; both refuse to run otherwise. `backup` additionally copies the author's journal if `~/.claude/projects/E--/memory` exists. |
| `wake`, `vitals`, `quota`, `eras`, `burn` | Optionally, Claude Code transcripts under `~/.claude/projects`. Without them the `thread` and token figures are missing. |

## What is in this repository

Station is also the author's own working checkout, so it ships real state alongside the code:

- **Ledgers and notes:** `*.jsonl` (spine inputs, errata, preregistrations, forecasts, market hypotheses, token-burn history), `digests/`, `hand-results/`, `THINKING/`, `market/`, `forecasts/`, `HANDOFF.md`. They contain the author's local paths. Because `wake` reads them, a fresh clone reports the author's open items (for example overdue preregistrations or "rot" markers), not yours.
- **`station.json`:** the author's own registry (repositories, suites and logs under `E:/`), kept as a worked example of a real one.
- **`drift.jsonl` and `checks/`:** executable assertions about the author's estate. The ones about this repository itself (every verb is in `help`, `CAPSULE.md` covers every verb, the shard and glyph codecs round-trip) run from any clone. The rest check the author's other repositories and journal, and report `DRIFT` on any other machine; that is expected.
- **`shards.jsonl`:** erasure-coded copies (`station shard` / `station recover`) of the files listed in it.

## Evidence

What each claim above rests on, and what it does not.

| claim | how to check it |
|---|---|
| Ledger appends do not tear or lose lines under contention | `python tests_station.py StationTests.test_concurrent_spine_appends_never_tear` runs 5 processes writing 50 events each and requires all 250 to be intact. An earlier run with plain append-mode writes lost 1,553 of 4,000 lines; that was measured once, in the author's checkout, and the old code is no longer here to reproduce it. |
| A claim whose command crashes is never recorded as a fact, even when the crash output contains the expected text | `StationTests.test_say_refuses_a_crashing_route_that_contains_the_expect` and `test_drift_flags_a_crash_that_contains_the_expect`. From Python 3.13 a traceback from `python -c` repeats its own source line, which is how such output can contain the expected text. |
| `seal` ignores hand-typed timestamps | `StationTests.test_seal_stamps_clock_and_discards_typed_t`, and `errata.jsonl` (class `invented-timestamp`) records the incident: hand-typed times drifted by 48 minutes in the author's own ledgers. The 48-minute figure is that one observation, not a measurement you can reproduce. |
| A misspelled suite name is an error, not a PASS | `python station.py suites nosuchsuite` exits 1; `test_unknown_suite_name_exits_1_never_passes` guards it. |
| A timed-out command is killed with its children | `test_run_timeout_kills_the_command_tree` starts a command that would write a file after the deadline and checks the file never appears. |
| The tests pass on Windows and Linux, Python 3.10 to 3.13 | The CI matrix in `.github/workflows/ci.yml`. |
| The founding audit | At its founding (2026-07-03) Station was reviewed by seven agents with no prior context, which reported 38 findings, 3 of them blockers that were fixed and given regression tests (including the misspelled-suite false PASS, which happened once in live use). **The findings list is not committed here, so the numbers cannot be checked from this repository.** The regression tests can be. |

## Design principles

- **Files over memory.** State lives in the working directory in a fixed, line-oriented form, not in anyone's recollection of a conversation.
- **Cursors.** Old bytes are never read twice, and nothing is summarised away.
- **One event log.** `spine.jsonl` is a single append-only record across repositories and tools, so "what happened while I was away" is one read.
- **Fixed one-line output.** Output is one line per fact in a stable layout, built for machine parsing rather than for reading.
