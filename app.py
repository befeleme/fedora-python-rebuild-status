import sys

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

status_dict = {}
for pkg in all_pkgs_list:
    # it's been rebuilt but it doesn't require 'python(abi) = 3.13', skip
    if pkg == "python3.12":
        continue
    if pkg in SUCCESSFUL:
        status_dict[pkg] = "🟢"
    elif pkg in FAILED:
        status_dict[pkg] = "🔴"
    elif pkg in WAITING:
        status_dict[pkg] = "⚪"
    else:
        print(f"{pkg} doesn't belong in either cathegory", file=sys.stderr)


@app.route('/')
def index():
    return render_template(
        'index.html',
        number_pkgs_to_rebuild=len(ALL_PKGS),
        number_pkgs_success=len(SUCCESSFUL),
        number_pkgs_failed=len(FAILED),
        number_pkgs_waiting=len(WAITING),
        status_dict=status_dict,
    )
