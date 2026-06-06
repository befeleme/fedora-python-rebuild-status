#! /bin/bash -eu
mkdir -p data

##############################################################################
# Python 3.15 Data Collection (from Koji - post-mass-rebuild)
##############################################################################

# post-mass-rebuild query - use koji now as a source for data
repoquery --repo=koji --source --whatrequires 'libpython3.15.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.15' --whatrequires 'python3.15dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python315-45.pkgs

# get what's built with old python in koji
repoquery --repo=koji --source --whatrequires 'libpython3.14.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.14' --whatrequires 'python3.14dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python314.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python314.pkgs data/python315-45.pkgs | grep -E -v '^(python3\.14)$' > data/todo_py315.pkgs

# post-mass-rebuild query
# get the current progress and find the actual failures + blocked packages
curl https://raw.githubusercontent.com/hroncok/whatdoibuild/python3.15/progress.pkgs |env LANG=en_US.utf-8 sort > data/progress_py315.pkgs
env LANG=en_US.utf-8 comm -12 data/progress_py315.pkgs data/todo_py315.pkgs > data/failed_py315.pkgs
env LANG=en_US.utf-8 comm -13 data/progress_py315.pkgs data/todo_py315.pkgs > data/waiting_py315.pkgs

repoquery -q --repo python315 python3.15 --latest-limit 1 > data/pyver_py315


##############################################################################
# Common Data Collection
##############################################################################

# get packages and their respective maintainers
curl https://src.fedoraproject.org/extras/pagure_owner_alias.json -o data/pagure_owner_alias.json

# get bz urls for failed packages (python 3.15)
python3 scripts/bugzillas.py --version 3.15

# download the most downloaded packages from PyPI
wget https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json -O data/top-pypi-packages.json

# download commonly needed components report
curl https://raw.githubusercontent.com/fedora-python/whatdoibuild/refs/heads/python3.15/commonly-needed-report.json -o data/commonly-needed-report.json
