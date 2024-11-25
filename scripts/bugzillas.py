import json
import bugzilla

from loaders import load_data, load_monitor_report, KOJI


BUGZILLA = 'bugzilla.redhat.com'
BZ_PAGE_SIZE = 20
TRACKER = 2322407  # PYTHON3.14
RAWHIDE = 2300528  # F42FTBFS
BZAPI = bugzilla.Bugzilla(BUGZILLA)

FAILED = load_data("data/failed.pkgs")
# we only want to do Copr magic before the mass rebuild
if not KOJI:
    HISTORICALLY_SUCCESSFUL = load_data("data/python314.pkgs")
    ALL_IN_COPR = load_monitor_report("data/copr.pkgs")

    # Attempt to find bugzillas for packages that
    # started to fail to build just recently
    FAILED.update(pkg for pkg in HISTORICALLY_SUCCESSFUL if ALL_IN_COPR.get(pkg) == "failed")

SORTED_FAILS = sorted(FAILED)


def bugzillas():
    query = BZAPI.build_query(product='Fedora')
    query['blocks'] = [TRACKER, RAWHIDE]
    query['limit'] = BZ_PAGE_SIZE
    query['offset'] = 0
    results = []
    while len(partial := BZAPI.query(query)) == BZ_PAGE_SIZE:
        results += partial
        query['offset'] += BZ_PAGE_SIZE
    results += partial
    return [b for b in sorted(results, key=lambda b: -b.id)
            if b.is_open and b.component in SORTED_FAILS]


def map_pkgs_and_bzurls(bugzillas):
    pkgs_urls = {pkg: {"urls": [], "summaries": []} for pkg in SORTED_FAILS}
    for bug in bugzillas:
        pkgs_urls[bug.component]["urls"].append(bug.weburl)
        pkgs_urls[bug.component]["summaries"].append(bug.summary)
    return pkgs_urls


if __name__ == "__main__":
    pkg_url_mapping = map_pkgs_and_bzurls(bugzillas())
    with open('data/bzurls.json', 'w') as open_file:
        json.dump(pkg_url_mapping, open_file, indent=2)
