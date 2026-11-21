"""Print progress for the LAMS backlog checklist files (docs/backlog/M*.md).

Usage, from the repo root:  python scripts/backlog/progress.py
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BACKLOG = Path(__file__).resolve().parents[2] / "docs" / "backlog"
ITEM = re.compile(r"^- \[( |x|X)\] (~~)?\*\*(LAMS-\d{4})\*\*")

grand_done = grand_total = 0
in_progress = []
for path in sorted(BACKLOG.glob("M*.md")):
    done = total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ITEM.match(line)
        if not m:
            continue
        total += 1
        if m.group(1).lower() == "x":
            done += 1
        elif "(in progress)" in line:
            in_progress.append(f"{m.group(3)} ({path.stem[:3]})")
    grand_done += done
    grand_total += total
    pct = round(100 * done / total) if total else 0
    bar = "#" * (pct // 10) + "." * (10 - pct // 10)
    print(f"{path.stem:<35} [{bar}] {done:>2}/{total:<2} {pct:>3}%")

pct = round(100 * grand_done / grand_total) if grand_total else 0
print(f"\n{'Overall':<35} {grand_done}/{grand_total} items, {pct}%")
print("In progress: " + (", ".join(in_progress) if in_progress else "none"))
