import json


def load_data(filename):
    with open(filename, "r", encoding="utf=8") as f:
        return {row.strip() for row in f.readlines()}


def load_json(filename):
    with open(filename, "r", encoding="utf=8") as f:
        return json.load(f)


def load_monitor_report(filename):
    monitor = {}
    with open(filename, "r", encoding="utf=8") as f:
        for line in f:
            pkgname, state = line.strip().split("\t")
            monitor[pkgname] = state
    return monitor