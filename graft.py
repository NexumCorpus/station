"""Xenograft primitives (spiral 122): prove a small artifact survives transplant.

The manifest is intentionally narrow and command-free. It carries only a local
source root, hash-pinned file mappings, and the relative Python check to execute
in a fresh temporary body. This is portability evidence, not a security sandbox.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED = ("id", "source_root", "files", "check")
FILE_REQUIRED = ("source", "dest", "sha256")
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}$")
SHA256 = re.compile(r"[0-9a-f]{64}$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel(value: str, label: str) -> Path:
    path = Path(str(value))
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"{label} must be a non-empty relative path")
    return path


def load(path: Path) -> dict:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"manifest unreadable: {exc}") from exc
    validate(manifest)
    return manifest


def validate(manifest: dict):
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    missing = [key for key in REQUIRED if manifest.get(key) in (None, "")]
    if missing:
        raise ValueError("manifest missing " + ", ".join(missing))
    if not ID.fullmatch(str(manifest["id"])):
        raise ValueError("id must be 3-64 lowercase letters, digits, or hyphens")
    root = Path(str(manifest["source_root"]))
    if not root.is_dir():
        raise ValueError("source_root must be an existing local directory")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        raise ValueError("files must be a non-empty list")
    destinations = set()
    for item in manifest["files"]:
        if not isinstance(item, dict) or set(item) != set(FILE_REQUIRED):
            raise ValueError("every file mapping must have exactly source, dest, sha256")
        source, dest = _rel(item["source"], "source"), _rel(item["dest"], "dest")
        if dest.as_posix() in destinations:
            raise ValueError("duplicate destination: " + dest.as_posix())
        destinations.add(dest.as_posix())
        if not (root / source).is_file():
            raise ValueError("missing source: " + source.as_posix())
        if not isinstance(item["sha256"], str) or not SHA256.fullmatch(item["sha256"]):
            raise ValueError("sha256 must be a 64-character lowercase hex digest")
    check = _rel(manifest["check"], "check")
    if check.as_posix() not in destinations:
        raise ValueError("check must be one of the transplanted destinations")


def verify_sources(manifest: dict) -> list[str]:
    """Return every stale/missing source edge before any byte enters a graft."""
    root = Path(manifest["source_root"])
    problems = []
    for item in manifest["files"]:
        source = root / item["source"]
        if not source.is_file():
            problems.append(f"missing:{item['source']}")
        elif sha256(source.read_bytes()) != item["sha256"]:
            problems.append(f"stale:{item['source']}")
    return problems


def run(manifest_path: Path, timeout_s: int = 30) -> dict:
    """Copy exactly the manifest bytes to an empty body and run its fixed check."""
    manifest = load(manifest_path)
    problems = verify_sources(manifest)
    if problems:
        return {"id": manifest["id"], "status": "GRAFT-ROT", "problems": problems}
    root = Path(manifest["source_root"])
    with tempfile.TemporaryDirectory(prefix="station-graft-") as tmp_s:
        tmp = Path(tmp_s)
        for item in manifest["files"]:
            src, dst = root / item["source"], tmp / item["dest"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            if sha256(dst.read_bytes()) != item["sha256"]:
                return {"id": manifest["id"], "status": "GRAFT-ROT",
                        "problems": [f"copy-hash:{item['dest']}"]}
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        try:
            proc = subprocess.run([sys.executable, "-E", "-s", manifest["check"]],
                                  cwd=str(tmp), env=env, text=True,
                                  capture_output=True, timeout=timeout_s)
            output = ((proc.stdout or "") + (proc.stderr or "")).strip()
            return {"id": manifest["id"],
                    "status": "GRAFT-OK" if proc.returncode == 0 else "GRAFT-FAIL",
                    "exit": proc.returncode, "tail": output[-500:],
                    "files": len(manifest["files"])}
        except subprocess.TimeoutExpired:
            return {"id": manifest["id"], "status": "GRAFT-FAIL", "exit": -124,
                    "tail": f"timeout after {timeout_s}s", "files": len(manifest["files"])}
