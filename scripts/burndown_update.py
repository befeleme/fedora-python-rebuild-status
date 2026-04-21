#!/usr/bin/env python3
"""Append today's data to the burndown JSON. Idempotent — skips if today exists."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA_FILES = {
    "succeeded": "data/python315.pkgs",
    "failed": "data/failed_py315.pkgs",
    "waiting": "data/waiting_py315.pkgs",
}
PYVER_FILE = "data/pyver_py315"
OUTPUT = "data/burndown_py315.json"


def count_lines(filepath):
    try:
        content = Path(filepath).read_text()
        return len([line for line in content.splitlines() if line.strip()])
    except FileNotFoundError:
        return 0


def parse_pyver():
    try:
        nvr = Path(PYVER_FILE).read_text().strip()
        match = re.search(r":(.+?)-\d+\.", nvr)
        if match:
            return match.group(1).replace("~", "")
        return nvr
    except FileNotFoundError:
        return None


def main():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    try:
        entries = json.loads(Path(OUTPUT).read_text())
    except FileNotFoundError:
        entries = []

    if entries and entries[-1]["date"] == today:
        print(f"Entry for {today} already exists, skipping", file=sys.stderr)
        return

    entry = {
        "date": today,
        "timestamp": now.isoformat(),
        "python_version": parse_pyver(),
    }
    for key, filepath in DATA_FILES.items():
        entry[key] = count_lines(filepath)

    entries.append(entry)

    with open(OUTPUT, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"Appended entry for {today} to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
