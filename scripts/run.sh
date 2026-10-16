#! /bin/bash -eu
mkdir -p data

##############################################################################
# Python 3.16 Data Collection (from Copr - pre-mass-rebuild)
##############################################################################

# get what was built with python 3.16 in copr
repoquery --repo=python316 --source --whatrequires 'libpython3.16.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.16' --whatrequires 'python3.16dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python316.pkgs

# get what's built with the old python in rawhide koji
repoquery --repo=koji --source --whatrequires 'libpython3.15.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.15' --whatrequires 'python3.15dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python315.pkgs

# get everything present in copr for python 3.16
copr monitor @python/python3.16 --output-format text-row --fields name,state | env LANG=en_US.utf-8 sort > data/copr_py316.pkgs
cut -f1 data/copr_py316.pkgs | sort > data/copr_names_py316.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python315.pkgs data/python316.pkgs | grep -E -v '^(python3\.15)$' > data/todo_py316.pkgs || true

# determine waiting and failed packages for python 3.16
env LANG=en_US.utf-8 comm -23 data/todo_py316.pkgs data/copr_names_py316.pkgs > data/waiting_py316.pkgs || true
env LANG=en_US.utf-8 comm -12 data/todo_py316.pkgs data/copr_names_py316.pkgs > data/failed_py316.pkgs || true
rm data/copr_names_py316.pkgs

# get python 3.16 version from copr
repoquery -q --repo python316 python3.16 --latest-limit 1 > data/pyver_py316


##############################################################################
# Common Data Collection
##############################################################################

# get packages and their respective maintainers
curl https://src.fedoraproject.org/extras/pagure_owner_alias.json -o data/pagure_owner_alias.json

# no PYTHON3.16 tracker yet - skip bugzilla collection for now
# get bz urls for failed packages (python 3.16)
# python3 scripts/bugzillas.py --version 3.16

# download the most downloaded packages from PyPI
wget https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json -O data/top-pypi-packages.json

# download commonly needed components report
curl https://raw.githubusercontent.com/fedora-python/whatdoibuild/refs/heads/python3.16/commonly-needed-report.json -o data/commonly-needed-report.json
