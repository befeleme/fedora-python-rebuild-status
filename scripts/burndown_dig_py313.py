#!/usr/bin/env python3
"""One-shot git archaeology for Python 3.13 rebuild data."""

import json
import re
import subprocess
import sys

START_COMMIT = "e4af4d83aec66f215ffc602623ea1a44a6fa0ef7"
END_COMMIT = "b2ddd4a70934f0433f03957025e13bb6a8464150"

OUTPUT = "data/burndown_py313.json"


def git(*args):
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True
    )
    return result.stdout, result.returncode


def get_commits():
    out, _ = git(
        "log", "--format=%H %aI %s",
        "--reverse",
        f"{START_COMMIT}~1..{END_COMMIT}~1",
        "--grep=Latest data:",
    )
    commits = []
    for line in out.strip().splitlines():
        parts = line.split(" ", 2)
        if len(parts) < 3:
            continue
        sha, iso_date, subject = parts
        if "Latest data:" not in subject:
            continue
        commits.append((sha, iso_date))
    return commits


def count_lines(sha, filepath):
    content, rc = git("show", f"{sha}:{filepath}")
    if rc != 0:
        return None
    return len([line for line in content.splitlines() if line.strip()])


def parse_pyver(sha):
    content, rc = git("show", f"{sha}:templates/index.html")
    if rc != 0:
        return "3.13.0a1"
    match = re.search(r"Python (3\.13\S*)\s*\(Target", content)
    if match:
        ver = match.group(1).replace("~", "")
        return ver
    return "3.13.0a1"


def main():
    commits = get_commits()
    print(f"Found {len(commits)} commits to process", file=sys.stderr)

    entries = []
    for i, (sha, iso_date) in enumerate(commits, 1):
        date_str = iso_date[:10]

        succeeded = count_lines(sha, "data/python313.pkgs") or 0
        waiting = count_lines(sha, "data/waiting.pkgs") or 0
        failed_count = count_lines(sha, "data/failed.pkgs")
        if failed_count is None:
            todo = count_lines(sha, "data/todo.pkgs") or 0
            failed_count = todo - waiting

        entry = {
            "date": date_str,
            "timestamp": iso_date,
            "python_version": parse_pyver(sha),
            "succeeded": succeeded,
            "failed": failed_count,
            "waiting": waiting,
        }
        entries.append(entry)
        if i % 40 == 0:
            print(f"  processed {i}/{len(commits)}", file=sys.stderr)

    # Deduplicate: keep last entry per day
    by_date = {}
    for entry in entries:
        by_date[entry["date"]] = entry
    deduped = sorted(by_date.values(), key=lambda e: e["timestamp"])

    with open(OUTPUT, "w") as f:
        json.dump(deduped, f, indent=2)

    print(f"Wrote {len(deduped)} entries ({len(entries)} before dedup) to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
