"""Create GitHub labels, milestones and issues from docs/WORK_PLAN.md.

Usage (from the repo root, after `gh auth login`):
    python scripts/github/create_backlog.py            # create everything
    python scripts/github/create_backlog.py --dry-run  # print what would be created

Safe to re-run: existing labels, milestones and issues (matched by title) are skipped.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs" / "WORK_PLAN.md"
DRY = "--dry-run" in sys.argv
sys.stdout.reconfigure(encoding="utf-8")

LABELS = {
    # area
    "data-model": "1d76db", "config": "5319e7", "security": "b60205", "apex": "0e8a16",
    "flow": "fbca04", "lwc": "0052cc", "vf-aura": "c5def5", "integration": "d93f0b",
    "portal": "006b75", "ai": "8a2be2", "reporting": "bfd4f2", "devops": "555555", "docs": "cccccc",
    # type
    "feature": "a2eeef", "bug": "d73a4a", "test": "e4e669", "chore": "ededed", "parking-lot": "f9d0c4",
    # size
    "S": "c2e0c6", "M": "fef2c0", "L": "f9c0c0",
}

MILESTONE_AREA = {
    "M01": "devops", "M02": "data-model", "M03": "config", "M04": "security", "M05": "data-model",
    "M06": "apex", "M07": "flow", "M08": "apex", "M09": "integration", "M10": "portal",
    "M11": "reporting", "M12": "ai", "M13": "docs",
}

FIXED_AREA = {"M01", "M02", "M03", "M04", "M05", "M10", "M11", "M12", "M13"}

KEYWORDS = [  # (case-sensitive regex on the item title, extra label)
    (r"\bLWCs?\b", "lwc"),
    (r"\b(?:sub)?[Ff]low\b|[Oo]rchestration|[Aa]pproval process|[Ee]mail templates", "flow"),
    (r"(?<!Customer )Service\b|Batch|Trigger|Api\b|WebService|Controller|class\b|invocables|Publisher|Logger|[Rr]outer|Queueable", "apex"),
    (r"PDF|Aura|Letter", "vf-aura"),
    (r"Credential|[Mm]ock|Postman|Integration User|External Client", "integration"),
]


def gh(*args, capture=True):
    cmd = ["gh", *args]
    res =subprocess.run(cmd, capture_output=capture, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{res.stderr}")
    return res.stdout


def parse_plan():
    text = PLAN.read_text(encoding="utf-8")
    backlog = text.split("## 4. Backlog", 1)[1].split("## 5.", 1)[0]
    milestones = []
    for block in re.split(r"\n(?=### M\d\d)", backlog):
        head = re.match(r"### (M\d\d) – (.+?)(?: \(≈ (\d+)h\))?\s*$", block.splitlines()[0])
        if not head:
            continue
        code, name, hours = head.groups()
        exit_m = re.search(r"\*\*Exit:\*\*\s*(.+)", block)
        dep_m = re.search(r"Depends on:\s*(.+)", block)
        items = []
        for row in re.findall(r"^\| (LAMS-\d{4}) \| (.+?) \| (S|M|L) \| (.+?) \|$", block, re.M):
            items.append(dict(zip(("id", "title", "size", "delivers"), row)))
        milestones.append(dict(code=code, name=name, hours=hours, exit=exit_m.group(1).strip() if exit_m else "",
                               depends=dep_m.group(1).strip() if dep_m else "", items=items))
    return milestones


def labels_for(ms_code, item):
    is_test = item["title"].startswith("Negative tests")
    labels = {item["size"], "test" if is_test else "feature"}
    if ms_code in FIXED_AREA:
        labels.add(MILESTONE_AREA[ms_code])
    if ms_code != "M01":
        for pattern, label in KEYWORDS:
            if re.search(pattern, item["title"]):
                labels.add(label)
    areas = set(MILESTONE_AREA.values()) | {"lwc", "flow", "apex", "vf-aura", "integration"}
    if not labels & areas:
        labels.add(MILESTONE_AREA[ms_code])
    return sorted(labels)


def body_for(ms, item):
    short = item["id"].split("-")[1]
    dep = ms["depends"] if short in ms["depends"] else ""
    lines = [
        f"**Milestone:** {ms['code']} – {ms['name']}",
        f"**Delivers:** {item['delivers']} (see `docs/LAMS_BRD_v2.md`)",
        f"**Size:** {item['size']}",
    ]
    if dep:
        lines.append(f"**Dependencies (milestone note):** {dep}")
    if ms["exit"]:
        lines.append(f"**Milestone exit:** {ms['exit']}")
    lines += [
        "",
        "## Done when",
        "",
        "- [ ] Metadata in source control and deploys cleanly",
        "- [ ] Apex tests in the same PR (≥ 90%, bulk 200, toggle on/off) — if Apex is involved",
        "- [ ] No hardcoded IDs, endpoints, thresholds or user-facing text",
        "- [ ] CI green",
        "- [ ] BRD updated if the design changed",
        "- [ ] Screenshot/GIF on the PR if visible",
    ]
    return "\n".join(lines)


def main():
    milestones = parse_plan()
    total = sum(len(m["items"]) for m in milestones)
    print(f"Parsed {len(milestones)} milestones, {total} work items")
    if DRY:
        for ms in milestones:
            print(f"\n{ms['code']} – {ms['name']} ({len(ms['items'])} items)")
            for it in ms["items"]:
                print(f"  {it['id']}: {it['title']}  {labels_for(ms['code'], it)}")
        return

    repo = json.loads(gh("repo", "view", "--json", "nameWithOwner"))["nameWithOwner"]
    print(f"Repo: {repo}")

    existing_labels = {l["name"] for l in json.loads(gh("label", "list", "--limit", "200", "--json", "name"))}
    for name, color in LABELS.items():
        if name not in existing_labels:
            gh("label", "create", name, "--color", color)
            print(f"label + {name}")

    existing_ms = {m["title"] for m in json.loads(gh("api", f"repos/{repo}/milestones?state=all&per_page=100"))}
    for ms in milestones:
        title = f"{ms['code']} – {ms['name']}"
        if title not in existing_ms:
            desc = f"≈ {ms['hours']}h. Exit: {ms['exit']}" if ms["exit"] else f"≈ {ms['hours']}h."
            gh("api", "--method", "POST", f"repos/{repo}/milestones", "-f", f"title={title}", "-f", f"description={desc}")
            print(f"milestone + {title}")

    existing_issues = {i["title"] for i in json.loads(gh("issue", "list", "--state", "all", "--limit", "500", "--json", "title"))}
    for ms in milestones:
        ms_title = f"{ms['code']} – {ms['name']}"
        for it in ms["items"]:
            title = f"{it['id']}: {it['title']}"
            if title in existing_issues:
                continue
            args = ["issue", "create", "--title", title, "--body", body_for(ms, it), "--milestone", ms_title]
            for label in labels_for(ms["code"], it):
                args += ["--label", label]
            url = gh(*args).strip()
            print(f"issue + {title}  {url}")


if __name__ == "__main__":
    main()
