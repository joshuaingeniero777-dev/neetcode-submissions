"""Builds tracker/tracker.csv and the progress section of README.md.

Runs automatically from .github/workflows/update-tracker.yml every time
NeetCode pushes a new submission (and once a day so "Due" dates stay current).
You can also run it locally from the repo root:  python tracker/build_tracker.py
"""

import csv
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DSA_DIR = ROOT / "Data Structures & Algorithms"
PROBLEMS = json.loads((ROOT / "tracker" / "problems.json").read_text())
CSV_PATH = ROOT / "tracker" / "tracker.csv"
README = ROOT / "README.md"
REPO = os.environ.get("GITHUB_REPOSITORY", "joshuaingeniero777-dev/neetcode-submissions")

# Spaced repetition: after your Nth separate day solving a problem,
# wait this many days before solving it again from scratch.
REVIEW_GAPS = [3, 7, 14, 30]
MASTERED_AFTER = 5  # separate solve days

CATEGORY_ORDER = []
for meta in PROBLEMS.values():
    if meta["category"] not in CATEGORY_ORDER:
        CATEGORY_ORDER.append(meta["category"])

# Optional notes line anywhere in your NeetCode code, e.g.
#   # help: Y | insight: hashmap of complements
#   // help: N | insight: two pointers from both ends
NOTE_RE = re.compile(r"^\s*(?:#|//|--)\s*help\s*:\s*([YyNn])\w*\s*(?:\|\s*insight\s*:\s*(.*))?$",
                     re.IGNORECASE | re.MULTILINE)
SUB_RE = re.compile(r"^submission-(\d+)\.(\w+)$")
LANGS = {"py": "Python", "js": "JavaScript", "ts": "TypeScript", "java": "Java", "cpp": "C++",
         "cs": "C#", "go": "Go", "rs": "Rust", "kt": "Kotlin", "swift": "Swift", "sql": "SQL"}


def today():
    return datetime.now().date()  # workflow sets TZ=America/New_York


def file_dates():
    """Map each file path to the date git first saw it (when NeetCode pushed it)."""
    out = subprocess.run(
        ["git", "-c", "core.quotePath=false", "log", "--diff-filter=A", "--reverse", "--name-only", "--format=@@%cI"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    dates, current = {}, None
    for line in out.splitlines():
        if line.startswith("@@"):
            current = datetime.fromisoformat(line[2:]).astimezone().date()
        elif line.strip() and current:
            dates.setdefault(line.strip().strip('"'), current)
    return dates


def collect():
    dates = file_dates()
    subs = defaultdict(list)
    if DSA_DIR.exists():
        for f in DSA_DIR.glob("*/submission-*.*"):
            m = SUB_RE.match(f.name)
            if not m:
                continue
            rel = f.relative_to(ROOT).as_posix()
            d = dates.get(rel) or date.fromtimestamp(f.stat().st_mtime)
            subs[f.parent.name].append({"n": int(m.group(1)), "ext": m.group(2), "date": d, "path": f})
    return subs


def summarize(slug, entries, now):
    meta = PROBLEMS.get(slug, {"num": "", "name": slug.replace("-", " ").title(),
                                "category": "Other", "difficulty": ""})
    row = {"#": meta["num"], "Problem": meta["name"], "Category": meta["category"],
           "Difficulty": meta["difficulty"], "Status": "Not Started", "First Solved": "",
           "Last Solved": "", "Solve Days": 0, "Submissions": 0, "Next Re-solve": "",
           "Needed Help": "", "Key Insight": "", "Language": "",
           "NeetCode Link": f"https://neetcode.io/problems/{slug}", "Solution": ""}
    if not entries:
        return row
    entries.sort(key=lambda e: (e["date"], e["n"]))
    days = sorted({e["date"] for e in entries})
    latest = entries[-1]
    gap = REVIEW_GAPS[min(len(days), len(REVIEW_GAPS)) - 1]
    nxt = days[-1] + timedelta(days=gap)
    help_flag, insight = "", ""
    for e in reversed(entries):  # newest note wins
        m = NOTE_RE.search(e["path"].read_text(errors="ignore"))
        if m:
            help_flag = "Y" if m.group(1).upper() == "Y" else "N"
            insight = (m.group(2) or "").strip()
            break
    if len(days) >= MASTERED_AFTER and nxt > now:
        status = "Mastered"
    elif nxt < now:
        status = "Overdue"
    elif nxt == now:
        status = "Due Today"
    else:
        status = "Scheduled"
    rel = latest["path"].relative_to(ROOT).as_posix().replace(" ", "%20").replace("&", "%26")
    row.update({"Status": status, "First Solved": days[0].isoformat(),
                "Last Solved": days[-1].isoformat(), "Solve Days": len(days),
                "Submissions": len(entries), "Next Re-solve": nxt.isoformat(),
                "Needed Help": help_flag, "Key Insight": insight,
                "Language": ", ".join(sorted({LANGS.get(e["ext"], e["ext"]) for e in entries})),
                "Solution": f"https://github.com/{REPO}/blob/main/{rel}"})
    return row


def build_rows():
    now = today()
    subs = collect()
    rows = [summarize(slug, subs.get(slug, []), now) for slug in PROBLEMS]
    rows += [summarize(slug, subs[slug], now) for slug in sorted(subs) if slug not in PROBLEMS]
    return rows, now


def write_csv(rows):
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def bar(done, total, width=10):
    filled = round(width * done / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def readme_section(rows, now):
    nc = [r for r in rows if r["Category"] != "Other"]
    solved = [r for r in nc if r["Status"] != "Not Started"]
    lines = ["## 📊 NeetCode 150 Progress", "",
             f"**{len(solved)} / 150 solved** `{bar(len(solved), 150, 20)}`  ",
             f"_Auto-updated {now.isoformat()} · full tracker: [tracker/tracker.csv](tracker/tracker.csv)_", ""]
    by_diff = defaultdict(lambda: [0, 0])
    for r in nc:
        by_diff[r["Difficulty"]][1] += 1
        by_diff[r["Difficulty"]][0] += r["Status"] != "Not Started"
    lines.append(" · ".join(f"{d}: **{by_diff[d][0]}/{by_diff[d][1]}**" for d in ("Easy", "Medium", "Hard")))
    lines += ["", "| Category | Solved | Progress |", "|---|---|---|"]
    for cat in CATEGORY_ORDER:
        cr = [r for r in nc if r["Category"] == cat]
        done = sum(r["Status"] != "Not Started" for r in cr)
        lines.append(f"| {cat} | {done}/{len(cr)} | `{bar(done, len(cr))}` |")
    due = sorted((r for r in rows if r["Status"] in ("Overdue", "Due Today")), key=lambda r: r["Next Re-solve"])
    lines += ["", "### 🔁 Due for a re-solve", ""]
    if due:
        lines += ["| Problem | Category | Last solved | Due |", "|---|---|---|---|"]
        lines += [f"| [{r['Problem']}]({r['NeetCode Link']}) | {r['Category']} | {r['Last Solved']} | {r['Next Re-solve']} |"
                  for r in due]
    else:
        lines.append("Nothing due. Nice work!")
    recent = sorted((r for r in rows if r["Last Solved"]), key=lambda r: r["Last Solved"], reverse=True)[:5]
    if recent:
        lines += ["", "### 🕒 Recently solved", "", "| Problem | Difficulty | Solved | Next re-solve |", "|---|---|---|---|"]
        lines += [f"| [{r['Problem']}]({r['Solution']}) | {r['Difficulty']} | {r['Last Solved']} | {r['Next Re-solve']} |"
                  for r in recent]
    return "\n".join(lines)


START, END = "<!-- TRACKER:START -->", "<!-- TRACKER:END -->"


def write_readme(section):
    text = README.read_text(encoding="utf-8") if README.exists() else ""
    block = f"{START}\n{section}\n{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    else:
        text = block + "\n\n---\n\n" + text
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    rows, now = build_rows()
    write_csv(rows)
    write_readme(readme_section(rows, now))
    print(f"Tracker updated: {sum(r['Status'] != 'Not Started' for r in rows)} problems solved")
