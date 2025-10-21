import datetime

from flask import Flask, render_template

from scripts.loaders import load_data, load_json, load_monitor_report, KOJI_PY314, KOJI_PY315
from wheels import generate_wheel_readiness_data

app = Flask("python_rebuild_status")


REPORT_STATES = {
    "success": "🟢",
    "once_succeeded_last_failed": "🟠",
    "waiting": "⚪",
    "failed": "🔴",
}

VERSIONS = {
    "314": {
        "major_version": "3.14",
        "fedora_version": "43",
        "koji_enabled": KOJI_PY314,
        "base_packages": "data/python313.pkgs",
        "exclude_package": "python3.13",
        "all_to_build": None,
        "successfully_rebuilt": None,
        "failed": None,
        "waiting": None,
        "bugzillas": None,
        "all_in_copr": None,
    },
    "315": {
        "major_version": "3.15",
        "fedora_version": "44",
        "koji_enabled": KOJI_PY315,
        "base_packages": "data/python314.pkgs",
        "exclude_package": "python3.14",
        "all_to_build": None,
        "successfully_rebuilt": None,
        "failed": None,
        "waiting": None,
        "bugzillas": None,
        "all_in_copr": None,
    }
}

# Load data for each version
for ver, config in VERSIONS.items():
    all_to_build = sorted(load_data(config["base_packages"]))
    all_to_build.remove(config["exclude_package"])
    config["all_to_build"] = all_to_build

    # TODO: this is a hack: I want F43 data for 3.14 rebuild and F44 data for 3.15,
    # hence the versioned file (python314.pkgs is in two source versions)
    if ver == "314":
        config["successfully_rebuilt"] = load_data(f"data/python{ver}-43.pkgs")
    else:
        config["successfully_rebuilt"] = load_data(f"data/python{ver}.pkgs")
    config["failed"] = load_data(f"data/failed_py{ver}.pkgs")
    config["waiting"] = load_data(f"data/waiting_py{ver}.pkgs")
    config["bugzillas"] = load_json(f"data/bzurls_py{ver}.json")

    if not config["koji_enabled"]:
        config["all_in_copr"] = load_monitor_report(f"data/copr_py{ver}.pkgs")


def load_python_version(ver):
    "Return just the version string from the whole src name"
    full_pkgname = load_data(f"data/pyver_py{ver}").pop()
    return full_pkgname.split(":")[-1].split("-")[0]


def count_pkgs_with_state(build_status, looked_for):
    return sum(1 for state in build_status.values() if state == looked_for)


def assign_build_status(ver):
    """Assign build status for packages for a given Python version.

    Args:
        ver: Version string (e.g., "314", "315")

    Returns:
        Dictionary mapping package names to their build status
    """
    config = VERSIONS[ver]
    if config["koji_enabled"]:
        return _assign_koji_build_status(ver)
    return _assign_copr_build_status(ver)


def _assign_koji_build_status(ver):
    """Assign build status for Koji builds."""
    config = VERSIONS[ver]
    build_status = {}
    for pkg in config["failed"]:
        build_status[pkg] = REPORT_STATES["failed"]
    for pkg in config["waiting"]:
        build_status[pkg] = REPORT_STATES["waiting"]
    for pkg in config["successfully_rebuilt"]:
        build_status[pkg] = REPORT_STATES["success"]
    return build_status


def _assign_copr_build_status(ver):
    """Assign build status for Copr builds."""
    config = VERSIONS[ver]
    build_status = {}
    for pkg in config["all_to_build"]:
        # pkg can build once and never again, so let's look at the last
        # build to determine if we need to take a look at it anyways
        if pkg in config["successfully_rebuilt"]:
            if config["all_in_copr"] and pkg in config["all_in_copr"]:
                last_build_state = config["all_in_copr"][pkg]
                if last_build_state == "failed":
                    status = REPORT_STATES["once_succeeded_last_failed"]
                elif last_build_state == "succeeded":
                    status = REPORT_STATES["success"]
                else:
                    # package is waiting in build queue, we don't know its status yet
                    status = REPORT_STATES["waiting"]
            else:
                status = REPORT_STATES["success"]
        elif pkg in config["failed"]:
            status = REPORT_STATES["failed"]
        elif pkg in config["waiting"]:
            status = REPORT_STATES["waiting"]
        else:
            # Default to waiting if no status is found
            status = REPORT_STATES["waiting"]
        build_status[pkg] = status
    return build_status


def find_maintainers(ver):
    """Find package maintainers for a given Python version.

    Args:
        ver: Version string (e.g., "314", "315")

    Returns:
        Dictionary mapping package names to their maintainers
    """
    # bits borrowed from: https://pagure.io/fedora-misc-package-utilities/blob/master/f/find-package-maintainers
    maintainers = load_json('data/pagure_owner_alias.json')
    config = VERSIONS[ver]
    return {pkg: maintainers["rpms"][pkg] for pkg in config["all_to_build"]}


def sort_by_maintainers(packages_with_maintainers, build_status):
    # get maintainer, their pkgs and build statuses
    by_maintainers = {}
    for pkg, maints in packages_with_maintainers.items():
        for maint in maints:
            by_maintainers.setdefault(maint, []).append(f"{pkg} {build_status[pkg]}")
    return sorted(by_maintainers.items())


def create_failed_report(ver, build_status):
    """Create a failure report for a given Python version.

    Args:
        ver: Version string (e.g., "314", "315")
        build_status: Dictionary mapping package names to their build status

    Returns:
        Dictionary mapping failed packages to their state and bugzilla data
    """
    failure_report = {}
    config = VERSIONS[ver]
    for pkg, bugs_data in config["bugzillas"].items():
        if (state := build_status.get(pkg)) is not None:
            failure_report[pkg] = dict({"state": state}, **bugs_data)
    return failure_report


def as_percentage(state, total):
    return f"{state * 100 / total:.2f}" if total > 0 else "0.00"


# Prepare data for all versions
build_data = {}
wheel_data = {}
for ver in VERSIONS.keys():
    build_status = assign_build_status(ver)
    packages_with_maintainers = find_maintainers(ver)
    config = VERSIONS[ver]

    build_data[ver] = {
        "build_status": build_status,
        "packages_with_maintainers": packages_with_maintainers,
        "status_by_packages": [(pkg, build_status[pkg], packages_with_maintainers[pkg]) for pkg in config["all_to_build"]],
        "status_by_maintainers": sort_by_maintainers(packages_with_maintainers, build_status),
        "failed_report": create_failed_report(ver, build_status),
    }

    # Generate wheel readiness data for each version
    wheel_readiness, wheels_count = generate_wheel_readiness_data(ver)
    wheel_data[ver] = {
        "readiness": wheel_readiness,
        "count": wheels_count,
    }

updated = datetime.datetime.now()


@app.route('/')
def index():
    # Calculate statistics for each version
    template_vars = {"updated": updated}

    for ver, config in VERSIONS.items():
        data = build_data[ver]
        build_status = data["build_status"]
        success = count_pkgs_with_state(build_status, REPORT_STATES["success"])
        failed = count_pkgs_with_state(build_status, REPORT_STATES["failed"])
        blocked = count_pkgs_with_state(build_status, REPORT_STATES["waiting"])
        flaky = count_pkgs_with_state(build_status, REPORT_STATES["once_succeeded_last_failed"])
        if config["koji_enabled"]:
            total = len(config["all_to_build"]) + success
            waiting = blocked + failed
        else:
            total = len(config["all_to_build"])
            waiting = blocked

        success_pct = as_percentage(success, total)
        failed_pct = as_percentage(failed, total)
        waiting_pct = as_percentage(waiting, total)
        blocked_pct = as_percentage(blocked, total)
        flaky_pct = as_percentage(flaky, total)

        prefix = f"py{ver}"
        template_vars.update({
            f"{prefix}_fedora_version": config["fedora_version"],
            f"{prefix}_target_fedora": config["fedora_version"],
            f"{prefix}_current_version": load_python_version(ver),
            f"{prefix}_data_source": "Koji" if config["koji_enabled"] else "Copr",
            f"{prefix}_total_packages": total,
            f"{prefix}_success_count": success,
            f"{prefix}_success_percentage": success_pct,
            f"{prefix}_waiting_count": waiting,
            f"{prefix}_waiting_percentage": waiting_pct,
            f"{prefix}_failed_count": failed,
            f"{prefix}_failed_percentage": failed_pct,
            f"{prefix}_blocked_count": blocked,
            f"{prefix}_blocked_percentage": blocked_pct,
            f"{prefix}_flaky_count": flaky,
            f"{prefix}_flaky_percentage": flaky_pct,
        })

    return render_template('index.html', **template_vars)

@app.route('/packages/')
def packages():
    return render_template(
        'packages_py315.html',
        py315_status_by_packages=build_data["315"]["status_by_packages"],
        updated=updated,
    )

@app.route('/maintainers/')
def maintainers():
    return render_template(
        'maintainers_py315.html',
        py315_status_by_maintainers=build_data["315"]["status_by_maintainers"],
        updated=updated,
    )

@app.route('/failures/')
def failures():
    return render_template(
        'failures_py315.html',
        py315_status_failed=build_data["315"]["failed_report"],
        updated=updated,
        zip=zip,
    )

@app.route('/packages_py314/')
def packages_py314():
    return render_template(
        'packages_py314.html',
        py314_status_by_packages=build_data["314"]["status_by_packages"],
        updated=updated,
    )

@app.route('/maintainers_py314/')
def maintainers_py314():
    return render_template(
        'maintainers_py314.html',
        py314_status_by_maintainers=build_data["314"]["status_by_maintainers"],
        updated=updated,
    )

@app.route('/failures_py314/')
def failures_py314():
    return render_template(
        'failures_py314.html',
        py314_status_failed=build_data["314"]["failed_report"],
        updated=updated,
        zip=zip,
    )

@app.route('/wheels/')
def wheels():
    return render_template(
        'wheels.html',
        results=wheel_data["315"]["readiness"],
        major=VERSIONS["315"]["major_version"],
        updated=updated,
        do_support=wheel_data["315"]["count"],
    )

@app.route('/wheels_py314/')
def wheels_py314():
    return render_template(
        'wheels.html',
        results=wheel_data["314"]["readiness"],
        major=VERSIONS["314"]["major_version"],
        updated=updated,
        do_support=wheel_data["314"]["count"],
    )

@app.route('/packages_py315/')
def packages_py315():
    return render_template(
        'packages_py315.html',
        py315_status_by_packages=build_data["315"]["status_by_packages"],
        updated=updated,
    )

@app.route('/maintainers_py315/')
def maintainers_py315():
    return render_template(
        'maintainers_py315.html',
        py315_status_by_maintainers=build_data["315"]["status_by_maintainers"],
        updated=updated,
    )

@app.route('/failures_py315/')
def failures_py315():
    return render_template(
        'failures_py315.html',
        py315_status_failed=build_data["315"]["failed_report"],
        updated=updated,
        zip=zip,
    )

@app.route('/wheels_py315/')
def wheels_py315():
    return render_template(
        'wheels.html',
        results=wheel_data["315"]["readiness"],
        major=VERSIONS["315"]["major_version"],
        updated=updated,
        do_support=wheel_data["315"]["count"],
    )
