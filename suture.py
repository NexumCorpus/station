"""Context-suture primitives (spiral 129): lossless context without replay.

A suture preserves exact declared byte intervals in an immutable payload.  It is
not a summary, a prompt, or executable authority: source bytes can be re-read
from the pack, while a later verify distinguishes intact payload from a donor
that has moved on.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path


ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}$")
REQUIRED = ("id", "purpose", "slices")
SLICE_REQUIRED = ("source", "start", "end", "dest")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(path: Path, roots: list[Path]) -> bool:
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return False
    return any(resolved.is_relative_to(root.resolve()) for root in roots)


def _dest(value: str) -> Path:
    path = Path(str(value))
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError("dest must be a non-empty relative path")
    return path


def validate_manifest(manifest: dict, roots: list[Path]):
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    missing = [key for key in REQUIRED if manifest.get(key) in (None, "")]
    if missing:
        raise ValueError("manifest missing " + ", ".join(missing))
    if not ID.fullmatch(str(manifest["id"])):
        raise ValueError("id must be 3-64 lowercase letters, digits, or hyphens")
    if not isinstance(manifest["purpose"], str) or len(manifest["purpose"]) > 240:
        raise ValueError("purpose must be 1-240 characters")
    slices = manifest["slices"]
    if not isinstance(slices, list) or not slices:
        raise ValueError("slices must be a non-empty list")
    dests = set()
    for item in slices:
        if not isinstance(item, dict) or set(item) != set(SLICE_REQUIRED):
            raise ValueError("every slice has exactly source,start,end,dest")
        source = Path(str(item["source"]))
        if not source.is_absolute() or not source.is_file() or not _inside(source, roots):
            raise ValueError("source must be an existing file inside a registered repo")
        start, end = item["start"], item["end"]
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
            raise ValueError("slice offsets must be non-negative and end > start")
        if end > source.stat().st_size:
            raise ValueError("slice ends after source bytes")
        dest = _dest(item["dest"]).as_posix()
        if dest in dests:
            raise ValueError("duplicate destination: " + dest)
        dests.add(dest)


def seal(manifest: dict, roots: list[Path], now: str) -> dict:
    """Make a self-contained, exact payload. Caller persists it only under a
    new id; this function never touches the donor or the filesystem."""
    validate_manifest(manifest, roots)
    slices = []
    for item in manifest["slices"]:
        source = Path(item["source"]).resolve()
        raw = source.read_bytes()
        chunk = raw[item["start"]:item["end"]]
        slices.append({
            "source": str(source).replace("\\", "/"), "start": item["start"],
            "end": item["end"], "dest": _dest(item["dest"]).as_posix(),
            "source_sha256": sha256(raw), "slice_sha256": sha256(chunk),
            "b64": base64.b64encode(chunk).decode("ascii"),
        })
    return {
        "kind": "context-suture", "id": manifest["id"], "purpose": manifest["purpose"],
        "t": now, "executor": "deterministic byte slicer",
        "authority": "none: passive context payload; not executable authority",
        "slices": slices,
    }


def verify(pack: dict) -> dict:
    """Check payload integrity first, then whether the donor still has exactly
    those bytes at the declared interval.  Payload drift is worse than donor
    drift: stale context can still be honestly used as historical context."""
    if not isinstance(pack, dict) or pack.get("kind") != "context-suture":
        return {"status": "SUTURE-ROT", "problems": ["invalid pack kind"]}
    rows = pack.get("slices")
    if not ID.fullmatch(str(pack.get("id", ""))) or not isinstance(rows, list) or not rows:
        return {"status": "SUTURE-ROT", "problems": ["invalid pack shape"]}
    problems, donor_drift, total = [], [], 0
    for item in rows:
        try:
            data = base64.b64decode(item["b64"].encode("ascii"), validate=True)
            if sha256(data) != item["slice_sha256"]:
                problems.append(item.get("dest", "?") + ":payload-hash")
                continue
            source = Path(item["source"])
            raw = source.read_bytes()
            if sha256(raw) != item["source_sha256"] or raw[item["start"]:item["end"]] != data:
                donor_drift.append(item.get("dest", "?"))
            total += len(data)
        except (KeyError, OSError, TypeError, ValueError, base64.binascii.Error):
            problems.append(str(item.get("dest", "?")) + ":unreadable")
    if problems:
        return {"status": "SUTURE-ROT", "problems": problems, "bytes": total}
    return {"status": "SUTURE-SOURCE-DRIFT" if donor_drift else "SUTURE-OK",
            "problems": donor_drift, "bytes": total, "slices": len(rows)}


def render(pack: dict, result: dict) -> str:
    return (f"{result['status']} {pack.get('id', '?')} slices={result.get('slices', 0)} "
            f"bytes={result.get('bytes', 0)}"
            + (" | " + "; ".join(result["problems"]) if result.get("problems") else ""))
