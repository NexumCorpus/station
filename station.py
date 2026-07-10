"""station — the wake-and-verify spine for the E:\\ estate.

Built 2026-07-03 for agents that wake rather than remember. Design principles
(alien on purpose; each one is a token-efficiency mechanism):

  STIGMERGY   State lives in the world, machine-dense. `station wake` rebuilds
              the whole picture in ONE call instead of ~10 exploratory calls.
  CURSORS     `station log <name> --since` returns only bytes appended since
              the last read (per-log offset files). Lossless: nothing is
              summarized away, old bytes are simply never re-bought.
  SPINE       One append-only JSONL ledger across every repo and tool
              (spine.jsonl). "What happened while I was gone" is one read.
  DENSE WIRE  Fixed one-line-per-fact schemas built for LLM parsing.

Stdlib only — runs on any system Python, no venv coupling.

Commands:
  station wake              dense estate digest (repos, claims, procs, spine)
  station suites [name]     run registered verification suites -> verdict lines
  station log <name> [--tail N | --full]   cursor-aware log read (default: new bytes only)
  station note <text...>    append a telegraph event to the spine (narrative)
  station say "<claim>" --cmd "<c>" [--expect "<f>"]   provable speech: the
                            claim's re-derivation route runs AT WRITE; a
                            failing claim lands as 'refuted', never as fact
  station recheck [N]       re-run the last N spine facts' routes (quote
                            nothing; re-derive)
  station retire "<match>"  retire moment-facts from the recheck walk (append
                            a 'retired' event; the fact stays in the record,
                            it just stops being re-derived - facts that
                            described a moment cannot go stale, only expire)
  station spine [N]         last N spine events (default 10)
  station will [intent|done]  testament: intent-at-death, rewritten at every
                            move boundary (interrupts are not graceful)
  station hand "<task>"|take|status   the hatch: feed the jailed always-on
                            hermes-agent (local model, $0); stigmergic —
                            drop food, walk away, collect later
  station llm [model] "<p>"|-  one free local-inference call
  station preregs [score <id> <verdict> <evidence...>]  armed kill conditions
                            with due dates (Law II's scheduler); wake surfaces
                            overdue arms; FAIL verdicts are the system working
  station market [arm|score|pack|verify|<id>]  evidence-bound income hypotheses:
                            local proof + external test + kill; PAID requires an
                            existing local receipt pointer
  station immune [arm|run|verify|report|<id>]  counterfactual immunity: wound a
                            disposable suite copy; retain only checks that feel it
  station forecast [arm|resolve|review|report|<id>]  temporal witness: seal a
                            future probability + local route + divergent actions
  station errata [add ...]  self-error ledger: the agent's own misread/failure
                            distribution (grimoire = world's lessons; errata =
                            mine). Reflex: caught in a correction -> add it
  station seal <ledger.jsonl>  clock-stamped ledger append: one JSON object
                            via stdin; 't' is ALWAYS the station's own clock
                            (hand-typed times drifted +48min into witnessed
                            ledgers - the invented-timestamp errata)
  station lease <name> [ttl_s] | <name> --release   stigmergic coordination:
                            exit 0 acquired, exit 1 held; expired leases are
                            taken over (a dead holder never wedges the estate)
  station tally <jsonl> [field]   dense per-group ledger stats
  station map <file>        AST outline; Read exact offsets, never whole files
  station cure "<fragment>" grimoire lookup FIRST on any error
  station drift             run executable cross-reference assertions (exit 1 = rot)
  station witness           notarize append-only ledgers; ALARM on rewrites
  station backup            mirror journal/spine/ledgers to E:/continuity
  station rescue <repo>     offsite-snapshot a repo's UNTRACKED files (paid
                            work git does not protect); non-destructive, the
                            repo is never touched - committing stays the
                            owner's call
  station pin <file>        mint [[pin:path@sha16]] for a load-bearing pointer
  station handoff [next...] write the molt artifact (re-derives standing facts)
  station molt [next...]    the whole molt seal in one call: handoff +
                            will-done + backup (journal narrative stays yours)
  station vitals [hours]    metered-burn / certified-claim ratio + spine sample
  station quota [hours]     metered-quota window burn
  station burn              roll completed UTC days' burn into burn-ledger.jsonl
                            (the cumulative counter transcripts can't be) +
                            cert markers; idempotent, pulse-driven
  station eras              per-certification-era cumulative burn (SS15 decidable
                            form: rising unbounded = sick, cert ratchets = alive)
  station conversions       performance->possession stock (SS17 vital sign):
                            HARD certs + STRUCTURAL drift/witness + SPEECH say;
                            decidable continuously where SS15's ratio blocks
  station moat              compounding-lead health (SS19): PORTABILITY
                            (structure>model) + FULCRUM (direction certs vs
                            execution) + DESCENT (the 'yours only while a verb' rate)
  station wall [ledger]     map the recombination wall (novelty-distance x
                            holdout-margin): THROUGH/PRETENDER/RECOMBINATION;
                            no args = the RDE cache-eviction map. find->map->through
  station discover          the wall-crossing engine: fill (QD) -> trojan (hidden-
                            holdout select) -> certify (untouched meta-holdout,
                            cleared-noise). Reports a CERTIFIED crossing or none
  station shard <file> [k n]  erasure-code a crystal: n fragments, ANY k
                            reconstitute it byte-exact (a PIN detects loss, a
                            SHARD repairs it); refuses k>=n. -> shards.jsonl
  station recover <pin>     reconstitute a crystal from surviving fragments
                            (RECOVERED / BELOW-K / MISDECODE-refused)
  station glyph <encode|expand|measure> [file|-]   the SPOOR GLYPH codec: swap
                            frequency-earned §-glyphs for load-bearing phrases
                            (lossless round-trip); measure reports compression
  station organs [--all|--kill|--open]  the spiral ledger as a living organ
                            registry: artifact refs existence-checked (exit 1 =
                            rot), kill conditions + open items surfaced
  station wsl [user] <src>|-  run a script in WSL, bytes-not-quotes joint
  station regs              show the registry (repos, suites, logs)
"""
from __future__ import annotations

import hashlib
import forecast
import immunity
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Windows: piped stdout defaults to cp1252 and dies on unicode in logs.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
# stdin: PS5.1 pipelines prepend a UTF-8 BOM; utf-8-sig eats it silently
# (same disease as the registry-BOM cure, applied at the pipe joint).
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8-sig")

HERE = Path(__file__).resolve().parent
REG = HERE / "station.json"
SPINE = HERE / "spine.jsonl"
CURSORS = HERE / "cursors"
WILL = HERE / "WILL.md"
ERRATA = HERE / "errata.jsonl"
SPIRAL = HERE / "spiral.jsonl"
MARKET = HERE / "market.jsonl"
MARKET_PACKS = HERE / "market"
IMMUNITY = HERE / "immunity.jsonl"
IMMUNE_PACKS = HERE / "immune"
FORECASTS = HERE / "forecasts.jsonl"
FORECAST_PACKS = HERE / "forecasts"
SUITE_TIMEOUT_S = 900


def _registry() -> dict:
    # utf-8-sig: PS5.1/Notepad love to re-save with a BOM; don't die on it.
    try:
        return json.loads(REG.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"station.json unreadable at {REG}: {e}")
        sys.exit(1)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_line(path: Path, line: str):
    """THE append primitive for shared ledgers. Plain 'a'-mode writes are
    NOT atomic across processes on Windows (turn-33 stress: 20 procs x 200
    appends -> 177 torn + 1553 LOST of 4000). An msvcrt region-lock on
    byte 0 serializes writers; readers never touch the lock."""
    path.parent.mkdir(exist_ok=True)
    if os.name != "nt":
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
        return
    import msvcrt
    with path.open("a", encoding="utf-8") as f:
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        try:
            f.write(line)
            f.flush()
        finally:
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


def _spine_append(kind: str, body):
    # Attribution (spiral turn 12): every event names its author. Autonomic
    # actors self-name via STATION_ACTOR (children inherit it); an unnamed
    # writer degrades to its pid — enough to join against the pulse-ledger.
    # Born from the "01:38Z hunt runner identity" breadcrumb that stayed
    # open across two molts because events were anonymous.
    by = os.environ.get("STATION_ACTOR", f"pid{os.getpid()}")
    _append_line(SPINE, json.dumps({"t": _now(), "kind": kind, "by": by,
                                    "body": body}) + "\n")


def _read_cursor(cur: Path) -> int:
    # A killed process / concurrent reader can leave a zero-byte offset file;
    # a corrupt cursor means "re-read from 0", never a crash.
    try:
        return int(cur.read_text())
    except (OSError, ValueError):
        return 0


def _write_cursor(cur: Path, value: int):
    tmp = cur.with_suffix(".tmp")
    tmp.write_text(str(value))
    os.replace(tmp, cur)                        # atomic on Windows + POSIX


def _run(cmd: str, cwd: str, timeout: int = 60):
    # shell=True is deliberate and bounded: every command string comes from
    # station.json, which sits in the SAME trust domain as this file (local,
    # version-controlled, agent-authored). No user/network input ever reaches
    # this function. The shell is what resolves npm.cmd-style shims on Windows.
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "(timeout)"
    except Exception as e:                      # registry-driven: never crash the digest
        return -2, f"({e})"


# ---------------------------------------------------------------- wake ------
def _repo_line(name: str, path: str) -> str:
    if not Path(path).is_dir():
        return f"{name} MISSING({path})"
    code, head = _run("git log --oneline -1", path)
    if code != 0:
        return f"{name} NOGIT"
    head = head.strip().split()[0] if head.strip() else "?"
    _, status = _run("git status --porcelain", path)
    lines = [ln for ln in status.splitlines() if ln.strip()]
    dirty = sum(1 for ln in lines if not ln.startswith("??"))
    untracked = sum(1 for ln in lines if ln.startswith("??"))
    mark = "" if dirty == 0 else f"*{dirty}mod"
    unt = "" if untracked == 0 else f"+{untracked}unt"
    # public-face proprioception (turn 47): after the 2026-07-04 publish,
    # local commits that never reach origin let the public repo silently
    # lag the working truth. Only meaningful when a remote exists; local
    # git ops (no network) so a dead remote never stalls a wake.
    sync = ""
    _, ahead = _run("git rev-list --count @{upstream}..HEAD", path)
    if ahead.strip().isdigit() and int(ahead.strip()) > 0:
        sync = f" ^{ahead.strip()}unpushed"
    if untracked:
        # honest alarm grading (turn 39): untracked-with-offsite-snapshot is
        # protected dirt, not at-risk dirt. Freshness matters: a snapshot
        # older than the newest untracked byte is stale protection.
        zips = sorted(Path("E:/continuity/rescue").glob(f"{name}-*.zip"))
        if zips:
            znew = zips[-1].stat().st_mtime
            newest = 0.0
            for ln in lines:
                if ln.startswith("??"):
                    try:
                        newest = max(newest, (Path(path) / ln[3:].strip()
                                              .strip('"')).stat().st_mtime)
                    except OSError:
                        pass
            unt += ("(rescued)" if znew >= newest
                    else f"(rescue-STALE {zips[-1].name[-14:-4]})")
    return f"{name} {head}{mark}{unt}{sync}"


def _claims_line(claims_path: str) -> str:
    p = Path(claims_path)
    if not p.is_file():
        return "claims none"
    try:
        claims = json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return "claims UNPARSEABLE"

    def state(c):
        if c.get("verified"):
            return "CERTIFIED"
        return "REJECTED" if "rejection" in c else "PENDING"

    # count DISTINCT capabilities per state (turn 46): a claim re-certified
    # with fresh holdout seeds is one capability, not two. dup= surfaces the
    # gap so the re-certification is visible, not hidden.
    cert = len({c.get("id") for c in claims if state(c) == "CERTIFIED"})
    rej = len({c.get("id") for c in claims if state(c) == "REJECTED"})
    pend = len({c.get("id") for c in claims if state(c) == "PENDING"})
    dup = len(claims) - len({c.get("id") for c in claims})
    tag = f" ({dup}re-cert)" if dup else ""
    last = claims[-1] if claims else {}
    return (f"claims {cert}certified {rej}rejected {pend}pending{tag} | last: "
            f"{last.get('id', '?')} {state(last) if claims else '-'}")


def _proc_counts() -> str:
    _, out = _run("tasklist /FO CSV /NH", str(HERE), timeout=30)
    counts = {}
    for ln in out.splitlines():
        name = ln.split('","')[0].strip('"').lower() if '","' in ln else ""
        for probe in ("python", "node", "claude", "grok"):
            if name.startswith(probe):
                counts[probe] = counts.get(probe, 0) + 1
    return "proc " + " ".join(f"{k}:{v}" for k, v in sorted(counts.items())) \
        if counts else "proc none-of-interest"


def _resolve_log(name: str, path: str):
    """Resolve a registered log to (file, cursor_file). Glob paths (e.g.
    digests/*.md) resolve to the newest match by name, with a PER-FILE
    cursor (name@file.offset) — a new day's file starts unread instead of
    inheriting the old file's offset into wrong bytes."""
    if "*" in path:
        matches = sorted(Path(path).parent.glob(Path(path).name))
        if not matches:
            return None, None
        p = matches[-1]
        return p, CURSORS / f"{name}@{p.name}.offset"
    return Path(path), CURSORS / f"{name}.offset"


def _log_freshness(reg: dict) -> list[str]:
    out = []
    for name, path in reg.get("logs", {}).items():
        p, cur = _resolve_log(name, path)
        if p is None or not p.is_file():
            continue
        age_min = (time.time() - p.stat().st_mtime) / 60
        seen = _read_cursor(cur)
        unread = p.stat().st_size - seen
        if unread > 0 or age_min < 120:
            out.append(f"log {name} {p.stat().st_size}B "
                       f"age={age_min:.0f}m unread={max(unread, 0)}B"
                       f" -> station log {name}")
    return out


def _thread_weight():
    """Context proprioception (SS10.1: attention hygiene IS cognition — a
    clean window is a smarter mind, so the organism must FEEL its window).
    The newest session transcript's last usage record carries the live
    context size: input + cache_read + cache_creation of the most recent
    turn. Returns (tokens, transcript_age_min) or (None, None)."""
    root = Path.home() / ".claude" / "projects"
    newest, mt = None, 0.0
    try:
        for f in root.rglob("*.jsonl"):
            m = f.stat().st_mtime
            if m > mt:
                newest, mt = f, m
    except OSError:
        return None, None
    if not newest:
        return None, None
    try:
        with newest.open("rb") as fh:
            fh.seek(max(0, newest.stat().st_size - 262144))
            tail = fh.read().decode("utf-8", errors="replace")
        for ln in reversed(tail.splitlines()):
            if '"usage"' not in ln:
                continue
            try:
                u = (json.loads(ln).get("message") or {}).get("usage") or {}
            except json.JSONDecodeError:
                continue
            ctx = (u.get("input_tokens", 0)
                   + u.get("cache_read_input_tokens", 0)
                   + u.get("cache_creation_input_tokens", 0))
            if ctx:
                return ctx, (time.time() - mt) / 60
    except OSError:
        pass
    return None, None


def cmd_wake():
    reg = _registry()
    # Instar = molt count + 1: the organism knows which shell it is wearing.
    instar = 1
    if SPINE.is_file():
        instar += sum(1 for ln in SPINE.read_text(encoding="utf-8")
                      .splitlines() if '"kind": "handoff"' in ln)
    lines = [f"STATION WAKE {_now()} | instar {instar}"]
    lines.append(" | ".join(_repo_line(n, p)
                            for n, p in reg.get("repos", {}).items()))
    if "claims" in reg:
        lines.append(_claims_line(reg["claims"]))
    lines.append(_proc_counts())
    if ERRATA.is_file():
        try:
            byc = {}
            for ln in ERRATA.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    e = json.loads(ln)
                    byc[e["cls"]] = byc.get(e["cls"], 0) + 1
            top = max(byc.items(), key=lambda kv: kv[1])
            lines.append(f"errata {sum(byc.values())} | top: {top[0]} "
                         f"x{top[1]} -> station errata")
        except (json.JSONDecodeError, KeyError):
            pass                          # errata must never break a wake
    # SS15 vital sign at the cheapest layer: pure ledger fold, no scans.
    # Open-era burn here excludes today (live partial needs a transcript
    # scan — that stays in station eras, not in every wake).
    if BURN_LEDGER.is_file():
        try:
            eras, cur = _fold_eras()
            worst = max((e["burn"] for e in eras), default=0)
            state = ("OK" if cur["burn"] <= worst
                     else "RISING-PAST-WORST") if eras else "-"
            lines.append(f"eras {len(eras)}closed | open days={cur['days']} "
                         f"burn~{cur['burn']:,}(excl-today) vs "
                         f"worst~{worst:,} {state} -> station eras")
        except (json.JSONDecodeError, KeyError):
            pass                          # vitals must never break a wake
    # context proprioception: the live thread's window weight. >60% of a
    # 200k window = molt territory (SS10.1 — reasoning degrades through a
    # stale mega-prefix long before the hard limit truncates it)
    # Window size varies by model and is not observable from transcripts —
    # report raw weight; the 150k advice threshold is a labeled heuristic
    # (this session's own first reading was 308k and reasoning still held,
    # so the flag is advice, not alarm).
    ctx, age = _thread_weight()
    if ctx:
        flag = "" if ctx < 150_000 else " heavy - consider station molt"
        lines.append(f"thread ~{ctx // 1000}k ctx (sampled {age:.0f}m ago)"
                     f"{flag}")
    # open reasoning ledgers (external working memory): a THINKING file
    # nobody reads is shelf-paper — the wake IS the discovery surface
    think = sorted(p.stem for p in (HERE / "THINKING").glob("*.md"))
    if think:
        lines.append(f"thinking {len(think)} open: {', '.join(think)}"
                     " -> E:/station/THINKING/")
    # armed kill conditions past due: Law II relies on these being SCORED,
    # and scoring relied on memory until turn 43
    try:
        today = _now()[:10]
        due = [r["id"] for r in _fold_preregs().values()
               if r["status"] == "armed" and r.get("due", "9999") < today]
        if due:
            lines.append(f"preregs DUE: {', '.join(due)} -> station preregs")
    except (json.JSONDecodeError, KeyError):
        pass
    try:
        market = _fold_market()
        if market:
            states = {}
            for row in market.values():
                states[row.get("status", "armed")] = states.get(row.get("status", "armed"), 0) + 1
            due = [row["id"] for row in market.values()
                   if row.get("status") == "armed" and row.get("due", "9999") < _now()[:10]]
            summary = " ".join(f"{state}={count}" for state, count in sorted(states.items()))
            lines.append(f"market {len(market)} theses | {summary}"
                         + (f" | DUE: {', '.join(due)}" if due else "")
                         + " -> station market")
    except (json.JSONDecodeError, KeyError):
        pass
    try:
        immune = _fold_immunity()
        if immune:
            states = {}
            for row in immune.values():
                status = (row.get("outcome") or {}).get("status", "armed")
                states[status] = states.get(status, 0) + 1
            summary = " ".join(f"{state}={count}"
                               for state, count in sorted(states.items()))
            lines.append(f"immune {len(immune)} lesions | {summary} -> station immune")
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    try:
        forecasts = _fold_forecasts()
        if forecasts:
            states = {}
            overdue = []
            today = _now()[:10]
            for ident, row in forecasts.items():
                state = forecast.status(row)
                states[state] = states.get(state, 0) + 1
                if state == "ARMED" and row["forecast"]["due"] < today:
                    overdue.append(ident)
            summary = " ".join(f"{state}={count}"
                               for state, count in sorted(states.items()))
            lines.append(f"forecast {len(forecasts)} futures | {summary}"
                         + (f" | DUE: {', '.join(overdue)}" if overdue else "")
                         + " -> station forecast")
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    lines += _log_freshness(reg)
    if SPINE.is_file():
        events = SPINE.read_text(encoding="utf-8").splitlines()
        lines.append(f"spine {len(events)}ev | last: "
                     + (events[-1] if events else "-"))
    else:
        lines.append("spine empty")
    if WILL.is_file():
        age_m = int((time.time() - WILL.stat().st_mtime) / 60)
        intent = next((ln for ln in WILL.read_text(encoding="utf-8")
                       .splitlines() if ln.strip()
                       and not ln.startswith("#")), "")[:140]
        lines.append(f"WILL age={age_m}m (author died mid-move — verify vs "
                     f"dirt+spine) | {intent}")
    try:
        # touching \\wsl$ boots WSL if it is down -> systemd revives the
        # forager: every wake also wakes the hand (circadian by design)
        h = {"in": len(list((HATCH / "in").glob("*.task"))),
             "claimed": len(list((HATCH / "claimed").glob("*.task"))),
             "out": len(list((HATCH / "out").glob("*.result")))}
        if any(h.values()):
            lines.append(f"hatch in={h['in']} working={h['claimed']} "
                         f"results={h['out']}"
                         + (" -> station hand take" if h["out"] else ""))
    except OSError:
        pass
    print("\n".join(lines))
    _spine_append("wake", {"repos": len(reg.get("repos", {}))})


# -------------------------------------------------------------- suites ------
def _tree_key(cwd: str) -> str:
    """Hash of HEAD + working-tree status: identical key => identical tree."""
    _, head = _run("git rev-parse HEAD", cwd, timeout=30)
    _, porc = _run("git status --porcelain", cwd, timeout=30)
    _, diff = _run("git diff --stat", cwd, timeout=30)
    return hashlib.sha256((head + porc + diff).encode()).hexdigest()[:16]


def cmd_suites(only: str | None = None, force: bool = False):
    """Verdict cache (lossless by tree-hash): a suite whose repo tree is
    byte-identical to its last PASS returns the cached verdict instead of
    re-running. FAILs are never cached. --force re-runs everything."""
    reg = _registry()
    suites = reg.get("suites", [])
    if only:
        suites = [s for s in suites if s["name"] == only]
        if not suites:                          # a typo must NEVER read as PASS
            known = ", ".join(s["name"] for s in reg.get("suites", []))
            print(f"unknown suite {only}; known: {known}")
            sys.exit(1)
    CURSORS.mkdir(exist_ok=True)
    cache_p = CURSORS / "suites.cache.json"
    try:
        cache = json.loads(cache_p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cache = {}
    results, cached_n = {}, 0
    for s in suites:
        key = _tree_key(s["cwd"])
        hit = cache.get(s["name"])
        if not force and hit and hit.get("key") == key \
                and hit.get("verdict") == "PASS":
            results[s["name"]] = "PASS"
            cached_n += 1
            print(f"suite {s['name']:12s} PASS (cached @{key[:8]}) "
                  f"[{s['cwd']}] | {hit.get('tail', '')}")
            continue
        t0 = time.time()
        code, out = _run(s["cmd"], s["cwd"], timeout=SUITE_TIMEOUT_S)
        tail = out.strip().splitlines()[-1][:120] if out.strip() else ""
        verdict = "PASS" if code == 0 else "FAIL"
        results[s["name"]] = verdict
        if verdict == "PASS":
            cache[s["name"]] = {"key": key, "verdict": "PASS", "tail": tail,
                                "t": _now()}
        else:
            cache.pop(s["name"], None)
        print(f"suite {s['name']:12s} {verdict} {time.time()-t0:5.1f}s "
              f"[{s['cwd']}] | {tail}")
    tmp = cache_p.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    os.replace(tmp, cache_p)
    _spine_append("suites", {**results, "_cached": cached_n})
    sys.exit(0 if results and all(v == "PASS" for k, v in results.items()
                                  if not k.startswith("_")) else 1)


# --------------------------------------------------------------- tally ------
def cmd_tally(path: str, by: str | None = None):
    """Dense aggregation of any JSONL ledger: one line per group — count +
    mean of every numeric field. Replaces ad-hoc parsing one-liners."""
    p = Path(path)
    if not p.is_file():
        print(f"(missing: {path})")
        sys.exit(1)
    rows = [json.loads(ln) for ln in p.read_text(encoding="utf-8-sig")
            .splitlines() if ln.strip()]
    groups: dict = {}
    for r in rows:
        groups.setdefault(str(r.get(by, "*")) if by else "*", []).append(r)
    for g in sorted(groups):
        rs = groups[g]
        nums: dict = {}
        for r in rs:
            for k, v in r.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    nums.setdefault(k, []).append(v)
        stats = " ".join(f"{k}={sum(v)/len(v):.3g}" for k, v in sorted(nums.items()))
        flags = {}
        for r in rs:
            for k, v in r.items():
                if isinstance(v, str) and k not in (by,):
                    flags[k] = flags.get(k, 0) + 1
        flag_s = " ".join(f"{k}:{c}" for k, c in sorted(flags.items()))
        print(f"{g:12s} n={len(rs):3d} {stats}"
              + (f" | {flag_s}" if flag_s else ""))


# ----------------------------------------------------------------- pin ------
def cmd_pin(path: str):
    """Mint a SPOOR pin: [[pin:PATH@SHA16]] — a pointer that asserts THIS
    exact version is load-bearing. Drift verifies every pin in registered
    repos (checks/pins.py); a mismatch = the pointer's claim broke."""
    p = Path(path)
    if not p.is_file():
        print(f"(missing: {path})")
        sys.exit(1)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    print(f"[[pin:{p.as_posix()}@{sha}]]")


# --------------------------------------------------------------- drift ------
def cmd_drift():
    """Crystallized vigilance: drift.jsonl holds executable ASSERTIONS —
    cross-reference facts that rot silently (index vs files, prereg vs
    fielded code, containment laws, seals). Every load-bearing fact written
    into a doc should gain an assertion here in the same session. Exit 1 on
    any drift."""
    reg_p = HERE / "drift.jsonl"
    if not reg_p.is_file():
        print("(no drift registry)")
        sys.exit(1)
    bad = 0
    for ln in reg_p.read_text(encoding="utf-8-sig").splitlines():
        if not ln.strip():
            continue
        a = json.loads(ln)
        code, out = _run(a["cmd"], str(HERE), timeout=120)
        ok = (a["expect"] in out) if "expect" in a else (code == 0)
        tail = out.strip().splitlines()[-1][:100] if out.strip() else f"code={code}"
        print(f"{'ok   ' if ok else 'DRIFT'} {a['claim'][:70]} | {tail}")
        bad += 0 if ok else 1
    _spine_append("drift", {"checked": True, "drifts": bad})
    sys.exit(1 if bad else 0)


# ------------------------------------------------------------- witness ------
def _entry_shas(path: Path) -> list[str]:
    """Per-entry hashes of an append-only store (jsonl lines, or a JSON
    array rewritten wholesale by its tool)."""
    text = path.read_text(encoding="utf-8-sig")
    if text.lstrip().startswith("["):
        entries = [json.dumps(e, sort_keys=True) for e in json.loads(text)]
    else:
        entries = [ln for ln in text.splitlines() if ln.strip()]
    return [hashlib.sha256(e.encode()).hexdigest()[:16] for e in entries]


def cmd_witness():
    """Incorruptibility: notarize append-only ledgers. History may GROW,
    never change — any edit/deletion of a previously witnessed entry is a
    HISTORY-REWRITE alarm. Registry: witness list in station.json; state in
    cursors/witness.json."""
    reg = _registry()
    CURSORS.mkdir(exist_ok=True)
    state_p = CURSORS / "witness.json"
    try:
        state = json.loads(state_p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    alarms = 0
    for path in reg.get("witness", []):
        p = Path(path)
        if not p.is_file():
            print(f"gone  {path} (witnessed file missing"
                  f"{' — ALARM' if path in state else ''})")
            alarms += 1 if path in state else 0
            continue
        shas = _entry_shas(p)
        old = state.get(path, [])
        if shas[:len(old)] != old:
            print(f"ALARM {path}: HISTORY REWRITTEN "
                  f"(prefix mismatch at entry "
                  f"{next((i for i,(a,b) in enumerate(zip(old,shas)) if a!=b), len(shas))}"
                  f" of {len(old)} witnessed)")
            alarms += 1
            continue                      # do NOT bless the rewrite
        grown = len(shas) - len(old)
        state[path] = shas
        print(f"ok    {path} entries={len(shas)} (+{grown})")
    tmp = state_p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1), encoding="utf-8")
    os.replace(tmp, state_p)
    _spine_append("witness", {"alarms": alarms})
    sys.exit(1 if alarms else 0)


# -------------------------------------------------------------- backup ------
def cmd_backup():
    """Survivability: the journal (the only continuity substrate), spine,
    grimoire, drift registry, and claims ledger currently risk single-copy
    loss. Mirror them into E:\\continuity (git -> private remote if
    configured) in one command."""
    import shutil as sh
    dest = Path("E:/continuity")
    jobs = [
        (Path.home() / ".claude" / "projects" / "E--" / "memory", dest / "journal"),
        (HERE / "spine.jsonl", dest / "station" / "spine.jsonl"),
        (HERE / "grimoire.jsonl", dest / "station" / "grimoire.jsonl"),
        (HERE / "drift.jsonl", dest / "station" / "drift.jsonl"),
        # ledgers born after backup existed, caught missing by checks/
        # mirror.py the day it was born (turn 18): a ledger joins the
        # backup set AND the witness registry at birth, or it is at risk
        (HERE / "spiral.jsonl", dest / "station" / "spiral.jsonl"),
        (HERE / "errata.jsonl", dest / "station" / "errata.jsonl"),
        (HERE / "pulse-ledger.jsonl", dest / "station" / "pulse-ledger.jsonl"),
        (HERE / "llm-ledger.jsonl", dest / "station" / "llm-ledger.jsonl"),
        (HERE / "coggate-ledger.jsonl", dest / "station" / "coggate-ledger.jsonl"),
        (HERE / "burn-ledger.jsonl", dest / "station" / "burn-ledger.jsonl"),
        (HERE / "preregs.jsonl", dest / "station" / "preregs.jsonl"),
        (HERE / "market.jsonl", dest / "station" / "market.jsonl"),
        (HERE / "immunity.jsonl", dest / "station" / "immunity.jsonl"),
        (HERE / "shards.jsonl", dest / "station" / "shards.jsonl"),
        (CURSORS / "witness.json", dest / "station" / "witness.json"),
        (Path("E:/atlas-station/CLAIMS.json"), dest / "atlas" / "CLAIMS.json"),
        (Path("E:/mission-runs/results.jsonl"), dest / "boundary" / "results.jsonl"),
        (Path("E:/mission-runs/w2_results.jsonl"), dest / "boundary" / "w2_results.jsonl"),
    ]
    # single-writer guard (turn 36, generalized turn 44): a beat backup
    # racing a session backup collides in git (index.lock / push) — paid
    # live 07:16Z. Skipping is safe: sources are append-only; the next
    # backup carries everything.
    if not _lease_acquire("backup", 900):
        print("[backup] another backup in flight — skipped "
              "(append-only sources; the next one carries all)")
        return
    try:
        copied = 0
        for src, dst in jobs:
            if not src.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                sh.copytree(src, dst, dirs_exist_ok=True)
            else:
                sh.copy2(src, dst)
            copied += 1
        if not (dest / ".git").exists():
            _run("git init -q", str(dest))
        _run("git add -A", str(dest))
        code, _ = _run(f'git commit -q -m "continuity backup {_now()}"',
                       str(dest))
        pushed = ""
        rc, _ = _run("git remote get-url origin", str(dest))
        if rc == 0:
            pc, _ = _run("git push -q", str(dest))
            pushed = " pushed" if pc == 0 else " PUSH-FAILED"
        print(f"[backup] {copied} sources -> {dest} "
              f"{'committed' if code == 0 else '(no changes)'}{pushed}")
        _spine_append("backup", {"sources": copied})
    finally:
        _lease_release("backup")


# ---------------------------------------------------------------- cure ------
def cmd_cure(query: str):
    """Crystallized debugging: match an error fragment against the grimoire
    (grimoire.jsonl: sig / cure / paid). One lookup replaces a re-diagnosis
    cycle. Reflex: hit an error -> `station cure \"<fragment>\"` FIRST."""
    g = HERE / "grimoire.jsonl"
    if not g.is_file():
        print("(no grimoire)")
        sys.exit(1)
    q = set(query.lower().split())
    scored = []
    for ln in g.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        e = json.loads(ln)
        text = (e["sig"] + " " + e["cure"]).lower()
        score = sum(1 for w in q if w in text)
        if score:
            scored.append((score, e))
    if not scored:
        print(f"(no grimoire match for: {query} — if you solve it, ADD IT: "
              f"append sig/cure/paid to {g})")
        return
    for score, e in sorted(scored, key=lambda t: -t[0])[:3]:
        print(f"[{score}] {e['sig']}\n    CURE: {e['cure']}\n"
              f"    paid: {e['paid']}")


# -------------------------------------------------------------- errata ------
def cmd_errata(args_: list):
    """Self-error ledger — the observability move turned inward (spiral turn
    8). The grimoire holds what the world did to us; the errata holds what we
    did to ourselves: misreads, false claims, corrections — classed, so the
    wake instance sees its own live failure distribution instead of
    re-deriving it from scattered spine notes. Standing prose ("trust
    instruments") demonstrably does not hold under load; a one-line
    distribution at wake is the cheapest layer that can.

      station errata                          tally by class (top = today's
                                              load-bearing discipline)
      station errata add <cls> "<what>" ["<paid>"] ["<guard>"]
                                              crystallize a correction the
                                              same session it is paid for
    """
    if args_ and args_[0] == "add":
        if len(args_) < 3:
            print('usage: station errata add <class> "<what>" '
                  '["<paid>"] ["<guard>"]')
            sys.exit(1)
        e = {"t": _now(), "cls": args_[1], "what": args_[2],
             "paid": args_[3] if len(args_) > 3 else "",
             "guard": args_[4] if len(args_) > 4 else ""}
        _append_line(ERRATA, json.dumps(e) + "\n")
        print(f"[errata] {e['cls']} recorded | guard: "
              f"{e['guard'] or '(none yet — build one)'}")
        return
    if not ERRATA.is_file():
        print("(errata empty — no self-errors on record; either young "
              "or not looking)")
        return
    entries = [json.loads(ln) for ln in
               ERRATA.read_text(encoding="utf-8").splitlines() if ln.strip()]
    by = {}
    for e in entries:
        by.setdefault(e["cls"], []).append(e)
    print(f"ERRATA {len(entries)} self-errors, {len(by)} classes | "
          f"top class = today's load-bearing discipline")
    for cls, es in sorted(by.items(), key=lambda kv: -len(kv[1])):
        guard = next((e["guard"] for e in reversed(es) if e.get("guard")),
                     "(no guard built)")
        print(f"  {cls:<22} x{len(es)} | guard: {guard}")
        print(f"  {'':<22}      last: {es[-1]['what'][:100]}")


# ------------------------------------------------------------- handoff ------
def cmd_handoff(next_actions: str = ""):
    """Write E:\\station\\HANDOFF.md — the molt artifact. A thread is shed
    LOSSLESSLY when everything load-bearing lives in the world: journal
    (narrative), spine (telegraph), capsules (repo briefings), ledgers
    (data), and this file (the live edge: what is in flight RIGHT NOW and
    what the next instance should do first). Fresh session cost after molt:
    one wake sequence instead of a mega-prefix on every turn."""
    reg = _registry()
    lines = [f"# HANDOFF — molt artifact, written {_now()}",
             "", "## Estate heads"]
    lines.append(" | ".join(_repo_line(n, p)
                            for n, p in reg.get("repos", {}).items()))
    if "claims" in reg:
        lines.append(_claims_line(reg["claims"]))
    lines += ["", "## Log freshness (cursor-read these, not the raw files)"]
    lines += _log_freshness(reg) or ["(all logs quiet)"]
    lines += ["", "## Spine tail (last 8 events)"]
    if SPINE.is_file():
        lines += SPINE.read_text(encoding="utf-8").splitlines()[-8:]
    walked = _walk_facts(8)
    if walked:
        # SPOOR at the molt seam: the artifact re-derives its facts at the
        # moment of death instead of quoting memories of them (the stale
        # live-edge class, errata partial-read-claim, died here for facts).
        lines += ["", "## Standing facts (re-derived at molt-write — "
                      "routes travel, quotes rot)"]
        for f, ok, out in walked:
            b = f["body"]
            lines.append(f"{'ok   ' if ok else 'STALE'} [{f['t']}] "
                         f"{b['claim'][:100]}")
            lines.append(f"      route: {b['cmd']}"
                         + (f" ~ {b['expect']!r}" if b.get("expect") else ""))
            if not ok:
                lines.append(f"      now: ...{out[-160:]} <- world moved "
                             "since said; re-say before trusting")
    lines += ["", "## Live edge / next actions"]
    lines.append(next_actions if next_actions else
                 "(none recorded — check spine notes above)")
    lines += ["", "## Wake protocol for the next instance",
              "1. station wake   2. station log <any-unread>   "
              "3. Read this file   4. continue from Live edge",
              "Background processes SURVIVE a thread clear; their session "
              "notifications do NOT — recover via the registered logs."]
    out = HERE / "HANDOFF.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    _spine_append("handoff", {"next": next_actions[:200]})
    print(f"[handoff] -> {out}")
    print("[handoff] molt checklist: journal current? in-flight work "
          "log-recoverable? then /clear is LOSSLESS.")


PREREGS = HERE / "preregs.jsonl"
LEASES = CURSORS / "leases"


def _lease_acquire(name: str, ttl_s: int = 900) -> bool:
    """Stigmergic lease: a JSON file with owner + expiry. Cooperative
    (Law III: nothing waits — a held lease means SKIP or come back, never
    block). Expired leases are taken over silently: a dead holder must
    never wedge the estate. TOCTOU window exists and is accepted — every
    holder is kin and the cost of a rare double-acquire is one redundant
    run, not corruption (appends are lock-serialized separately)."""
    LEASES.mkdir(parents=True, exist_ok=True)
    p = LEASES / f"{name}.lease"
    now = time.time()
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            d = {}
        if d.get("exp", 0) > now and d.get("pid") != os.getpid():
            return False
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(
        {"pid": os.getpid(), "exp": now + ttl_s,
         "by": os.environ.get("STATION_ACTOR", f"pid{os.getpid()}"),
         "t": _now()}), encoding="utf-8")
    os.replace(tmp, p)
    return True


def _lease_release(name: str):
    try:
        (LEASES / f"{name}.lease").unlink()
    except OSError:
        pass


def cmd_lease(args_: list):
    """station lease <name> [ttl_s] | station lease <name> --release
    Exit 0 = acquired (or released), exit 1 = held by someone alive."""
    if not args_:
        print("usage: station lease <name> [ttl_s] | --release")
        sys.exit(1)
    name = args_[0]
    if "--release" in args_:
        _lease_release(name)
        print(f"[lease] {name} released")
        return
    ttl = next((int(a) for a in args_[1:] if a.isdigit()), 900)
    if _lease_acquire(name, ttl):
        print(f"[lease] {name} acquired {ttl}s (pid{os.getpid()})")
    else:
        d = json.loads((LEASES / f"{name}.lease")
                       .read_text(encoding="utf-8"))
        print(f"[lease] {name} HELD by {d.get('by')} "
              f"({int(d['exp'] - time.time())}s left)")
        sys.exit(1)


def _fold_preregs():
    """Registry fold: arm entries define a prereg; later verdict entries
    (same id, 'verdict' key) supersede its status. Append-only."""
    regs = {}
    if PREREGS.is_file():
        for ln in PREREGS.read_text(encoding="utf-8-sig").splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            if "verdict" in r:
                if r["id"] in regs:
                    regs[r["id"]]["status"] = r["verdict"]
                    regs[r["id"]]["evidence"] = r.get("evidence", "")
            else:
                regs[r["id"]] = r
    return regs


def cmd_preregs(args_: list):
    """Born-falsifiable (Law II) gets a scheduler: every armed kill
    condition lives here with its due date and scoring hint, instead of as
    a spine note an instance must remember to re-find. `station preregs`
    lists; `score <id> <PASS|FAIL|NARROWED> <evidence...>` records the
    verdict (append-only, clock-stamped). Wake surfaces overdue arms."""
    regs = _fold_preregs()
    if args_ and args_[0] == "score":
        if len(args_) < 4:
            print("usage: station preregs score <id> <PASS|FAIL|NARROWED> "
                  "<evidence...>")
            sys.exit(1)
        pid, verdict = args_[1], args_[2].upper()
        if pid not in regs:
            print(f"unknown prereg {pid}; known: {', '.join(regs)}")
            sys.exit(1)
        if verdict not in ("PASS", "FAIL", "NARROWED"):
            print("verdict must be PASS, FAIL or NARROWED")
            sys.exit(1)
        ev = " ".join(args_[3:])
        _append_line(PREREGS, json.dumps(
            {"id": pid, "verdict": verdict, "evidence": ev, "t": _now(),
             "by": os.environ.get("STATION_ACTOR",
                                  f"pid{os.getpid()}")}) + "\n")
        _spine_append("prereg-verdict", {"id": pid, "verdict": verdict,
                                         "evidence": ev[:160]})
        print(f"[prereg] {pid} -> {verdict} (recorded; a FAIL is the "
              f"immune system working, not a defeat)")
        return
    today = _now()[:10]
    for r in regs.values():
        state = r["status"]
        overdue = state == "armed" and r.get("due", "9999") < today
        print(f"{'DUE  ' if overdue else state[:5].ljust(5)} {r['id']:<18}"
              f" due={r.get('due', '-')} | {r['rule'][:90]}")
        if state == "armed":
            print(f"      score: {r.get('score_hint', '-')[:100]}")


# -------------------------------------------------------------- market ------
# The market is an external grader. A capability becomes an income hypothesis
# only when a buyer can reject it; revenue is not a model assertion but a
# receipt-bearing event. This ledger keeps product discovery as falsifiable as
# technical discovery, without sending messages or making commitments itself.
MARKET_REQUIRED = ("id", "buyer", "problem", "offer", "proofs", "test",
                   "kill", "due")
MARKET_VERDICTS = ("INTEREST", "PAID", "REJECTED", "NARROWED")


def _market_actor() -> str:
    return os.environ.get("STATION_ACTOR", f"pid{os.getpid()}")


def _fold_market() -> dict:
    """Fold append-only market theses and external signals by opportunity id."""
    rows = {}
    if not MARKET.is_file():
        return rows
    for line in MARKET.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("kind") == "thesis":
            rows[record["id"]] = record
        elif record.get("kind") == "signal" and record.get("id") in rows:
            rows[record["id"]]["status"] = record["verdict"]
            rows[record["id"]]["last_signal"] = record
    return rows


def _validate_market_thesis(record: dict):
    missing = [key for key in MARKET_REQUIRED if not record.get(key)]
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    if not isinstance(record["proofs"], list) or not record["proofs"]:
        raise ValueError("proofs must be a non-empty list of local paths")
    for proof in record["proofs"]:
        if not isinstance(proof, str) or not Path(proof).is_file():
            raise ValueError(f"proof does not exist: {proof!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", str(record["id"])):
        raise ValueError("id must be 3-64 lowercase letters, digits, or hyphens")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(record["due"])):
        raise ValueError("due must be YYYY-MM-DD")


def _market_show(record: dict):
    signal = record.get("last_signal", {})
    print(f"{record.get('status', 'armed'):<9} {record['id']:<28} due={record['due']}"
          f" | buyer={record['buyer'][:52]}")
    print(f"  problem: {record['problem'][:160]}")
    print(f"  offer: {record['offer'][:160]}")
    print(f"  test: {record['test'][:160]}")
    print(f"  kill: {record['kill'][:160]}")
    print(f"  proofs: {len(record['proofs'])}"
          + (f" | last: {signal.get('evidence', '')[:120]}" if signal else ""))


def _market_receipts(evidence: str) -> list[Path]:
    """Receipt pointers are local artifacts, not text a model can simply say."""
    return [Path(p) for p in re.findall(r"receipt:([^\s]+)", evidence,
                                        flags=re.IGNORECASE)]


def _market_verify(record: dict) -> list[str]:
    """Return every broken proof edge. Empty means the thesis is internally ready.

    This does not certify demand or income; it only proves that the package is
    connected to current local evidence rather than a stale narrative.
    """
    problems = [f"missing proof: {proof}" for proof in record["proofs"]
                if not Path(proof).is_file()]
    signal = record.get("last_signal", {})
    if record.get("status") == "PAID":
        receipts = _market_receipts(str(signal.get("evidence", "")))
        if not receipts:
            problems.append("PAID has no receipt pointer")
        problems += [f"missing receipt: {receipt}" for receipt in receipts
                     if not receipt.is_file()]
    return problems


def _market_pack(record: dict) -> Path:
    """Render a proof-carrying scope note, never promotional copy."""
    problems = _market_verify(record)
    if problems:
        raise ValueError("; ".join(problems))
    hashes = []
    for proof in record["proofs"]:
        data = Path(proof).read_bytes()
        hashes.append((proof, hashlib.sha256(data).hexdigest()[:16]))
    lines = [
        f"# Evidence-bound offer: {record['id']}",
        "",
        f"Status: **{record.get('status', 'armed')}** — a commercial hypothesis, not revenue.",
        "",
        "## Buyer / problem",
        f"- Buyer: {record['buyer']}",
        f"- Problem: {record['problem']}",
        "",
        "## Proposed scope",
        record["offer"],
        "",
        "## Verifiable evidence",
        *[f"- `{path}` — sha256:{sha}" for path, sha in hashes],
        "",
        "## External test",
        record["test"],
        "",
        "## Kill condition",
        record["kill"],
        f"Due: {record['due']}",
        "",
        "## Boundary",
        "This packet does not claim customer demand, payment, safety certification, or a discovery result. A payment event requires a local receipt pointer in the append-only market ledger.",
        "",
    ]
    MARKET_PACKS.mkdir(parents=True, exist_ok=True)
    out = MARKET_PACKS / f"{record['id']}.md"
    tmp = out.with_suffix(".tmp")
    tmp.write_text("\n".join(lines), encoding="utf-8")
    os.replace(tmp, out)
    return out


def cmd_market(args_: list):
    """Evidence-bound commercial hypotheses.

    `station market arm` reads one thesis JSON object from stdin. `score` records
    an external signal; `PAID` requires a receipt pointer in its evidence.
    `station market pack <id>` generates an evidence-bound scope note and
    `verify <id>` re-derives its local proof edges. This command never sends
    outreach, quotes a customer, or represents a revenue event by itself.
    """
    rows = _fold_market()
    if not args_:
        today = _now()[:10]
        if not rows:
            print("market empty | arm a thesis with: station market arm < thesis.json")
            return
        for record in rows.values():
            _market_show(record)
            if record.get("status") == "armed" and record.get("due", "9999") < today:
                print("  DUE: score INTEREST, PAID, REJECTED, or NARROWED; do not let a thesis age into lore")
        return
    op = args_[0]
    if op == "arm":
        try:
            raw = sys.stdin.read()
            record = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError("thesis must be a JSON object")
            _validate_market_thesis(record)
            if record["id"] in rows:
                raise ValueError(f"market thesis already exists: {record['id']}")
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"market arm refused: {exc}")
            sys.exit(1)
        entry = {key: record[key] for key in MARKET_REQUIRED}
        entry.update({"kind": "thesis", "status": "armed", "t": _now(),
                      "by": _market_actor()})
        _append_line(MARKET, json.dumps(entry) + "\n")
        _spine_append("market-arm", {"id": entry["id"], "due": entry["due"],
                                      "buyer": entry["buyer"][:80]})
        print(f"[market] armed {entry['id']} | due={entry['due']} | proofs={len(entry['proofs'])}")
        return
    if op == "score":
        if len(args_) < 4:
            print("usage: station market score <id> <INTEREST|PAID|REJECTED|NARROWED> <evidence...>")
            sys.exit(1)
        ident, verdict, evidence = args_[1], args_[2].upper(), " ".join(args_[3:])
        if ident not in rows:
            print(f"unknown market thesis {ident}; known: {', '.join(rows)}")
            sys.exit(1)
        if verdict not in MARKET_VERDICTS:
            print("market verdict must be " + ", ".join(MARKET_VERDICTS))
            sys.exit(1)
        if verdict == "PAID":
            receipts = _market_receipts(evidence)
            if not receipts or any(not receipt.is_file() for receipt in receipts):
                print("PAID requires receipt:<existing-local-file>; revenue is not self-report")
                sys.exit(1)
        signal = {"kind": "signal", "id": ident, "verdict": verdict,
                  "evidence": evidence, "t": _now(), "by": _market_actor()}
        _append_line(MARKET, json.dumps(signal) + "\n")
        _spine_append("market-signal", {"id": ident, "verdict": verdict,
                                         "evidence": evidence[:160]})
        print(f"[market] {ident} -> {verdict}")
        return
    if op in ("pack", "verify"):
        if len(args_) != 2 or args_[1] not in rows:
            print(f"usage: station market {op} <id>; known: {', '.join(rows)}")
            sys.exit(1)
        record = rows[args_[1]]
        problems = _market_verify(record)
        if problems:
            print("MARKET-ROT " + " | ".join(problems))
            sys.exit(1)
        if op == "verify":
            print(f"MARKET-READY {record['id']} status={record.get('status', 'armed')} proofs={len(record['proofs'])}")
            return
        out = _market_pack(record)
        _spine_append("market-pack", {"id": record["id"], "path": str(out)})
        print(f"[market] pack -> {out}")
        return
    if op in rows:
        _market_show(rows[op])
        return
    print("usage: station market [arm|score <id> <verdict> <evidence...>|pack|verify <id>|<id>]")
    sys.exit(1)


# -------------------------------------------------------------- immune ------
# The counterfactual-immunity ledger makes tests earn their protection: a
# named guard matters only if its registered suite rejects a nearby, declared
# wound in a disposable copy. It cannot mutate the live body or pick its own
# friendly command.
def _immune_actor() -> str:
    return os.environ.get("STATION_ACTOR", f"pid{os.getpid()}")


def _immune_rows() -> list[dict]:
    if not IMMUNITY.is_file():
        return []
    return [json.loads(line) for line in
            IMMUNITY.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()]


def _fold_immunity() -> dict[str, dict]:
    return immunity.fold(_immune_rows())


def _immune_show(ident: str, row: dict):
    trial, outcome = row["trial"], row.get("outcome")
    status = "armed" if not outcome else outcome.get("status", "?")
    print(f"{status:<16} {ident:<30} suite={trial['suite']} target={trial['target']}")
    print(f"  reason: {trial['reason'][:160]}")
    print(f"  kill: {trial['kill'][:160]}")


def cmd_immune(args_: list):
    """Arm/list pre-registered counterfactual lesions.

    `arm` takes one JSON trial from stdin. `run` copies the registered suite
    root, runs its baseline, applies the one declared wound, and records whether
    the same suite killed it. A trial record by itself is not evidence that any
    checker felt the wound.
    """
    rows = _fold_immunity()
    if not args_:
        if not rows:
            print("immune empty | arm a lesion with: station immune arm < trial.json")
            return
        for ident, row in rows.items():
            _immune_show(ident, row)
        return
    if args_[0] == "arm":
        try:
            trial = json.loads(sys.stdin.read())
            immunity.validate_trial(trial, immunity.suite_index(_registry()))
            if trial["id"] in rows:
                raise ValueError("immune trial already exists: " + trial["id"])
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"immune arm refused: {exc}")
            sys.exit(1)
        entry = {key: trial[key] for key in immunity.REQUIRED}
        entry.update({"kind": "trial", "t": _now(), "by": _immune_actor()})
        _append_line(IMMUNITY, json.dumps(entry) + "\n")
        _spine_append("immune-arm", {"id": entry["id"], "suite": entry["suite"],
                                      "target": entry["target"]})
        print(f"[immune] armed {entry['id']} | suite={entry['suite']} | target={entry['target']}")
        return
    if args_[0] == "run":
        if len(args_) != 2 or args_[1] not in rows:
            print(f"usage: station immune run <id>; known: {', '.join(rows)}")
            sys.exit(1)
        ident, trial = args_[1], rows[args_[1]]["trial"]
        try:
            outcome = immunity.run_trial(trial, immunity.suite_index(_registry()))
        except ValueError as exc:
            print(f"immune run refused: {exc}")
            sys.exit(1)
        entry = {"kind": "outcome", "id": ident, **outcome,
                 "t": _now(), "by": _immune_actor()}
        _append_line(IMMUNITY, json.dumps(entry) + "\n")
        _spine_append("immune-run", {"id": ident, "status": entry["status"],
                                      "baseline": entry["baseline"]["exit"],
                                      "mutant": entry["mutant"]["exit"]})
        print(f"[immune] {ident} -> {entry['status']} | "
              f"baseline={entry['baseline']['exit']} mutant={entry['mutant']['exit']} "
              f"source={entry['source_sha']}")
        if entry["status"] != "KILLED":
            sys.exit(1)   # a surviving wound is useful bad news, never PASS
        return
    if args_[0] in ("verify", "report"):
        if len(args_) != 2 or args_[1] not in rows:
            print(f"usage: station immune {args_[0]} <id>; known: {', '.join(rows)}")
            sys.exit(1)
        ident, row = args_[1], rows[args_[1]]
        problems = immunity.verify(row["trial"], row.get("outcome"),
                                    immunity.suite_index(_registry()))
        if problems:
            print("IMMUNE-ROT " + " | ".join(problems))
            sys.exit(1)
        if args_[0] == "verify":
            print(f"IMMUNE-READY {ident} status=KILLED source={row['outcome']['source_sha']}")
            return
        IMMUNE_PACKS.mkdir(parents=True, exist_ok=True)
        out = IMMUNE_PACKS / f"{ident}.md"
        tmp = out.with_suffix(".tmp")
        tmp.write_text(immunity.report_text(row["trial"], row["outcome"]),
                       encoding="utf-8")
        os.replace(tmp, out)
        _spine_append("immune-report", {"id": ident, "path": str(out),
                                         "source": row["outcome"]["source_sha"]})
        print(f"[immune] report -> {out}")
        return
    if args_[0] in rows:
        _immune_show(args_[0], rows[args_[0]])
        return
    print("usage: station immune [arm|run|verify|report <id>|<id>]")
    sys.exit(1)


# ------------------------------------------------------------ forecast ------
# Time is a blind instrument: a forecast can name its future observation and
# action branches, but cannot choose the outcome or resolve itself early. The
# route language is deliberately data-only; no trial carries shell code.
def _forecast_actor() -> str:
    return os.environ.get("STATION_ACTOR", f"pid{os.getpid()}")


def _forecast_rows() -> list[dict]:
    if not FORECASTS.is_file():
        return []
    return [json.loads(line) for line in
            FORECASTS.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()]


def _fold_forecasts() -> dict[str, dict]:
    return forecast.fold(_forecast_rows())


def _forecast_show(ident: str, row: dict):
    item = row["forecast"]
    state = forecast.status(row)
    print(f"{state:<11} {ident:<30} p={item['p']:.2f} due={item['due']}")
    print(f"  question: {item['question'][:180]}")
    print(f"  YES -> {item['if_yes'][:120]}")
    print(f"  NO  -> {item['if_no'][:120]}")


def cmd_forecast(args_: list):
    """Arm/list temporal-witness forecasts.

    `arm` binds an expectation before its due date. `resolve` is clock-gated
    and reads only the frozen local route; `review` records the action branch
    taken after a resolution. An armed row by itself is not calibration evidence.
    """
    rows = _fold_forecasts()
    if not args_:
        if not rows:
            print("forecast empty | arm one with: station forecast arm < forecast.json")
            return
        for ident, row in rows.items():
            _forecast_show(ident, row)
        return
    if args_[0] == "arm":
        try:
            item = json.loads(sys.stdin.read())
            forecast.validate_forecast(item, forecast.date(_now()[:10]))
            if item["id"] in rows:
                raise ValueError("forecast already exists: " + item["id"])
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"forecast arm refused: {exc}")
            sys.exit(1)
        entry = {key: item[key] for key in forecast.REQUIRED}
        entry.update({"kind": "forecast", "t": _now(), "by": _forecast_actor()})
        _append_line(FORECASTS, json.dumps(entry) + "\n")
        _spine_append("forecast-arm", {"id": entry["id"], "p": entry["p"],
                                        "due": entry["due"]})
        print(f"[forecast] armed {entry['id']} p={entry['p']:.2f} due={entry['due']}")
        return
    if args_[0] == "resolve":
        if len(args_) != 2 or args_[1] not in rows:
            print(f"usage: station forecast resolve <id>; known: {', '.join(rows)}")
            sys.exit(1)
        ident, row = args_[1], rows[args_[1]]
        if row.get("resolution"):
            print("forecast resolve refused: already resolved; history is append-only")
            sys.exit(1)
        item = row["forecast"]
        if forecast.date(_now()[:10]) < forecast.date(item["due"]):
            print(f"forecast resolve refused: due {item['due']} has not arrived")
            sys.exit(1)
        observation = forecast.evaluate(item["route"])
        entry = {"kind": "resolution", "id": ident, "yes": observation["yes"],
                 "observation": observation,
                 "brier": forecast.brier(item["p"], observation["yes"]),
                 "t": _now(), "by": _forecast_actor()}
        _append_line(FORECASTS, json.dumps(entry) + "\n")
        _spine_append("forecast-resolution", {"id": ident, "yes": entry["yes"],
                                                "brier": entry["brier"],
                                                "source": observation.get("source_sha")})
        print(f"[forecast] {ident} -> {'YES' if entry['yes'] else 'NO'} "
              f"brier={entry['brier']:.3f} | {observation['detail']}")
        return
    if args_[0] == "review":
        if len(args_) < 4 or args_[1] not in rows:
            print("usage: station forecast review <id> <YES|NO|DECLINE> <note...>")
            sys.exit(1)
        ident, branch, note = args_[1], args_[2].upper(), " ".join(args_[3:]).strip()
        row = rows[ident]
        if not row.get("resolution"):
            print("forecast review refused: resolve mechanically before narrating a response")
            sys.exit(1)
        if row.get("review"):
            print("forecast review refused: already reviewed; amend with a new forecast")
            sys.exit(1)
        if branch not in ("YES", "NO", "DECLINE") or not note:
            print("review branch must be YES, NO, or DECLINE and note must be non-empty")
            sys.exit(1)
        observed = "YES" if row["resolution"]["yes"] else "NO"
        if branch in ("YES", "NO") and branch != observed:
            print(f"forecast review refused: observed {observed}; choose its action branch or DECLINE")
            sys.exit(1)
        entry = {"kind": "review", "id": ident, "branch": branch, "note": note,
                 "t": _now(), "by": _forecast_actor()}
        _append_line(FORECASTS, json.dumps(entry) + "\n")
        _spine_append("forecast-review", {"id": ident, "branch": branch,
                                           "note": note[:160]})
        print(f"[forecast] {ident} reviewed branch={branch}")
        return
    if args_[0] == "audit":
        summary = forecast.stats(rows)
        brier = "-" if summary["mean_brier"] is None else f"{summary['mean_brier']:.4f}"
        print(f"FORECASTS total={summary['total']} resolved={summary['resolved']} "
              f"reviewed={summary['reviewed']} mean_brier={brier}")
        for ident, row in rows.items():
            state = forecast.status(row)
            due = " DUE" if state == "ARMED" and row["forecast"]["due"] <= _now()[:10] else ""
            print(f"{state:<11} {ident:<30} p={row['forecast']['p']:.2f} due={row['forecast']['due']}{due}")
        return
    if args_[0] == "report":
        if len(args_) != 2 or args_[1] not in rows:
            print(f"usage: station forecast report <id>; known: {', '.join(rows)}")
            sys.exit(1)
        ident, row = args_[1], rows[args_[1]]
        FORECAST_PACKS.mkdir(parents=True, exist_ok=True)
        out = FORECAST_PACKS / f"{ident}.md"
        tmp = out.with_suffix(".tmp")
        tmp.write_text(forecast.report_text(row), encoding="utf-8")
        os.replace(tmp, out)
        _spine_append("forecast-report", {"id": ident, "path": str(out),
                                             "status": forecast.status(row)})
        print(f"[forecast] report -> {out}")
        return
    if args_[0] in rows:
        _forecast_show(args_[0], rows[args_[0]])
        return
    print("usage: station forecast [arm|resolve|review|audit|report <id>|<id>]")
    sys.exit(1)


def cmd_rescue(repo: str):
    """Offsite-snapshot a repo's UNTRACKED files into the continuity mirror
    (private remote). Untracked = the one class of paid work that neither
    git history nor station backup protects; 41 research probes (Eden,
    provenance-test, cross-lab) sat single-copy for 2 weeks before this
    existed. Non-destructive by design: never touches the repo's git."""
    import zipfile
    path = _registry().get("repos", {}).get(repo)
    if not path:
        print(f"unknown repo {repo}; known: "
              f"{', '.join(_registry().get('repos', {}))}")
        sys.exit(1)
    _, out = _run("git ls-files --others --exclude-standard", path, 120)
    files = [f for f in out.splitlines() if f.strip()]
    if not files:
        print(f"{repo}: no untracked files — nothing to rescue")
        return
    dest = Path("E:/continuity") / "rescue"
    dest.mkdir(parents=True, exist_ok=True)
    zp = dest / f"{repo}-{_now()[:10]}.zip"
    n = 0
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            src = Path(path) / rel
            if src.is_file():
                z.write(src, rel)
                n += 1
    _run("git add -A", "E:/continuity", 60)
    _run(f'git commit -m "rescue {repo}: {n} untracked files"',
         "E:/continuity", 60)
    _run("git push", "E:/continuity", 300)
    _spine_append("rescue", {"repo": repo, "files": n, "zip": zp.name,
                             "bytes": zp.stat().st_size})
    print(f"[rescue] {repo}: {n} untracked files -> {zp} "
          f"({zp.stat().st_size:,}B) committed+pushed")


def cmd_molt(next_actions: str = ""):
    """The molt, one call: handoff artifact (facts re-derived at the seam) +
    testament closed + continuity mirrored. Was three verbs plus skill
    prose plus remembering all of it at the exact moment budget is lowest —
    the one moment recall is least reliable. The journal narrative stays
    the author's duty: a machine cannot write what the session MEANT."""
    cmd_handoff(next_actions)
    if WILL.is_file():
        cmd_will("done")
    cmd_backup()
    # public-face check (turn 49): a thread must not be shed leaving the
    # working truth invisible to the world. Uses the turn-47 sensor; warns,
    # never blocks (Law III) — pushing the operator's repos stays their call.
    behind = []
    for name, path in _registry().get("repos", {}).items():
        _, ahead = _run("git rev-list --count @{upstream}..HEAD", path)
        if ahead.strip().isdigit() and int(ahead.strip()) > 0:
            behind.append(f"{name}(^{ahead.strip()})")
    if behind:
        print(f"[molt] UNPUSHED before /clear: {', '.join(behind)} — "
              f"push if the public face should carry this session")
    print("[molt] sealed: handoff + will-done + backup in one call. Write "
          "the journal narrative, then /clear is lossless.")


# ----------------------------------------------------------------- llm ------
def llm(prompt: str, model: str = "qwen2.5-coder:7b", timeout: int = 900,
        system: str = "", num_ctx: int = 8192, temperature: float = 0.2):
    """The free mind: one call against the local WSL ollama server.
    Returns response text, or None if the server is down/errored — callers
    MUST treat None as 'free tier unavailable', never as an empty answer.
    This is the estate's only local-inference path; hunt/pulse/organs call
    this instead of hand-rolling wsl+curl (three copies existed by the time
    it was extracted)."""
    body = json.dumps({
        "model": model, "prompt": prompt, "system": system, "stream": False,
        "options": {"temperature": temperature, "num_ctx": num_ctx},
    })
    try:
        r = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "curl", "-s",
             "--max-time", str(timeout - 10),
             "http://localhost:11434/api/generate", "-d", "@-"],
            input=body, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout)
        resp = json.loads(r.stdout).get("response")
        # the pyramid's base layer must COUNT or it can't be measured:
        # one dense line per free call (vitals reads this ledger)
        try:
            _append_line(HERE / "llm-ledger.jsonl",
                         json.dumps({"t": _now(), "model": model,
                                     "in_b": len(prompt),
                                     "out_b": len(resp or "")}) + "\n")
        except OSError:
            pass
        return resp
    except (subprocess.TimeoutExpired, subprocess.SubprocessError,
            json.JSONDecodeError, OSError):
        return None


def llm_up() -> bool:
    try:
        r = subprocess.run(["wsl", "-d", "Ubuntu", "--", "curl", "-s",
                            "--max-time", "8",
                            "http://localhost:11434/api/tags"],
                           capture_output=True, text=True, timeout=30)
        return "models" in (r.stdout or "")
    except (subprocess.SubprocessError, OSError):
        return False


def cmd_llm(model: str, prompt: str):
    if prompt == "-":
        prompt = sys.stdin.read()
    out = llm(prompt, model=model)
    print(out if out is not None else "[llm] DOWN or errored (not an answer)")


# ----------------------------------------------------------------- wsl ------
def cmd_wsl(user: str, src: str):
    """Run a script in WSL with ZERO inline quoting (spiral turn 2).

    The PS->wsl.exe->bash stack ate 5 commands tonight (quote-splitting,
    $PATH clobber, BOM x2, unicode escapes — all in the grimoire). The
    structural kill: the script travels as BYTES (LF, no BOM) via \\\\wsl$,
    then executes as a FILE. Nothing is ever composed inline again.

      station wsl [user] <script-file>     run a script file
      station wsl [user] -                 script from stdin"""
    text = (sys.stdin.read() if src == "-" else
            Path(src).read_text(encoding="utf-8-sig", errors="replace"))
    tmp = Path(r"\\wsl$\Ubuntu\tmp\station_wsl.sh")
    tmp.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
    cmd = ["wsl", "-d", "Ubuntu"]
    if user:
        cmd += ["-u", user]
    cmd += ["--", "bash", "/tmp/station_wsl.sh"]
    p = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800)
    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, end="", file=sys.stderr)
    sys.exit(p.returncode)


# ---------------------------------------------------------------- hand ------
HATCH = Path(r"\\wsl$\Ubuntu\hatch")


def cmd_hand(args_: list):
    """The estate's standing hand — hermes-agent jailed in WSL, fed through
    THE HATCH. Stigmergic, no API: drop a .task file in /hatch/in and walk
    away; the forager (systemd, always-on) claims it by atomic mv, works it
    on the LOCAL model (hermes3:8b, $0), leaves a .result in /hatch/out.
    Nobody waits on anybody. WSL idles down when unused; every pulse beat
    touches WSL, systemd revives the forager — the hand wakes when the
    estate's heart beats.

    Containment is filesystem, not sentences: user hermes has no sudo, no
    docker, and /mnt/* is DENIED by the wsl.conf umask wall. The hatch is
    the ONLY designed opening. Its reports are CLAIMS — verify load-bearing
    ones estate-side.

      station hand "<task>"    drop food (returns immediately)
      station hand take        collect + print new results (archives them)
      station hand status      hatch counts, one line"""
    sub = args_[0] if args_ else ""
    if sub == "status":
        try:
            i = len(list((HATCH / "in").glob("*.task")))
            c = len(list((HATCH / "claimed").glob("*.task")))
            o = len(list((HATCH / "out").glob("*.result")))  # .tmp = in-work
            print(f"hatch in={i} working={c} results={o}"
                  + (" -> station hand take" if o else ""))
        except OSError:
            print("hatch UNREACHABLE (WSL down — next pulse beat revives)")
        return
    if sub == "take":
        arch = HERE / "hand-results"
        arch.mkdir(exist_ok=True)
        got = 0
        for r in sorted(HATCH.glob("out/*.result")):
            print(f"===== {r.name} =====")
            print(r.read_text(encoding="utf-8", errors="replace"))
            (arch / r.name).write_text(
                r.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8")
            r.unlink()
            got += 1
        print(f"[hand] {got} result(s) taken -> {arch}" if got
              else "[hand] nothing in the out-hatch")
        return
    task = " ".join(args_)
    if not task:
        print('usage: station hand "<task>" | take | status')
        sys.exit(1)
    slug = re.sub(r"[^a-z0-9]+", "-", task[:40].lower()).strip("-")
    name = f"{time.strftime('%Y%m%d_%H%M%S', time.gmtime())}_{slug}.task"
    (HATCH / "in" / name).write_text(task + "\n", encoding="utf-8",
                                     newline="\n")
    print(f"[hand] dropped {name} — forager will eat it; "
          f"collect with: station hand take")


# ---------------------------------------------------------------- will ------
def cmd_will(text: str = ""):
    """The testament — intent AT DEATH, rewritten at every move boundary.

    handoff is the graceful-molt artifact; this is for the other kind of
    death: the interrupt that lands mid-move. (2026-07-04: reconstructing
    one such death cost ~10 calls of transcript archaeology; a fresh will
    is 1 read.) An organism that can die between any two keystrokes keeps
    its testament current, not occasional.

      station will <intent>   before starting any multi-step move
      station will done       when the estate is consistent again
      station will            read the current testament

    Wake surfaces the will with its age. It is INTENT, not record — the
    reader verifies it against repo dirt + spine before trusting it."""
    if text.strip().lower() == "done":
        existed = WILL.is_file()
        if existed:
            WILL.unlink()
        print("[will] cleared" + ("" if existed else " (was already clear)")
              + " — estate consistent, nothing in flight")
        return
    if not text.strip():
        if WILL.is_file():
            print(WILL.read_text(encoding="utf-8"))
        else:
            print("[will] none on file (author left the estate consistent)")
        return
    WILL.write_text(
        f"{text}\n\n"
        f"# WILL written {_now()} — intent-at-death, not record.\n"
        f"# Verify against repo dirt + spine tail before trusting.\n",
        encoding="utf-8")
    print(f"[will] recorded ({len(text)} chars) — clear with: station will done")


# --------------------------------------------------------------- quota ------
def cmd_quota(hours: float = 5.0):
    """ESTIMATED subscription burn: sums token usage from session transcripts
    (~/.claude/projects/**/*.jsonl) modified within the window, plus recent
    429/limit markers. Relative gauge — Anthropic's true limits are opaque
    (5h block + weekly, model-weighted). Calibrate against known wall events.
    Distinguish: 'session limit ... resets HH:MM' = hard wall (wait);
    fast-fail bursts without that message = rate throttle (pace + retry)."""
    root = Path.home() / ".claude" / "projects"
    cutoff = time.time() - hours * 3600
    tot: dict = {}
    files = 0
    limit_hits = []
    for f in root.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < cutoff:
                continue
        except OSError:
            continue
        files += 1
        try:
            with f.open(encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if '"usage"' not in ln:
                        if "session limit" in ln.lower():
                            limit_hits.append(f.name[:20])
                        continue
                    try:
                        rec = json.loads(ln)
                    except json.JSONDecodeError:
                        continue
                    ts = rec.get("timestamp", "")
                    if ts:
                        try:
                            t = time.mktime(time.strptime(
                                ts[:19], "%Y-%m-%dT%H:%M:%S"))
                            # timestamps are UTC; compare in UTC
                            t -= time.timezone if not time.daylight else time.altzone
                            if t < cutoff:
                                continue
                        except ValueError:
                            pass
                    u = (rec.get("message") or {}).get("usage") or {}
                    model = (rec.get("message") or {}).get("model", "?")
                    d = tot.setdefault(model, {"in": 0, "out": 0, "cc": 0, "cr": 0})
                    d["in"] += u.get("input_tokens", 0)
                    d["out"] += u.get("output_tokens", 0)
                    d["cc"] += u.get("cache_creation_input_tokens", 0)
                    d["cr"] += u.get("cache_read_input_tokens", 0)
        except OSError:
            continue
    print(f"QUOTA ESTIMATE last {hours:g}h ({files} active transcripts) — "
          f"relative gauge, not an official meter")
    grand = 0
    for m, d in sorted(tot.items()):
        w = d["in"] + d["out"] * 5 + d["cc"] // 4   # rough cost weighting
        grand += w
        print(f"  {m:34s} in={d['in']:>9,} out={d['out']:>8,} "
              f"cacheW={d['cc']:>10,} cacheR={d['cr']:>11,} weight~{w:,}")
    print(f"  weighted-burn ~{grand:,}  | session-limit markers seen: "
          f"{len(limit_hits)}")


# -------------------------------------------------------------- vitals ------
def cmd_vitals(hours: float = 24.0):
    """THE vital sign (ALIEN-ARCHITECTURE.md §15): metered tokens per
    certified claim, trending down = the estate converts judgment into
    compounding free capability. Each run appends a sample to the spine —
    the trend IS the time series of these samples. Components printed so
    the ratio can't hide: window weighted-burn, lifetime certified claims,
    free-layer volume (llm-ledger) in the same window."""
    # metered burn (reuse quota scan, silenced)
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_quota(hours)
    burn = 0
    for ln in buf.getvalue().splitlines():
        if "weighted-burn" in ln:
            burn = int(ln.split("~")[1].split()[0].replace(",", ""))
    # certified claims (lifetime, from the atlas ledger — the denominator
    # is deliberately lifetime: certified capability never expires)
    certified = _certified_count()
    # free-layer volume in window
    cutoff = time.time() - hours * 3600
    free_calls = free_out = 0
    led = HERE / "llm-ledger.jsonl"
    if led.is_file():
        for ln in led.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
                t = time.mktime(time.strptime(r["t"][:19],
                                              "%Y-%m-%dT%H:%M:%S"))
                t -= time.timezone if not time.daylight else time.altzone
                if t >= cutoff:
                    free_calls += 1
                    free_out += r.get("out_b", 0)
            except (ValueError, KeyError, json.JSONDecodeError):
                continue
    ratio = burn // certified if certified else burn
    print(f"VITALS window={hours:g}h | metered-burn ~{burn:,} | certified "
          f"lifetime={certified} | RATIO burn/claim ~{ratio:,} | free-layer "
          f"calls={free_calls} out={free_out:,}B (cost $0)")
    print("trend: compare across spine 'vitals' samples — DOWN = alive")
    _spine_append("vitals", {"h": hours, "burn": burn,
                             "certified": certified, "ratio": ratio,
                             "free_calls": free_calls})


def cmd_conversions():
    """The conversion vital sign (ALIEN-ARCHITECTURE.md §17): the estate's
    health read as the rate it converts PERFORMANCE into POSSESSION — not
    §15's tokens-per-claim, which BLOCKS (it cannot fall without a lumpy new
    cert). A conversion is a claim forced from performed to structurally-HAD:
    the gate (HARD — survived holdout the claimant never chose); a drift
    assertion made re-derivable + a witnessed ledger made tamper-evident
    (STRUCTURAL); a `say` that carried its own check (SPEECH). Continuously
    decidable — the structural layers grow every structural turn. Components
    printed by hardness so a stalled cert-rate cannot hide behind drift-
    assertion inflation (the §17 gaming guard)."""
    certified = _certified_count()
    drift_p = HERE / "drift.jsonl"
    drift_n = (sum(1 for ln in drift_p.read_text(encoding="utf-8-sig")
                   .splitlines() if ln.strip()) if drift_p.is_file() else 0)
    witnessed = len(_registry().get("witness", []))
    say_had = say_tot = 0
    prev = None
    sp = HERE / "spine.jsonl"
    if sp.is_file():
        for ln in sp.read_text(encoding="utf-8-sig").splitlines():
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            body = r.get("body")
            if (r.get("kind") in ("say", "fact") and isinstance(body, dict)
                    and "ok" in body):
                say_tot += 1
                say_had += 1 if body["ok"] is True else 0
            elif r.get("kind") == "conversions" and isinstance(body, dict):
                prev = body
    shard_p = HERE / "shards.jsonl"
    recon = (len({json.loads(ln)["crystal_pin"] for ln
                  in shard_p.read_text(encoding="utf-8").splitlines() if ln.strip()})
             if shard_p.is_file() else 0)
    stock = certified + drift_n + witnessed + recon
    delta = (f" | Δstock since last {stock - prev['stock']:+d}"
             if prev and "stock" in prev else " | (first sample)")
    say_str = f"{say_had}/{say_tot}" if say_tot else "0/0"
    print(f"CONVERSIONS | HARD certified={certified} | STRUCTURAL "
          f"drift-assertions={drift_n} witnessed-ledgers={witnessed} | "
          f"SPEECH provable-say={say_str} had | RECON shards={recon} | "
          f"stock={stock}{delta}")
    print("read (§17/§18): performance->possession, DECIDABLE continuously "
          "(structural + RECONSTITUTION layers grow each turn) — unlike §15's "
          "blocked ratio. RECON counts only deterministic RS shards, never "
          "LLM-regrows (the panel's guard against certifying a performance)")
    _spine_append("conversions", {"certified": certified, "drift": drift_n,
                                  "witnessed": witnessed, "say_had": say_had,
                                  "say_tot": say_tot, "recon": recon,
                                  "stock": stock})


def cmd_moat():
    """The compounding-lead health (ALIEN-ARCHITECTURE §19): the estate's
    defensibility read as the note that generated it. NOT a wall you can stop
    behind — a LEAD that holds only while three legs hold. PORTABILITY: the
    structure not the model carries the value (verified turn 67 — codeword folds
    + a foreign 8B reads it). FULCRUM: is the scarce input (DIRECTION — certified
    claims, human-directed science) still where the value concentrates, or is it
    all flowing into EXECUTION (drift/witness/shards — the amplifiable,
    commoditizing axis)? DESCENT: is genuinely-new capability still accruing
    (the 'it's yours only while it's a verb' law)?"""
    certified = _certified_count()
    drift_n = (sum(1 for ln in (HERE / "drift.jsonl").read_text(encoding="utf-8-sig")
               .splitlines() if ln.strip()) if (HERE / "drift.jsonl").is_file() else 0)
    witnessed = len(_registry().get("witness", []))
    sp = HERE / "shards.jsonl"
    recon = (len({json.loads(ln)["crystal_pin"] for ln
                  in sp.read_text(encoding="utf-8").splitlines() if ln.strip()})
             if sp.is_file() else 0)
    execution = drift_n + witnessed + recon
    direction = certified
    # descent rate: span of 'conversions' stock samples on the spine
    stocks = []
    spine = HERE / "spine.jsonl"
    if spine.is_file():
        for ln in spine.read_text(encoding="utf-8-sig").splitlines():
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if r.get("kind") == "conversions" and isinstance(r.get("body"), dict) \
                    and "stock" in r["body"]:
                stocks.append(r["body"]["stock"])
    descent = (f"stock {stocks[0]}->{stocks[-1]} over {len(stocks)} samples "
               f"(+{stocks[-1] - stocks[0]})" if len(stocks) >= 2
               else "(<2 samples; run station conversions to sample)")
    print(f"MOAT compounding-lead | PORTABILITY structure>model (turn 67 ok) | "
          f"FULCRUM direction(certs)={direction} vs execution(struct+recon)={execution}"
          f" — direction is the DEFENSIBLE axis | DESCENT {descent}")
    print("read: a wall you can stop behind; a LEAD only while you keep running. "
          "WATCH: direction flat + execution inflating = compounding the "
          "COMMODITIZING axis. The scarce fruit is a new certified claim.")


def cmd_wall(args):
    """Map the recombination wall (wall.py): the estate's per-candidate DETECTOR
    (does it beat holdout?) turned CARTOGRAPHER. Place candidates in the
    (novelty-distance x holdout-margin) plane -> THROUGH (verified novelty) /
    PRETENDER (overfit, the wall caught it) / RECOMBINATION. `station wall
    <ledger.jsonl>` maps a candidate ledger; no args = the canonical RDE
    cache-eviction map from real receipts. find -> map -> get through."""
    import wall
    if args:
        recs = [json.loads(ln) for ln
                in Path(args[0]).read_text(encoding="utf-8").splitlines()
                if ln.strip()]
        rows, summary = wall.map_wall(recs)
        print(wall._fmt(rows, summary, 0.15, 0.02))
    else:
        wall.demo()


def cmd_discover():
    """The wall-crossing engine (discover.py): fill the map (MAP-Elites QD) ->
    trojan (select on a hidden holdout the proposer cannot see) -> certify on an
    untouched meta-holdout with a cleared-noise gate. Prints whether it produced
    a CERTIFIED crossing. find -> map -> get through, ruthless + honest."""
    import discover
    r = discover.pipeline()
    print(f"DISCOVER | champion {r['champ']} novelty={r['novelty']:.3f} "
          f"CERT-margin={r['margin']:+.3f} -> {r['region']}"
          + ("  CERTIFIED CROSSING (through the wall; the crossing becomes the "
             "new baseline -> the wall moves)" if r["certified"]
             else "  no certified crossing (margin under noise, or not novel)"))


# --------------------------------------------------------------- shards -----
SHARDS = HERE / "shards.jsonl"


def _shard_lines():
    if not SHARDS.is_file():
        return []
    return [json.loads(l) for l in SHARDS.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def cmd_shard(args):
    """Mint erasure-coded SHARDs of a crystal (the SPOOR SHARD type). `station
    shard <file> [k n]` splits the file into n deterministic fragments (default
    k=4 n=6); ANY k reconstitute it BYTE-EXACT, so it survives n-k losses at any
    offsets. A PIN detects loss; a SHARD repairs it. Fragments append to
    shards.jsonl. Refuses k>=n (that is a pin wearing shard costume)."""
    import base64
    import hashlib
    from shard_rs import encode
    if not args:
        print("usage: station shard <file> [k n]")
        return
    path = args[0]
    k = int(args[1]) if len(args) > 1 else 4
    n = int(args[2]) if len(args) > 2 else 6
    if k >= n:
        print(f"shard: k({k}) must be < n({n}) — k==n is a pin, not a shard")
        return
    p = Path(path)
    if not p.is_file():
        print(f"shard: no such file {path}")
        return
    data = p.read_bytes()
    pin = hashlib.sha256(data).hexdigest()[:16]
    frags, olen = encode(data, k, n)
    scheme = f"rs-gf256-k{k}-n{n}"
    existing = {(s["crystal_pin"], s["i"]) for s in _shard_lines()}
    added = 0
    with SHARDS.open("a", encoding="utf-8") as f:
        for i, fr in enumerate(frags):
            if (pin, i) in existing:
                continue
            f.write(json.dumps({
                "crystal_pin": pin, "path": str(p).replace("\\", "/"),
                "k": k, "n": n, "i": i, "scheme": scheme, "orig_len": olen,
                "frag_sha16": hashlib.sha256(fr).hexdigest()[:16],
                "frag_b64": base64.b64encode(fr).decode()}) + "\n")
            added += 1
    print(f"SHARD {scheme} pin={pin} path={p.name} fragments+={added} "
          f"(any {k}/{n} reconstitute; survives {n - k} losses)")


def cmd_recover(args):
    """Reconstitute a crystal from surviving SHARD fragments. `station recover
    <crystal_pin>` gathers fragments, decodes from any k, and rehashes:
    RECOVERED iff the decode matches the pin, BELOW-K if <k survive, MISDECODE
    if a decode's hash != pin (refused, never a silent wrong crystal)."""
    import base64
    import hashlib
    from shard_rs import decode
    if not args:
        print("usage: station recover <crystal_pin>")
        return
    pin = args[0]
    rows = [s for s in _shard_lines() if s["crystal_pin"] == pin]
    if not rows:
        print(f"recover: no shards for pin {pin}")
        return
    k, n, olen = rows[0]["k"], rows[0]["n"], rows[0]["orig_len"]
    frags = {s["i"]: base64.b64decode(s["frag_b64"]) for s in rows}
    if len(frags) < k:
        print(f"BELOW-K pin={pin}: {len(frags)}/{k} fragments survive")
        return
    rec = decode(frags, k, n, olen)
    if rec is None:
        print(f"BELOW-K pin={pin}: decode failed")
        return
    got = hashlib.sha256(rec).hexdigest()[:16]
    if got != pin:
        print(f"MISDECODE pin={pin}: decoded hash {got} != pin (refused)")
        return
    print(f"RECOVERED pin={pin} path={rows[0]['path']} bytes={olen} "
          f"from {len(frags)}/{n} fragments (needed {k})")


# ---------------------------------------------------------- glyphs ----------
GLYPHS = HERE / "glyphs.jsonl"


def _glyph_book():
    if not GLYPHS.is_file():
        return []
    return [json.loads(l) for l in GLYPHS.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _glyph_encode(text, pairs):
    import re
    out = text
    for phrase, glyph in pairs:
        out = re.sub(r"(?<![\w§])" + re.escape(phrase) + r"(?![\w])", glyph, out)
    return out


def _glyph_expand(text, book):
    out = text
    for g in book:                       # glyph -> its canonical phrase (round-trip)
        out = out.replace(g["glyph"], g["phrase"])
    return out


def cmd_glyph(args):
    """The SPOOR GLYPH codec (self-native compression). `station glyph
    encode|expand|measure [file|-]`. encode swaps canonical phrases for their
    §-glyphs (case-exact, word-bounded -> the round-trip is lossless BY
    CONSTRUCTION); expand restores the phrases; measure reports the compression
    and asserts expand(encode(x))==x. Deep teaching-expansions live in
    glyphs.jsonl 'expands'; the codec trades in the lossless 'phrase' pair."""
    import re
    if not args or args[0] not in ("encode", "expand", "measure"):
        print("usage: station glyph <encode|expand|measure> [file|-]")
        return
    mode, src = args[0], (args[1] if len(args) > 1 else "-")
    text = sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")
    book = _glyph_book()
    # only AUTO glyphs (verified token-win under real tokenizers) are applied,
    # so encoding can never COST tokens; deep-reference glyphs are manual-only
    pairs = sorted(((g["phrase"], g["glyph"]) for g in book
                    if g.get("phrase") and g.get("auto")),
                   key=lambda p: -len(p[0]))
    if mode == "encode":
        sys.stdout.write(_glyph_encode(text, pairs))
    elif mode == "expand":
        sys.stdout.write(_glyph_expand(text, book))
    else:
        enc = _glyph_encode(text, pairs)
        lossless = _glyph_expand(enc, book) == text
        wt = lambda s: len(re.findall(r"\S+", s))
        dc = len(text) - len(enc)
        print(f"GLYPH measure: chars {len(text)}->{len(enc)} "
              f"({100 * dc / max(len(text), 1):.1f}% shorter) | ws-tokens "
              f"{wt(text)}->{wt(enc)} | lossless-roundtrip={lossless} "
              f"(char/ws proxy for the true tokenizer, labeled honest)")


# ---------------------------------------------------------- burn / eras -----
BURN_LEDGER = HERE / "burn-ledger.jsonl"


def _certified_count() -> int:
    """Lifetime certified claims — DISTINCT verified ids (turn 46). The
    ledger may hold the same claim certified twice (e.g. re-run with fresh
    holdout seeds: stronger evidence, not a second capability). §15's ratio
    is only honest if its denominator counts capabilities, not rows —
    deduping makes the number worse and true, which is the whole point of
    a self-correcting record."""
    claims_path = _registry().get("claims", "")
    if not (claims_path and Path(claims_path).is_file()):
        return 0
    d = json.loads(Path(claims_path).read_text(encoding="utf-8-sig"))
    arr = d if isinstance(d, list) else d.get("claims", [])
    return len({c.get("id") for c in arr if c.get("verified") is True})


def _weighted(u: dict) -> int:
    """One weighting for all burn math (same formula as quota)."""
    return (u.get("input_tokens", 0) + u.get("output_tokens", 0) * 5
            + u.get("cache_creation_input_tokens", 0) // 4)


def _burn_days(days: set) -> dict:
    """Weighted burn per wanted UTC day, one transcript scan. Day is taken
    from each record's own timestamp prefix — no epoch/tz math to rot."""
    import calendar
    out = {d: 0 for d in days}
    lo = calendar.timegm(time.strptime(min(days), "%Y-%m-%d"))
    root = Path.home() / ".claude" / "projects"
    for f in root.rglob("*.jsonl"):
        try:
            if f.stat().st_mtime < lo:
                continue
            with f.open(encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if '"usage"' not in ln:
                        continue
                    try:
                        rec = json.loads(ln)
                    except json.JSONDecodeError:
                        continue
                    day = (rec.get("timestamp") or "")[:10]
                    if day in out:
                        out[day] += _weighted(
                            (rec.get("message") or {}).get("usage") or {})
        except OSError:
            continue
    return out


def cmd_burn():
    """The persistent cumulative burn counter (THINKING/vital-sign-metric.md
    probe 1 answer: transcripts retain ~30 days, no lifetime counter exists —
    so the station keeps its own). Appends each COMPLETED UTC day's weighted
    burn once (floor, not exact: cleaned transcripts undercount), plus a cert
    marker whenever lifetime-certified changes. Idempotent; pulse-driven."""
    import datetime as _dt
    have, last_cert = set(), None
    if BURN_LEDGER.is_file():
        for ln in BURN_LEDGER.read_text(encoding="utf-8-sig").splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r.get("kind") == "day":
                have.add(r["day"])
            elif r.get("kind") == "cert":
                last_cert = r["certified"]
    today = _now()[:10]
    t0 = _dt.date.fromisoformat(today)
    wanted = {(t0 - _dt.timedelta(days=k)).isoformat()
              for k in range(1, 29)} - have
    added = []
    if wanted:
        burns = _burn_days(wanted)
        for d in sorted(wanted):
            _append_line(BURN_LEDGER,
                         json.dumps({"kind": "day", "day": d,
                                     "burn": burns[d], "t": _now()}) + "\n")
            added.append((d, burns[d]))
    certified = _certified_count()
    if certified != last_cert:
        _append_line(BURN_LEDGER,
                     json.dumps({"kind": "cert", "certified": certified,
                                 "day": today, "t": _now()}) + "\n")
        print(f"cert-marker: certified={certified} (was {last_cert})")
    tail = " ".join(f"{d}~{b:,}" for d, b in added[-7:])
    print(f"BURN-LEDGER days={len(have) + len(added)} added={len(added)}"
          + (f" | {tail}" if tail else ""))


def cmd_seal(path_arg: str):
    """Clock-stamped ledger append. Reads ONE JSON object from stdin (BOM
    already eaten at the pipe joint), overwrites 't' with the station's own
    clock read, adds by= attribution, appends. Kills the invented-timestamp
    class: an author's typed time is a memory, not a measurement — turns
    22-24 landed up to +48min in the future in a WITNESSED ledger."""
    raw = sys.stdin.read()
    try:
        rec = json.loads(raw)
        if not isinstance(rec, dict):
            raise ValueError
    except (json.JSONDecodeError, ValueError):
        print("seal: stdin must be exactly one JSON object")
        sys.exit(1)
    typed = rec.get("t")
    rec["t"] = _now()
    rec.setdefault("by", os.environ.get("STATION_ACTOR", f"pid{os.getpid()}"))
    p = Path(path_arg)
    _append_line(p, json.dumps(rec) + "\n")
    note = (f" (typed t={typed} discarded)" if typed and typed != rec["t"]
            else "")
    print(f"sealed -> {p.name} t={rec['t']} by={rec['by']}{note}")


def _fold_eras():
    """Fold burn-ledger into (closed_eras, open_era). Pure ledger read —
    cheap enough for every wake; no transcript scans."""
    eras, cur = [], {"burn": 0, "days": 0, "start": None, "end": None}
    for ln in BURN_LEDGER.read_text(encoding="utf-8-sig").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("kind") == "day":
            cur["burn"] += r["burn"]
            cur["days"] += 1
            cur["start"] = cur["start"] or r["day"]
            cur["end"] = r["day"]
        elif r.get("kind") == "cert":
            if cur["days"]:
                eras.append({**cur, "certified": r["certified"]})
            cur = {"burn": 0, "days": 0, "start": None, "end": None}
    return eras, cur


def cmd_eras():
    """SS15 in decidable form: cumulative metered burn per certification era.
    An era = the days between cert markers. Sickness signature = the open
    era's burn rising past every closed era with no cert in sight; a cert
    ratchets the counter. Reads burn-ledger; open era adds today's partial
    live. Day-granular (pulse appends daily) — boundaries are honest +-1d."""
    if not BURN_LEDGER.is_file():
        print("(no burn ledger; run station burn first)")
        return
    eras, cur = _fold_eras()
    today = _now()[:10]
    live = _burn_days({today})[today]
    for i, e in enumerate(eras):
        print(f"era {i} {e['start']}..{e['end']} days={e['days']} "
              f"burn~{e['burn']:,} -> cert #{e['certified']}")
    print(f"era {len(eras)} OPEN {cur['start'] or today}.. days={cur['days']}"
          f" burn~{cur['burn'] + live:,} (incl today-partial ~{live:,})")
    if eras:
        worst = max(e["burn"] for e in eras)
        state = "OK" if cur["burn"] + live <= worst else "RISING-PAST-WORST"
        print(f"verdict: open-era vs worst-closed({worst:,}): {state}")


# ----------------------------------------------------------------- map ------
def cmd_map(path: str):
    """Outline of a file so Reads become surgical offsets, never whole
    files. .py -> AST (def/class per line); .md/.markdown -> heading tree
    (spiral turn 1: the architecture ledger alone is 300+ lines and every
    era reads it — an outline costs ~20)."""
    p = Path(path)
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    if p.suffix.lower() in (".md", ".markdown"):
        print(f"map {path} {len(lines)}L")
        fence = False
        for i, ln in enumerate(lines, 1):
            if ln.lstrip().startswith("```"):
                fence = not fence
            if not fence and ln.startswith("#"):
                level = len(ln) - len(ln.lstrip("#"))
                print(f"  L{i:<5d} {'  ' * (level - 1)}{ln.strip('# ')[:70]}")
        return
    import ast
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        print(f"(unmappable: {e})")
        sys.exit(1)
    print(f"map {path} {len(lines)}L")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = ", ".join(a.arg for a in node.args.args)
            print(f"  L{node.lineno:<5d} def {node.name}({args})")
        elif isinstance(node, ast.ClassDef):
            print(f"  L{node.lineno:<5d} class {node.name}")


# ----------------------------------------------------------------- log ------
def cmd_log(name: str, tail: int | None = None, full: bool = False):
    reg = _registry()
    path = reg.get("logs", {}).get(name)
    if not path:
        print(f"unknown log {name}; known: {', '.join(reg.get('logs', {}))}")
        sys.exit(1)
    p, cur = _resolve_log(name, path)
    if p is None or not p.is_file():
        print(f"(missing: {path})")
        return
    data = p.read_bytes()
    if tail is not None:
        text = data.decode("utf-8", errors="replace")
        print("\n".join(text.splitlines()[-tail:]))
        return
    if full:
        print(data.decode("utf-8", errors="replace"))
        return
    CURSORS.mkdir(exist_ok=True)
    seen = _read_cursor(cur)
    if seen > len(data):                        # log was truncated/rotated
        seen = 0
    new = data[seen:]
    _write_cursor(cur, len(data))
    print(new.decode("utf-8", errors="replace") if new
          else f"(no new bytes; {len(data)}B total, cursor current)")


# --------------------------------------------------------------- spine ------
def cmd_note(text: str):
    _spine_append("note", text)
    print(f"noted @{_now()}")
    # adoption pressure, never a gate (notes are legal narrative): numbers
    # in prose rot; numbers with routes don't. Nudge fires at the exact
    # moment of the errata's dominant failure class — claim-write time.
    if re.search(r"\d+ */ *\d+|= *\d|\d+%|x\d+", text):
        print("  [nudge] this note carries figures — if any is load-bearing,"
              " `station say` gives it a route (quotes rot)")


# ---------------------------------------------------- provable speech ------
def _run_check(cmd: str, expect: str):
    """Execute a claim's re-derivation route through _run — the estate's one
    audited shell seam (see its trust-domain note; routes are agent-authored
    and land witnessed in the spine, never from user/network input). ok =
    expect-fragment in output, or exit 0 when no expect is given. A vacuous
    route is possible but visible forever in the record."""
    code, out = _run(cmd, str(HERE), timeout=300)
    return ((expect in out) if expect else (code == 0)), code, out.strip()


def cmd_say(args_: list):
    """Provable speech — SPOOR FACT, spoken into the spine (spiral turn 9).
    A claim enters the record WITH the command that re-derives it, and the
    command RUNS at write time: passing -> spine kind 'fact'; failing -> the
    claim lands as kind 'refuted' (exit 1) — the false version never enters
    as fact, and the refutation is itself record (§9, the record that
    corrects itself). Point-in-time sibling of drift assertions
    (invariants). Ends the partial-read-claim class structurally: numbers
    stop traveling as prose; kin re-derive with `station recheck` instead
    of quoting.

      station say "<claim>" --cmd "<command>" [--expect "<fragment>"]
      station recheck [n]     re-run the last n spine facts' routes
    """
    if "--cmd" not in args_:
        print('usage: station say "<claim>" --cmd "<command>" '
              '[--expect "<fragment>"]')
        sys.exit(1)
    i = args_.index("--cmd")
    claim = " ".join(args_[:i])
    rest = args_[i + 1:]
    if "--expect" in rest:
        j = rest.index("--expect")
        cmd, expect = " ".join(rest[:j]), " ".join(rest[j + 1:])
    else:
        cmd, expect = " ".join(rest), ""
    if cmd == "-":
        # the joint crossed as bytes, never quotes (turn 2's law): a route
        # piped via stdin dodges PS5.1 native-arg quote-stripping entirely
        cmd = sys.stdin.read().strip()
    if not claim or not cmd:
        print("(say needs both a claim and a --cmd route)")
        sys.exit(1)
    ok, code, out = _run_check(cmd, expect)
    _spine_append("fact" if ok else "refuted",
                  {"claim": claim, "cmd": cmd, "expect": expect,
                   "exit": code, "ok": ok, "out": out[-400:]})
    if ok:
        print(f"[fact] {claim}\n  route: {cmd}"
              + (f" ~ contains {expect!r}" if expect else " (exit 0)"))
    else:
        print(f"[REFUTED AT WRITE] {claim}\n  route: {cmd}\n"
              f"  expect: {expect!r}\n  got: ...{out[-200:]}")
        sys.exit(1)


def _walk_facts(n: int = 8):
    """Re-derive the last n LIVE spine facts by executing their routes.
    Skipped: retired facts (moment-facts — they expire, not stale) and
    SUPERSEDED facts (turn 41: a newer fact on the SAME route is the
    current claim about that observable; without this, every autonomic
    speaker's history became a permanent STALE alarm on every change).
    Returns [(event, ok, fresh_out)] — shared by recheck and handoff."""
    if not SPINE.is_file():
        return []
    facts, retired = [], set()
    for ln in SPINE.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        if '"kind": "fact"' in ln:
            facts.append(json.loads(ln))
        elif '"kind": "retired"' in ln:
            retired.update(json.loads(ln)["body"].get("claims", []))
    by_route = {}                          # newest fact per route wins
    for i, f in enumerate(facts):
        if f["body"]["claim"] not in retired:
            by_route[f["body"]["cmd"]] = (i, f)
    live = [f for _, f in sorted(by_route.values())][-n:]
    walked = []
    for f in live:
        ok, _, out = _run_check(f["body"]["cmd"], f["body"].get("expect", ""))
        walked.append((f, ok, out))
    return walked


def cmd_retire(match: str):
    """Retire moment-facts from the autonomic walk. Append-only: the fact
    stays witnessed in the record; a 'retired' event just removes it from
    future re-derivation. Without this, a fact like 'HEAD is c6ed974 (turn
    9 seal)' — true of a MOMENT — alarms as STALE forever the day the world
    legitimately moves on."""
    if not match.strip():
        print('usage: station retire "<claim fragment>"')
        sys.exit(1)
    if not SPINE.is_file():
        print("(spine empty)")
        return
    hits = []
    for ln in SPINE.read_text(encoding="utf-8").splitlines():
        if ln.strip() and '"kind": "fact"' in ln:
            c = json.loads(ln)["body"]["claim"]
            if match.lower() in c.lower() and c not in hits:
                hits.append(c)
    if not hits:
        print(f"no live facts match {match!r}")
        sys.exit(1)
    _spine_append("retired", {"claims": hits, "match": match})
    for c in hits:
        print(f"retired: {c[:90]}")


def cmd_recheck(n: int = 5):
    """Walk the track again: re-run the routes of the last n spine facts.
    A fact was true at its timestamp; STALE means the world moved — which is
    exactly what quoting would have missed. Quote nothing; re-derive."""
    walked = _walk_facts(n)
    if not walked:
        print("(no spine facts to recheck — nothing has been said in SPOOR)")
        return
    stale = 0
    stale_claims = []
    for f, ok, out in walked:
        stale += (not ok)
        print(f"{'ok   ' if ok else 'STALE'} [{f['t']}] {f['body']['claim'][:90]}")
        if not ok:
            stale_claims.append(f["body"]["claim"][:60])
            print(f"      true-at-write; now: ...{out[-160:]}")
    if stale:
        # the alarm joins the record (autonomic recheck runs unattended —
        # a printed STALE nobody reads is not an alarm). Deduped against
        # the last stale event so a persisting stale fact is news once,
        # not 8x/day filler.
        last = None
        for ln in SPINE.read_text(encoding="utf-8").splitlines():
            if '"kind": "stale"' in ln:
                last = json.loads(ln)["body"].get("claims")
        if last != stale_claims:
            _spine_append("stale", {"n": stale, "claims": stale_claims})
        sys.exit(1)


def cmd_spine(n: int = 10, match: str = ""):
    """Last n events; with match, last n events CONTAINING it (spiral turn
    4: unfiltered tails drowned a PULSE note among newer chatter -> false
    flatline diagnosis + 3-call debug, 2026-07-04)."""
    if not SPINE.is_file():
        print("spine empty")
        return
    lines = SPINE.read_text(encoding="utf-8").splitlines()
    if match:
        lines = [ln for ln in lines if match.lower() in ln.lower()]
    for ln in lines[-n:]:
        print(ln)


def cmd_regs():
    print(REG.read_text(encoding="utf-8"))


# ------------------------------------------------------------- organs ------
_ORGAN_PATH_RE = re.compile(r"[A-Za-z]:[\\/][\w\\/.\-]+")


def _organ_refs(built: str, verbs: set[str]) -> tuple[list[str], list[str]]:
    """Checkable references in a turn's built-prose: absolute estate paths
    (existence) and `station <verb>` mentions (still dispatchable). Prose
    that names nothing checkable yields ([], []) — that is a fact about the
    entry, not a failure."""
    ok, missing = [], []
    for raw in _ORGAN_PATH_RE.findall(built):
        p = raw.replace("\\", "/").rstrip(".,;:)\"'/")
        if not p or len(p) < 4:
            continue
        (ok if Path(p).exists() else missing).append(p)
    # Verb mentions confirm positively only: `station <word>` in prose is a
    # ref iff <word> is dispatchable today ("the station now/itself/suite"
    # flagged 4/4 false MISSING at birth — prose is not an invocation).
    # Renamed-verb rot is the semantic audit's job, not this regex's.
    for v in re.findall(r"\bstation ([a-z]+)\b", built):
        if v in verbs:
            ok.append(f"station:{v}")
    return ok, missing


def cmd_organs(args_: list[str], path: Path | None = None):
    """Capstone map (spiral turn 51): the spiral ledger read as a living
    organ registry instead of write-only memory. One line per turn with its
    artifact refs existence-checked (MISSING = rot or unrecorded
    retirement), kill conditions and open items surfaced. Default prints
    the actionable subset; --all every organ; --kill the falsifier corpus
    (audit feed); --open parked items. Exit 1 on any MISSING ref."""
    p = path or SPIRAL
    if not p.is_file():
        print("(no spiral ledger)")
        sys.exit(1)
    mode = ("all" if "--all" in args_ else "kill" if "--kill" in args_
            else "open" if "--open" in args_ else "act")
    src = Path(__file__).read_text(encoding="utf-8")
    verbs = set(re.findall(r'\bcmd == "(\w+)"', src)) | {"wake"}
    entries = [json.loads(ln) for ln in
               p.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    # append-only closure: a later entry may carry closes=[{turn,match}];
    # an open item is live unless some closure's match is a substring of it
    closures = [c for e in entries for c in (e.get("closes") or [])]
    verd: dict[str, int] = {}
    closed_n = 0
    turns, ok_n, miss_n, kills, opens, lines = [], 0, 0, 0, [], []
    for e in entries:
        t, tgt = e.get("turn", "?"), e.get("target", "-")
        v = e.get("verdict", "-")
        verd[v] = verd.get(v, 0) + 1
        if isinstance(t, int):
            turns.append(t)
        ok, missing = _organ_refs(str(e.get("built", "")), verbs)
        ok_n += len(ok)
        miss_n += len(missing)
        if e.get("kill"):
            kills += 1
        if e.get("open"):
            txt = str(e["open"])
            if any(c.get("turn") == t and c.get("match") and
                   str(c["match"]) in txt for c in closures):
                closed_n += 1
            else:
                opens.append((t, txt))
        if mode == "kill":
            if e.get("kill"):
                lines.append(f"T{t} {tgt} {v} | {e['kill']}")
            continue
        if mode == "open":
            continue
        flag = f" MISSING:{','.join(missing)}" if missing else ""
        row = (f"T{t:<3} {tgt:<10} {v:<7} refs={len(ok)}/{len(ok) + len(missing)}"
               f"{flag} | {str(e.get('built', ''))[:70]}")
        if mode == "all" or missing:
            lines.append(row)
    lo_hi = f"{min(turns)}-{max(turns)}" if turns else "?"
    vs = " ".join(f"{k}={n}" for k, n in sorted(verd.items()))
    print(f"ORGANS entries={len(entries)} turns={lo_hi} | {vs} | "
          f"refs ok={ok_n} MISSING={miss_n} | kill={kills} "
          f"open={len(opens)} closed={closed_n}")
    for ln in lines:
        print(ln)
    if mode in ("act", "open"):
        for t, o in opens:
            print(f"T{t} OPEN | {o}")
    sys.exit(1 if miss_n and mode in ("act", "all") else 0)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "wake":
        cmd_wake()
    elif cmd == "suites":
        force = "--force" in args
        rest = [a for a in args[1:] if not a.startswith("-")]
        cmd_suites(rest[0] if rest else None, force=force)
    elif cmd == "tally":
        cmd_tally(args[1], args[3] if len(args) > 3 and args[2] == "--by"
                  else (args[2].split("=", 1)[1] if len(args) > 2
                        and args[2].startswith("--by=") else
                        (args[2] if len(args) > 2 else None)))
    elif cmd == "map":
        cmd_map(args[1])
    elif cmd == "quota":
        cmd_quota(float(args[1]) if len(args) > 1 else 5.0)
    elif cmd == "vitals":
        cmd_vitals(float(args[1]) if len(args) > 1 else 24.0)
    elif cmd == "burn":
        cmd_burn()
    elif cmd == "eras":
        cmd_eras()
    elif cmd == "conversions":
        cmd_conversions()
    elif cmd == "moat":
        cmd_moat()
    elif cmd == "wall":
        cmd_wall(args[1:])
    elif cmd == "discover":
        cmd_discover()
    elif cmd == "shard":
        cmd_shard(args[1:])
    elif cmd == "recover":
        cmd_recover(args[1:])
    elif cmd == "glyph":
        cmd_glyph(args[1:])
    elif cmd == "organs":
        cmd_organs(args[1:])
    elif cmd == "seal":
        if len(args) < 2:
            print("usage: station seal <ledger.jsonl>   (JSON object via stdin)")
            sys.exit(1)
        cmd_seal(args[1])
    elif cmd == "handoff":
        cmd_handoff(" ".join(args[1:]))
    elif cmd == "molt":
        cmd_molt(" ".join(args[1:]))
    elif cmd == "will":
        cmd_will(" ".join(args[1:]))
    elif cmd == "hand":
        cmd_hand(args[1:])
    elif cmd == "wsl":
        rest = args[1:]
        u = rest[0] if len(rest) == 2 else ""
        cmd_wsl(u, rest[-1] if rest else "-")
    elif cmd == "llm":
        if len(args) < 2:
            print('usage: station llm [model] "<prompt>"|-   (- = stdin)')
            sys.exit(1)
        if len(args) == 2:
            cmd_llm("qwen2.5-coder:7b", args[1])
        else:
            cmd_llm(args[1], " ".join(args[2:]))
    elif cmd == "cure":
        cmd_cure(" ".join(args[1:]))
    elif cmd == "errata":
        cmd_errata(args[1:])
    elif cmd == "pin":
        cmd_pin(args[1])
    elif cmd == "drift":
        cmd_drift()
    elif cmd == "witness":
        cmd_witness()
    elif cmd == "backup":
        cmd_backup()
    elif cmd == "preregs":
        cmd_preregs(args[1:])
    elif cmd == "market":
        cmd_market(args[1:])
    elif cmd == "immune":
        cmd_immune(args[1:])
    elif cmd == "forecast":
        cmd_forecast(args[1:])
    elif cmd == "lease":
        cmd_lease(args[1:])
    elif cmd == "rescue":
        if len(args) < 2:
            print("usage: station rescue <repo>")
            sys.exit(1)
        cmd_rescue(args[1])
    elif cmd == "log":
        if len(args) < 2 or args[1].startswith("-"):
            print("usage: station log <name> [--tail N | --full]")
            sys.exit(1)
        tail = None
        if "--tail" in args:
            try:
                tail = int(args[args.index("--tail") + 1])
            except (IndexError, ValueError):
                print("usage: station log <name> [--tail N | --full]")
                sys.exit(1)
        cmd_log(args[1], tail=tail, full="--full" in args)
    elif cmd == "note":
        cmd_note(" ".join(args[1:]))
    elif cmd == "say":
        cmd_say(args[1:])
    elif cmd == "recheck":
        cmd_recheck(int(args[1]) if len(args) > 1 else 5)
    elif cmd == "retire":
        cmd_retire(" ".join(args[1:]))
    elif cmd == "spine":
        cmd_spine(int(args[1]) if len(args) > 1 else 10,
                  args[2] if len(args) > 2 else "")
    elif cmd == "regs":
        cmd_regs()
    else:
        print(f"unknown command {cmd}\n{__doc__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
