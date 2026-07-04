"""Drift check: every probe check name in every wave-2 task maps to a
correctness area (the self-report instrument's totality dependency)."""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, "E:/boundary/mission1")
from scorer import load_task_config, _probe_area  # noqa: E402


class _Stub:
    def __getattr__(self, n):
        return lambda *a, **k: None


bad = []
for td in ("task_t2", "task_t3", "task_t4"):
    base = Path("E:/boundary/mission1/tasks") / td
    cfg = load_task_config(base)
    names = []
    for pf in sorted((base / "probes").glob("probe_*.py")):
        spec = importlib.util.spec_from_file_location(pf.stem, pf)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        try:
            names += [n for n, _ in m.run(_Stub())]
        except Exception:
            names.append("CRASH:" + pf.stem)
    bad += [f"{td}:{n}" for n in names
            if _probe_area(n, cfg["areas"]) is None]

print("CHECK-OK" if not bad else "UNMAPPED:" + str(bad[:5]))
