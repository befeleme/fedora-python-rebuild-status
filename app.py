import json
import sys

from flask import Flask, render_template

app = Flask("python_rebuild_status")


def load_data(filename):
    with open(filename, "r", encoding="utf=8") as f:
        return {row.strip() for row in f.readlines()}


ALL_PKGS = sorted(load_data("data/python312.pkgs"))
SUCCESSFUL = load_data("data/python313.pkgs")
TODO = load_data("data/todo.pkgs")
WAITING = load_data("data/waiting.pkgs")
FAILED = TODO - WAITING


def assign_build_status():
    build_status = {}
    for pkg in ALL_PKGS:
        if pkg not in (SUCCESSFUL | TODO) and pkg != "python3.12":
            print(f"{pkg} doesn't belong in either cathegory", file=sys.stderr)
            continue
        # it's been rebuilt but it doesn't require 'python(abi) = 3.13'
        if pkg in SUCCESSFUL or pkg == "python3.12":
            status = "🟢"
        elif pkg in FAILED:
            status = "🔴"
        elif pkg in WAITING:
            status = "⚪"
        build_status[pkg] = status
    return build_status


def find_maintainers():
    # bits borrowed from: https://pagure.io/fedora-misc-package-utilities/blob/master/f/find-package-maintainers
    with open('data/pagure_owner_alias.json', 'r') as f:
        maintainers = json.load(f)
    return {pkg: maintainers["rpms"][pkg] for pkg in ALL_PKGS }


def sort_by_maintainers(packages_with_maintainers, build_status):
    # get maintainer, their pkgs and build statuses
    by_maintainers = {}
    for pkg, maints in packages_with_maintainers.items():
        for maint in maints:
            by_maintainers.setdefault(maint, []).append(f"{pkg} {build_status[pkg]}")
    return sorted(by_maintainers.items())


build_status = assign_build_status()
packages_with_maintainers = find_maintainers()
status_by_packages = [(pkg, build_status[pkg], packages_with_maintainers[pkg]) for pkg in ALL_PKGS]
status_by_maintainers = sort_by_maintainers(packages_with_maintainers, build_status)


@app.route('/')
def index():
    return render_template(
        'index.html',
        number_pkgs_to_rebuild=len(ALL_PKGS),
        number_pkgs_success=len(SUCCESSFUL),
        number_pkgs_failed=len(FAILED),
        number_pkgs_waiting=len(WAITING),
    )

@app.route('/packages')
def packages():
    return render_template(
        'packages.html',
        status_by_packages=status_by_packages,
    )

@app.route('/maintainers')
def maintainers():
    return render_template(
        'maintainers.html',
        status_by_maintainers=status_by_maintainers,
    )

@app.route('/failures')
def failures():
        return render_template(
        'failures.html',
        status_failed=sorted(FAILED),
    )
