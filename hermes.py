"""hermes — the messenger: free recursive reading for the estate.

The RLM result (arXiv:2512.24601, findings: research/rlm.md) made section 12
of ALIEN-ARCHITECTURE.md buildable: a small LOCAL model, given a fixed
map-reduce loop instead of an open REPL (the paper's own evidence: untrained
small models fail as free-form roots but work as directed workers), can read
files far beyond any context window; local Ollama can be free, while a family
CLI backend is account-metered according to its provider.

What this buys the estate: transcript archaeology, log digestion, ledger
questions — the exact class of work that cost ~10 metered calls at this
session's start — become free and unbounded in input size.

Loop (fixed, per rlm.md for 7B-class workers):
  1. GREP-FIRST: optional regex prefilter shrinks the corpus losslessly.
  2. CHUNK: newline-aligned ~28KB pieces (~7K tok, fits worker's 16K ctx
     with room for the question + answer).
  3. MAP: one worker call per chunk -> partial notes (relevant facts only,
     or the exact token NOTHING).
  4. REDUCE: concatenate partials; if they still exceed one chunk, recurse
     on the notes (depth wall 3). Final call synthesizes the answer.
  Budget: 64 worker calls per question, hard.

Honesty contract: hermes is a READER, not an oracle. Its answer carries
counts (calls, depth, chunks, bytes) and is advisory — anything load-bearing
gets verified against the primary bytes before entering a record. If the
local model is down, hermes says DOWN; it never silently degrades.

Usage:
  python hermes.py ask <file> "<question>" [--grep REGEX]
  python hermes.py ask - "<question>"          (corpus from stdin)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from station import llm, llm_up                            # noqa: E402

# Hermes is a schema/reading specialist; coding models stay assigned to build
# routes. Override only when a local operator has deliberately installed a
# different reader model.
BACKEND = os.environ.get("HERMES_BACKEND", "codex-cli").strip().lower()
# Hermes reads default to a family agent through the authenticated Codex CLI.
# Ollama remains an explicit fallback (`HERMES_BACKEND=ollama`), never silent.
MODEL = os.environ.get("HERMES_MODEL", "gpt-5.6-luna")
CHUNK_BYTES = 28_000          # ~7K tokens: worker keeps headroom in 16K ctx
NUM_CTX = 16_384              # ollama default 4-8K silently truncates (rlm.md)
MAX_CALLS = 64
MAX_DEPTH = 3

MAP_SYS = ("You extract facts. Given a QUESTION and a text PIECE, output "
           "ONLY facts from the piece relevant to the question, one per "
           "line, verbatim numbers/names/paths preserved. When the text "
           "shows speakers/roles (user, assistant, log source), PREFIX each "
           "fact with [who]. Never merge different speakers into one fact. "
           "If nothing is relevant output exactly: NOTHING")
REDUCE_SYS = ("You synthesize. Given a QUESTION and NOTES extracted from a "
              "large document, answer the question directly and concisely. "
              "Keep [who] attributions — never ascribe one speaker's words "
              "to another. State plainly what the notes do not establish. "
              "Never invent facts absent from the notes.")


def _codex_binary() -> str | None:
    """Resolve the installed family CLI without reading or manufacturing keys."""
    explicit = os.environ.get("ATLAS_CODEX_BIN")
    if explicit and Path(explicit).is_file():
        return explicit
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "OpenAI" / "Codex" / "bin"
    if root.is_dir():
        for version in sorted((p for p in root.iterdir() if p.is_dir()), reverse=True):
            candidate = version / ("codex.exe" if os.name == "nt" else "codex")
            if candidate.is_file():
                return str(candidate)
    found = shutil.which("codex.exe") or shutil.which("codex")
    if found:
        return found
    return None


def _codex_read(prompt: str, system: str, timeout: int) -> str | None:
    binary = _codex_binary()
    if not binary:
        return None
    prepared = ("You are Hermes, a bounded extractive reader.\n"
                "Return only the requested answer; do not edit files, call tools, "
                "or claim facts absent from the supplied text.\n\n"
                f"READER RULES:\n{system}\n\n{prompt}")
    args = [binary, "exec", "--json", "--color", "never", "--ignore-user-config",
            "--model", MODEL, "-C", str(HERE), "-s", "read-only", prepared]
    try:
        proc = subprocess.run(args, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    answer = ""
    for line in (proc.stdout or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            answer = str(item["text"])
        if event.get("type") in ("turn.failed", "error"):
            return None
    return answer.strip() or None


def _reader_call(prompt: str, system: str, num_ctx: int = NUM_CTX,
                 timeout: int = 900) -> str | None:
    if BACKEND == "codex-cli":
        return _codex_read(prompt, system, timeout)
    if BACKEND == "ollama":
        return llm(prompt, model=MODEL, system=system, num_ctx=num_ctx,
                   timeout=timeout)
    return None


def _backend_up() -> bool:
    if BACKEND == "codex-cli":
        return _codex_binary() is not None
    if BACKEND == "ollama":
        return llm_up()
    return False


def _read_any(path: Path) -> str:
    """Encoding-sniffing read: PowerShell redirects write UTF-16LE, and a
    UTF-8 read of UTF-16 feeds the model NUL-riddled garbage it (honestly)
    extracts nothing from — the first live hermes test failed exactly this
    way. BOM first, then NUL-density heuristic."""
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig", errors="replace")
    if raw and raw[:2000].count(0) > len(raw[:2000]) // 4:
        return raw.decode("utf-16-le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def _chunks(text: str, size: int = CHUNK_BYTES):
    """Newline-aligned pieces <= size bytes (a fact is never cut mid-line)."""
    out, buf, n = [], [], 0
    for line in text.splitlines(keepends=True):
        if n + len(line) > size and buf:
            out.append("".join(buf))
            buf, n = [], 0
        buf.append(line)
        n += len(line)
    if buf:
        out.append("".join(buf))
    return out


def ask(corpus: str, question: str, grep: str | None = None) -> dict:
    """Fixed map-reduce read. Returns {answer|error, calls, depth, chunks,
    bytes_read} — counts are part of the answer, not decoration."""
    if not _backend_up():
        return {"error": f"DOWN: Hermes backend unavailable ({BACKEND})", "calls": 0}
    raw_bytes = len(corpus)
    if grep:
        kept = [ln for ln in corpus.splitlines()
                if re.search(grep, ln, re.IGNORECASE)]
        corpus = "\n".join(kept)
        if not corpus:
            return {"answer": f"grep '{grep}' matched nothing",
                    "calls": 0, "depth": 0, "chunks": 0,
                    "bytes_read": raw_bytes}
    calls = 0
    depth = 0
    notes = corpus
    total_chunks = 0
    if len(corpus) <= CHUNK_BYTES:
        # fits whole: answer directly off the raw bytes — a map stage here
        # would only launder context through a lossy extract for no reason
        r = _reader_call(f"QUESTION: {question}\n\nDOCUMENT:\n{corpus}", REDUCE_SYS)
        if r is None:
            return {"error": "DOWN at direct read", "calls": 1}
        return {"answer": r.strip(), "calls": 1, "depth": 0, "chunks": 1,
                "bytes_read": raw_bytes}
    while depth < MAX_DEPTH:
        pieces = _chunks(notes)
        total_chunks += len(pieces)
        if len(pieces) == 1 and depth > 0:
            break                          # notes fit; go synthesize
        partials = []
        for p in pieces:
            if calls >= MAX_CALLS:
                partials.append("[BUDGET EXHAUSTED — remainder unread]")
                break
            r = _reader_call(f"QUESTION: {question}\n\nPIECE:\n{p}", MAP_SYS)
            calls += 1
            if r is None:
                return {"error": f"DOWN mid-read after {calls} calls",
                        "calls": calls}
            if r.strip() and r.strip() != "NOTHING":
                partials.append(r.strip())
        notes = "\n".join(partials) if partials else "NOTHING RELEVANT FOUND"
        depth += 1
        if len(notes) <= CHUNK_BYTES:
            break
    r = _reader_call(f"QUESTION: {question}\n\nNOTES:\n{notes[:CHUNK_BYTES]}", REDUCE_SYS)
    calls += 1
    if r is None:
        return {"error": f"DOWN at synthesis after {calls} calls",
                "calls": calls}
    return {"answer": r.strip(), "calls": calls, "depth": depth,
            "chunks": total_chunks, "bytes_read": raw_bytes}


DIGEST_MODEL = "hermes3:8b"       # schema-tuned (research/hermes-local.md);
                                  # falls back to MODEL if not pulled
DIGESTS = HERE / "digests"
NIGHT_CURSORS = HERE / "cursors"  # night_<log> files — SEPARATE namespace:
                                  # the wake's unread signal is never stolen
DIGEST_SYS = ("You digest machine logs. Output EXACTLY this schema, nothing "
              "else:\nFACTS: 3-8 lines, one extractive fact each, verbatim "
              "numbers/ids preserved\nANOMALY: one line per irregularity, "
              "or the exact token NONE\nMANDATORY: any line containing an "
              "error code (4xx/5xx), 'error', 'failed', 'timeout', 'limit', "
              "'wall', or an exception IS an anomaly — list it even if also "
              "listed as a fact. Never interpret, never advise, never "
              "invent.")


def digest():
    """Night job (pulse-run, free): pre-digest NEW bytes of registered logs
    into digests/YYYYMMDD.md. Sleep-compute evidence (research/
    sleep-compute.md): extractive+schema-bound is the only 7-8B-safe job;
    digests are CANDIDATES — raw bytes stay on disk, wake cursors untouched,
    anything load-bearing is re-verified at the source."""
    import time as _t
    reg = json.loads((HERE / "station.json").read_text(encoding="utf-8-sig"))
    model = MODEL
    out_lines, done = [], 0
    for name, path in reg.get("logs", {}).items():
        if done >= 2:                      # bound the beat
            break
        p = Path(path)
        if not p.is_file():
            continue
        cur = NIGHT_CURSORS / f"night_{name}.offset"
        seen = int(cur.read_text()) if cur.is_file() else 0
        size = p.stat().st_size
        if size <= seen or size - seen < 200:
            continue
        raw = p.read_bytes()[seen:]
        text = raw.decode("utf-16", "replace") if raw[:2000].count(0) \
            > len(raw[:2000]) // 4 else raw.decode("utf-8", "replace")
        r = _reader_call(f"LOG {name} (new bytes {seen}-{size}):\n{text[:CHUNK_BYTES]}", DIGEST_SYS)
        if r is None:
            print("[digest] model DOWN — nothing consumed")
            return
        out_lines.append(f"## {name} bytes {seen}-{size} "
                         f"@{_t.strftime('%H:%M:%SZ', _t.gmtime())}\n{r.strip()}\n")
        cur.parent.mkdir(exist_ok=True)
        cur.write_text(str(size))
        done += 1
    if out_lines:
        DIGESTS.mkdir(exist_ok=True)
        day = DIGESTS / f"{_t.strftime('%Y%m%d', _t.gmtime())}.md"
        with day.open("a", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
        print(f"[digest] {done} log(s) -> {day.name} (advisory; raw bytes "
              f"remain the record)")
    else:
        print("[digest] nothing new to digest")


def _has_model(tag: str) -> bool:
    import subprocess
    try:
        r = subprocess.run(["wsl", "-d", "Ubuntu", "--", "curl", "-s",
                            "--max-time", "8",
                            "http://localhost:11434/api/tags"],
                           capture_output=True, text=True, timeout=30)
        return tag.split(":")[0] in (r.stdout or "")
    except Exception:
        return False


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "digest":
        digest()
        return
    if len(sys.argv) < 4 or sys.argv[1] != "ask":
        print(__doc__)
        sys.exit(1)
    src, question = sys.argv[2], sys.argv[3]
    grep = None
    if "--grep" in sys.argv:
        grep = sys.argv[sys.argv.index("--grep") + 1]
    corpus = sys.stdin.read() if src == "-" else _read_any(Path(src))
    res = ask(corpus, question, grep=grep)
    if "error" in res:
        print(f"[hermes] {res['error']}")
        sys.exit(2)
    print(res["answer"])
    cost = "$0 local" if BACKEND == "ollama" else "account-metered/unknown"
    print(f"\n[hermes] backend={BACKEND} model={MODEL} calls={res['calls']} depth={res['depth']} "
          f"chunks={res['chunks']} bytes={res['bytes_read']:,} cost={cost}")
    print("[hermes] SCOPE: substance advisory, ATTRIBUTION UNRELIABLE — the "
          "the model may be wrong. Verify load-bearing facts at source.")


if __name__ == "__main__":
    main()
