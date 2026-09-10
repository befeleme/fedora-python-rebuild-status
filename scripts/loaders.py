import json

# set to True after the mass-rebuild to use Koji as the source for data
# otherwise Copr will be used (90% of the time)
KOJI_PY315 = True


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


def parse_pyver_nvr(nvr, koji_enabled):
    "Return just the version string from a Python src package NVR"
    if koji_enabled:
        # Koji src rpm name, e.g. python3.15-3.15.0~rc1-1.fc45.src.rpm
        return nvr.removesuffix(".src.rpm").rsplit("-", 2)[1]
    # Copr src rpm name, e.g. python3.15-0:3.15.0~rc1-9.fc46.src
    return nvr.split(":")[-1].split("-")[0]


def load_python_version(file_suffix, koji_enabled):
    "Return just the version string from data/pyver_py<file_suffix>"
    full_pkgname = load_data(f"data/pyver_py{file_suffix}").pop()
    return parse_pyver_nvr(full_pkgname, koji_enabled)