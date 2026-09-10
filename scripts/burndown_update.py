#!/usr/bin/env python3
"""Append today's data to the burndown JSON. Updates if today exists."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from loaders import KOJI_PY315, parse_pyver_nvr

DATA_FILES = {
    "succeeded": "data/python315-45.pkgs",
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
    except FileNotFoundError:
        return None
    return parse_pyver_nvr(nvr, KOJI_PY315).replace("~", "")


def main():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    try:
        entries = json.loads(Path(OUTPUT).read_text())
    except FileNotFoundError:
        entries = []

    entry = {
        "date": today,
        "timestamp": now.isoformat(),
        "python_version": parse_pyver(),
    }
    for key, filepath in DATA_FILES.items():
        entry[key] = count_lines(filepath)

    if entries and entries[-1]["date"] == today:
        entries[-1] = entry
        action = "Updated"
    else:
        entries.append(entry)
        action = "Appended"

    with open(OUTPUT, "w") as f:
        json.dump(entries, f, indent=2)

    print(f"{action} entry for {today} to {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
