import json
import bugzilla

from loaders import load_data, load_monitor_report, KOJI_PY315, KOJI_PY315B1


BUGZILLA = 'bugzilla.redhat.com'
BZ_PAGE_SIZE = 20

# Python version configurations
VERSION_CONFIG = {
    "3.15": {
        "tracker": 2412434,  # PYTHON3.15
        "rawhide": [2384424, 2433833],  # F44FTBFS, F45FTBFS
        "failed_file": "data/failed_py315.pkgs",
        "waiting_file": "data/waiting_py315.pkgs",
        "python_pkgs": "data/python315.pkgs",
        "copr_file": "data/copr_py315.pkgs",
        "output_file": "data/bzurls_py315.json"
    },
    "3.15-b1": {
        "tracker": 2412434,  # PYTHON3.15
        "rawhide": [2384424, 2433833],  # F44FTBFS, F45FTBFS
        "failed_file": "data/failed_py315-b1.pkgs",
        "waiting_file": "data/waiting_py315-b1.pkgs",
        "python_pkgs": "data/python315-b1.pkgs",
        "copr_file": "data/copr_py315-b1.pkgs",
        "output_file": "data/bzurls_py315-b1.json"
    }
}

BZAPI = bugzilla.Bugzilla(BUGZILLA)


def load_failed_packages(version="3.15"):
    """Load failed packages for a specific Python version."""

    koji = KOJI_PY315 if version == "3.15" else KOJI_PY315B1

    config = VERSION_CONFIG[version]

    FAILED = load_data(config["failed_file"])
    if koji:
        WAITING = load_data(config["waiting_file"])
        FAILED.update(WAITING)
    # we only want to do Copr magic before the mass rebuild
    else:
        HISTORICALLY_SUCCESSFUL = load_data(config["python_pkgs"])
        ALL_IN_COPR = load_monitor_report(config["copr_file"])

        # Attempt to find bugzillas for packages that
        # started to fail to build just recently
        FAILED.update(pkg for pkg in HISTORICALLY_SUCCESSFUL if ALL_IN_COPR.get(pkg) == "failed")

    return sorted(FAILED)


def bugzillas(sorted_fails, tracker, rawhide):
    """Query Bugzilla for open bugs blocking the tracker or rawhide."""
    query = BZAPI.build_query(product='Fedora')

    # Only add trackers that are not None
    blocks = []
    if tracker:
        blocks.append(tracker)
    if rawhide:
        blocks.extend(rawhide)

    if not blocks:
        # If no trackers, return empty list
        return []

    query['blocks'] = blocks
    query['limit'] = BZ_PAGE_SIZE
    query['offset'] = 0
    results = []
    while len(partial := BZAPI.query(query)) == BZ_PAGE_SIZE:
        results += partial
        query['offset'] += BZ_PAGE_SIZE
    results += partial
    return [b for b in sorted(results, key=lambda b: -b.id)
            if b.is_open and b.component in sorted_fails]


def map_pkgs_and_bzurls(bugzillas_list, sorted_fails):
    """Map packages to their Bugzilla URLs and summaries."""
    pkgs_urls = {pkg: {"urls": [], "summaries": []} for pkg in sorted_fails}
    for bug in bugzillas_list:
        if bug.component not in pkgs_urls:
            continue
        pkgs_urls[bug.component]["urls"].append(bug.weburl)
        pkgs_urls[bug.component]["summaries"].append(bug.summary)
    return pkgs_urls


if __name__ == "__main__":
    sorted_fails_315 = load_failed_packages("3.15")
    sorted_fails_315b1 = load_failed_packages("3.15-b1")

    # Union both package sets so a single BZ query covers both versions
    all_fails = sorted(set(sorted_fails_315) | set(sorted_fails_315b1))

    config_315 = VERSION_CONFIG["3.15"]
    bugzillas_list = bugzillas(all_fails, config_315["tracker"], config_315["rawhide"])

    for version, sorted_fails in [("3.15", sorted_fails_315), ("3.15-b1", sorted_fails_315b1)]:
        config = VERSION_CONFIG[version]
        pkg_url_mapping = map_pkgs_and_bzurls(bugzillas_list, sorted_fails)
        with open(config["output_file"], 'w') as open_file:
            json.dump(pkg_url_mapping, open_file, indent=2)
        print(f"Bugzilla URLs for Python {version} written to {config['output_file']}")
