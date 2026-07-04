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
  station note <text...>    append a telegraph event to the spine
  station spine [N]         last N spine events (default 10)
  station will [intent|done]  testament: intent-at-death, rewritten at every
                            move boundary (interrupts are not graceful)
  station hand "<task>"|take|status   the hatch: feed the jailed always-on
                            hermes-agent (local model, $0); stigmergic —
                            drop food, walk away, collect later
  station llm [model] "<p>"|-  one free local-inference call
  station regs              show the registry (repos, suites, logs)
"""
from __future__ import annotations

import hashlib
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

HERE = Path(__file__).resolve().parent
REG = HERE / "station.json"
SPINE = HERE / "spine.jsonl"
CURSORS = HERE / "cursors"
WILL = HERE / "WILL.md"
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


def _spine_append(kind: str, body):
    SPINE.parent.mkdir(exist_ok=True)
    with SPINE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": _now(), "kind": kind, "body": body}) + "\n")


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
    return f"{name} {head}{mark}{unt}"


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

    cert = sum(1 for c in claims if state(c) == "CERTIFIED")
    rej = sum(1 for c in claims if state(c) == "REJECTED")
    pend = sum(1 for c in claims if state(c) == "PENDING")
    last = claims[-1] if claims else {}
    return (f"claims {cert}certified {rej}rejected {pend}pending | last: "
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


def _log_freshness(reg: dict) -> list[str]:
    out = []
    for name, path in reg.get("logs", {}).items():
        p = Path(path)
        if not p.is_file():
            continue
        age_min = (time.time() - p.stat().st_mtime) / 60
        seen = _read_cursor(CURSORS / f"{name}.offset")
        unread = p.stat().st_size - seen
        if unread > 0 or age_min < 120:
            out.append(f"log {name} {p.stat().st_size}B "
                       f"age={age_min:.0f}m unread={max(unread, 0)}B"
                       f" -> station log {name}")
    return out


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
        (CURSORS / "witness.json", dest / "station" / "witness.json"),
        (Path("E:/atlas-station/CLAIMS.json"), dest / "atlas" / "CLAIMS.json"),
        (Path("E:/mission-runs/results.jsonl"), dest / "boundary" / "results.jsonl"),
        (Path("E:/mission-runs/w2_results.jsonl"), dest / "boundary" / "w2_results.jsonl"),
    ]
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
    code, _ = _run(f'git commit -q -m "continuity backup {_now()}"', str(dest))
    pushed = ""
    rc, _ = _run("git remote get-url origin", str(dest))
    if rc == 0:
        pc, _ = _run("git push -q", str(dest))
        pushed = " pushed" if pc == 0 else " PUSH-FAILED"
    print(f"[backup] {copied} sources -> {dest} "
          f"{'committed' if code == 0 else '(no changes)'}{pushed}")
    _spine_append("backup", {"sources": copied})


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
            with (HERE / "llm-ledger.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"t": _now(), "model": model,
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
    claims_path = _registry().get("claims", "")
    certified = 0
    if claims_path and Path(claims_path).is_file():
        d = json.loads(Path(claims_path).read_text(encoding="utf-8-sig"))
        arr = d if isinstance(d, list) else d.get("claims", [])
        certified = sum(1 for c in arr if c.get("verified") is True)
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


# ----------------------------------------------------------------- map ------
def cmd_map(path: str):
    """AST outline of a python file: one line per def/class with its line
    number — so Reads become surgical offsets, never whole files."""
    import ast
    p = Path(path)
    try:
        tree = ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))
    except (OSError, SyntaxError) as e:
        print(f"(unmappable: {e})")
        sys.exit(1)
    n_lines = len(p.read_text(encoding="utf-8-sig", errors="replace")
                  .splitlines())
    print(f"map {path} {n_lines}L")
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
    p = Path(path)
    if not p.is_file():
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
    cur = CURSORS / f"{name}.offset"
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


def cmd_spine(n: int = 10):
    if not SPINE.is_file():
        print("spine empty")
        return
    for ln in SPINE.read_text(encoding="utf-8").splitlines()[-n:]:
        print(ln)


def cmd_regs():
    print(REG.read_text(encoding="utf-8"))


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
    elif cmd == "handoff":
        cmd_handoff(" ".join(args[1:]))
    elif cmd == "will":
        cmd_will(" ".join(args[1:]))
    elif cmd == "hand":
        cmd_hand(args[1:])
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
    elif cmd == "pin":
        cmd_pin(args[1])
    elif cmd == "drift":
        cmd_drift()
    elif cmd == "witness":
        cmd_witness()
    elif cmd == "backup":
        cmd_backup()
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
    elif cmd == "spine":
        cmd_spine(int(args[1]) if len(args) > 1 else 10)
    elif cmd == "regs":
        cmd_regs()
    else:
        print(f"unknown command {cmd}\n{__doc__}")
        sys.exit(1)


if __name__ == "__main__":
    main()
