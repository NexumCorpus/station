"""Drift check: the WSL anchor + hatch must persist — without the anchor,
WSL idles out and kills the hand mid-task (paid 2026-07-04)."""
import os
import pathlib

s = pathlib.Path(os.path.expandvars(
    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
    r"\WSL-Anchor.lnk")).is_file()
h = pathlib.Path(r"\\wsl$\Ubuntu\hatch\in").is_dir()
print("OK" if s and h else f"BROKEN shortcut={s} hatch={h}")
