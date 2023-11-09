import sys

import requests

from flask import Flask, render_template

app = Flask("python_rebuild_status")


def load_data(filename):
    with open(filename, "r", encoding="utf=8") as f:
        return {row.strip() for row in f.readlines()}


ALL_PKGS = load_data("data/python312.pkgs")
SUCCESSFUL = load_data("data/python313.pkgs")
TODO = load_data("data/todo.pkgs")
WAITING = load_data("data/waiting.pkgs")
FAILED = TODO - WAITING

all_pkgs_list = sorted(ALL_PKGS)
build_status = {}
for pkg in all_pkgs_list:
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

# bits borrowed from: https://pagure.io/fedora-misc-package-utilities/blob/master/f/find-package-maintainers
maintainers = requests.get('https://src.fedoraproject.org/extras/pagure_owner_alias.json').json()
by_package = {pkg: maintainers["rpms"][pkg] for pkg in ALL_PKGS }

# get package, its build status and list of maintainers
status_by_packages = [(pkg, build_status[pkg], by_package[pkg]) for pkg in all_pkgs_list]

# get maintainer, their pkgs and build statuses
status_by_maintainers = {}
for pkg, maints in sorted(by_package.items()):
    for maint in maints:
        status_by_maintainers.setdefault(maint, []).append(f"{pkg} {build_status[pkg]}")

@app.route('/')
def index():
    return render_template(
        'index.html',
        number_pkgs_to_rebuild=len(ALL_PKGS),
        number_pkgs_success=len(SUCCESSFUL),
        number_pkgs_failed=len(FAILED),
        number_pkgs_waiting=len(WAITING),
        status_by_packages=status_by_packages,
        status_by_maintainers=status_by_maintainers,
    )