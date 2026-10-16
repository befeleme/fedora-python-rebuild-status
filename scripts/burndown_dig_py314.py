#!/usr/bin/env python3
"""One-shot git archaeology for Python 3.14 rebuild data."""

import json
import re
import subprocess
import sys

START_COMMIT = "b2ddd4a70934f0433f03957025e13bb6a8464150"
END_COMMIT = "1b08a13ba602a848b28bb11fd3417e969088861e"

DATA_FILES = {
    "succeeded": "data/python314.pkgs",
    "failed": "data/failed.pkgs",
    "waiting": "data/waiting.pkgs",
}
PYVER_FILE = "data/pyver"

OUTPUT = "data/burndown_py314.json"


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
        match = re.search(r"Latest data: (.+)", subject)
        if not match:
            continue
        commits.append((sha, iso_date))
    return commits


def count_lines(sha, filepath):
    content, rc = git("show", f"{sha}:{filepath}")
    if rc != 0:
        return 0
    return len([line for line in content.splitlines() if line.strip()])


def parse_pyver(sha):
    content, rc = git("show", f"{sha}:{PYVER_FILE}")
    if rc != 0:
        return "3.14.0a1"
    nvr = content.strip()
    match = re.search(r":(.+?)-\d+\.", nvr)
    if match:
        return match.group(1).replace("~", "")
    return nvr


def main():
    commits = get_commits()
    print(f"Found {len(commits)} commits to process", file=sys.stderr)

    entries = []
    for i, (sha, iso_date) in enumerate(commits, 1):
        date_str = iso_date[:10]
        entry = {
            "date": date_str,
            "timestamp": iso_date,
            "python_version": parse_pyver(sha),
        }
        for key, filepath in DATA_FILES.items():
            entry[key] = count_lines(sha, filepath)

        entries.append(entry)
        if i % 40 == 0:
            print(f"  processed {i}/{len(commits)}", file=sys.stderr)

    with open(OUTPUT, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"Wrote {len(entries)} entries to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
