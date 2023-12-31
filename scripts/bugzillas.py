import json
import bugzilla

from loaders import load_data, load_monitor_report


BUGZILLA = 'bugzilla.redhat.com'
BZ_PAGE_SIZE = 20
TRACKER = 2244836  # PYTHON3.13
BZAPI = bugzilla.Bugzilla(BUGZILLA)

FAILED = load_data("data/failed.pkgs")
HISTORICALLY_SUCCESSFUL = load_data("data/python313.pkgs")
ALL_IN_COPR = load_monitor_report("data/copr.pkgs")

# Attempt to find bugzillas for packages that
# started to fail to build just recently
FAILED.update(pkg for pkg in HISTORICALLY_SUCCESSFUL if ALL_IN_COPR.get(pkg) == "failed")


def bugzillas():
    query = BZAPI.build_query(product='Fedora')
    query['blocks'] = TRACKER
    query['limit'] = BZ_PAGE_SIZE
    query['offset'] = 0
    results = []
    while len(partial := BZAPI.query(query)) == BZ_PAGE_SIZE:
        results += partial
        query['offset'] += BZ_PAGE_SIZE
    results += partial
    return [b for b in sorted(results, key=lambda b: -b.id)
            if b.resolution != 'DUPLICATE']


def bz_url(bugzillas, failed_pkg):
    for bug in bugzillas:
        if failed_pkg == bug.component and bug.is_open:
            return bug.weburl
    return None


def map_pkgs_and_bzurls(bugzillas):
    pkgs_urls = {}
    for failed_pkg in sorted(FAILED):
        pkgs_urls[failed_pkg] = bz_url(bugzillas, failed_pkg)
    return pkgs_urls


if __name__ == "__main__":
    pkg_url_mapping = map_pkgs_and_bzurls(bugzillas())
    with open('data/bzurls.json', 'w') as open_file:
        json.dump(pkg_url_mapping, open_file, indent=2)
