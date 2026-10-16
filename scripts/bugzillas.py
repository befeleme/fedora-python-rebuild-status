import json
import bugzilla

from loaders import load_data, load_monitor_report, KOJI_PY316


BUGZILLA = 'bugzilla.redhat.com'
BZ_PAGE_SIZE = 20

# Python version configurations
VERSION_CONFIG = {
    "3.16": {
        "tracker": None,  # PYTHON3.16 tracker does not exist yet
        "rawhide": [],  # F47FTBFS etc. - add once the trackers are filed
        "failed_file": "data/failed_py316.pkgs",
        "waiting_file": "data/waiting_py316.pkgs",
        "python_pkgs": "data/python316.pkgs",
        "copr_file": "data/copr_py316.pkgs",
        "output_file": "data/bzurls_py316.json"
    },
}

BZAPI = bugzilla.Bugzilla(BUGZILLA)


def load_failed_packages(version="3.16"):
    """Load failed packages for a specific Python version."""

    koji = KOJI_PY316

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
    sorted_fails_316 = load_failed_packages("3.16")

    config_316 = VERSION_CONFIG["3.16"]
    # With no tracker filed yet, bugzillas() returns an empty list and the
    # resulting mapping has empty url/summary lists for every failed package.
    bugzillas_list = bugzillas(sorted_fails_316, config_316["tracker"], config_316["rawhide"])

    for version, sorted_fails in [("3.16", sorted_fails_316)]:
        config = VERSION_CONFIG[version]
        pkg_url_mapping = map_pkgs_and_bzurls(bugzillas_list, sorted_fails)
        with open(config["output_file"], 'w') as open_file:
            json.dump(pkg_url_mapping, open_file, indent=2)
        print(f"Bugzilla URLs for Python {version} written to {config['output_file']}")
