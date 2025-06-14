import datetime
import sys

from flask import Flask, render_template

from scripts.loaders import load_data, load_json, load_monitor_report, KOJI
from wheels import generate_wheel_readiness_data

app = Flask("python_rebuild_status")


REPORT_STATES = {
    "success": "🟢",
    "once_succeeded_last_failed": "🟠",
    "waiting": "⚪",
    "failed": "🔴",
}

MAJOR_VERSION = "3.14"
WHEEL_MAJOR_VERSION = "3.14"
ALL_TO_BUILD = sorted(load_data("data/python313.pkgs"))
ALL_TO_BUILD.remove("python3.13")  # it won't ever require 'python(abi) = MAJOR_VERSION'
SUCCESSFULLY_REBUILT = load_data("data/python314.pkgs")
FAILED = load_data("data/failed.pkgs")
WAITING = load_data("data/waiting.pkgs")
BUGZILLAS = load_json("data/bzurls.json")
if not KOJI:
    ALL_IN_COPR = load_monitor_report("data/copr.pkgs")


def load_current_python_version():
    "Return just the version string from the whole src name"
    full_pkgname = load_data("data/pyver").pop()
    return full_pkgname.split(":")[-1].split("-")[0]


def count_pkgs_with_state(build_status, looked_for):
    return sum(1 for state in build_status.values() if state == looked_for)


def assign_build_status():
    if KOJI:
        return _assign_koji_build_status()
    return _assign_copr_build_status()


def _assign_koji_build_status():
    build_status = {}
    for pkg in FAILED:
        build_status[pkg] = REPORT_STATES["failed"]
    for pkg in WAITING:
        build_status[pkg] = REPORT_STATES["waiting"]
    for pkg in SUCCESSFULLY_REBUILT:
        build_status[pkg] = REPORT_STATES["success"]
    return build_status


def _assign_copr_build_status():
    build_status = {}
    for pkg in ALL_TO_BUILD:
        # pkg can build once and never again, so let's look at the last
        # build to determine if we need to take a look at it anyways
        if pkg in SUCCESSFULLY_REBUILT:
            last_build_state = ALL_IN_COPR[pkg]
            if last_build_state == "failed":
                status = REPORT_STATES["once_succeeded_last_failed"]
            elif last_build_state == "succeeded":
                status = REPORT_STATES["success"]
            else:
                # package is waiting in build queue, we don't know its status yet
                status = REPORT_STATES["waiting"]
        elif pkg in FAILED:
            status = REPORT_STATES["failed"]
        elif pkg in WAITING:
            status = REPORT_STATES["waiting"]
        build_status[pkg] = status
    return build_status


def find_maintainers():
    # bits borrowed from: https://pagure.io/fedora-misc-package-utilities/blob/master/f/find-package-maintainers
    maintainers = load_json('data/pagure_owner_alias.json')
    return {pkg: maintainers["rpms"][pkg] for pkg in ALL_TO_BUILD}


def sort_by_maintainers(packages_with_maintainers, build_status):
    # get maintainer, their pkgs and build statuses
    by_maintainers = {}
    for pkg, maints in packages_with_maintainers.items():
        for maint in maints:
            by_maintainers.setdefault(maint, []).append(f"{pkg} {build_status[pkg]}")
    return sorted(by_maintainers.items())


def create_failed_report(build_status):
    failure_report = {}
    for pkg, bugs_data in BUGZILLAS.items():
        if (state := build_status.get(pkg)) is not None:
            failure_report[pkg] = dict({"state": state}, **bugs_data)
    return failure_report


build_status = assign_build_status()
packages_with_maintainers = find_maintainers()
status_by_packages = [(pkg, build_status[pkg], packages_with_maintainers[pkg]) for pkg in ALL_TO_BUILD]
status_by_maintainers = sort_by_maintainers(packages_with_maintainers, build_status)
wheel_readiness, wheels_count = generate_wheel_readiness_data()

updated = datetime.datetime.now()


@app.route('/')
def index():
    return render_template(
        'index.html',
        number_pkgs_to_rebuild=len(ALL_TO_BUILD),
        number_pkgs_success=count_pkgs_with_state(build_status, REPORT_STATES["success"]),
        number_pkgs_flaky=count_pkgs_with_state(build_status, REPORT_STATES["once_succeeded_last_failed"]),
        number_pkgs_failed=len(FAILED),
        number_pkgs_waiting=len(WAITING),
        updated=updated,
        majorver=MAJOR_VERSION,
        currver=load_current_python_version(),
    )

@app.route('/packages/')
def packages():
    return render_template(
        'packages.html',
        status_by_packages=status_by_packages,
        updated=updated,
        majorver=MAJOR_VERSION,
    )

@app.route('/maintainers/')
def maintainers():
    return render_template(
        'maintainers.html',
        status_by_maintainers=status_by_maintainers,
        updated=updated,
        majorver=MAJOR_VERSION,
    )

@app.route('/failures/')
def failures():
        return render_template(
        'failures.html',
        status_failed=create_failed_report(build_status),
        updated=updated,
        majorver=MAJOR_VERSION,
        zip=zip,
    )

@app.route('/wheels/')
def wheels():
        return render_template(
        'wheels.html',
        results=wheel_readiness,
        major=WHEEL_MAJOR_VERSION,
        updated=updated,
        do_support=wheels_count,
    )
