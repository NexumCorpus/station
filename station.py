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
  station regs              show the registry (repos, suites, logs)
"""
from __future__ import annotations

import json
import os
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
    lines = [f"STATION WAKE {_now()}"]
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
    print("\n".join(lines))
    _spine_append("wake", {"repos": len(reg.get("repos", {}))})


# -------------------------------------------------------------- suites ------
def cmd_suites(only: str | None = None):
    reg = _registry()
    suites = reg.get("suites", [])
    if only:
        suites = [s for s in suites if s["name"] == only]
        if not suites:                          # a typo must NEVER read as PASS
            known = ", ".join(s["name"] for s in reg.get("suites", []))
            print(f"unknown suite {only}; known: {known}")
            sys.exit(1)
    results = {}
    for s in suites:
        t0 = time.time()
        code, out = _run(s["cmd"], s["cwd"], timeout=SUITE_TIMEOUT_S)
        tail = out.strip().splitlines()[-1][:120] if out.strip() else ""
        verdict = "PASS" if code == 0 else "FAIL"
        results[s["name"]] = verdict
        print(f"suite {s['name']:12s} {verdict} {time.time()-t0:5.1f}s "
              f"[{s['cwd']}] | {tail}")
    _spine_append("suites", results)
    sys.exit(0 if results and all(v == "PASS" for v in results.values()) else 1)


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
        cmd_suites(args[1] if len(args) > 1 else None)
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
