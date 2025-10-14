#! /bin/bash -eu
mkdir -p data

##############################################################################
# Python 3.14 Data Collection (from Koji - post-mass-rebuild)
##############################################################################

# get what was built with new python in copr
# repoquery --repo=python314 --source --whatrequires 'libpython3.14.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.14' --whatrequires 'python3.14dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python314.pkgs

# post-mass-rebuild query - use koji now as a source for data
repoquery --repo=koji --source --whatrequires 'libpython3.14.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.14' --whatrequires 'python3.14dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python314.pkgs

# get what's built with old python in koji
repoquery --repo=koji --source --whatrequires 'libpython3.13.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.13' --whatrequires 'python3.13dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python313.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python313.pkgs data/python314.pkgs | grep -E -v '^(python3\.13)$' > data/todo_py314.pkgs

# get everything present in copr
# copr monitor @python/python3.14 --output-format text-row --fields name,state | env LANG=en_US.utf-8 sort > data/copr_py314.pkgs
# cut -f1 data/copr_py314.pkgs | sort > data/copr_names_py314.pkgs
# env LANG=en_US.utf-8 comm -23 data/todo_py314.pkgs data/copr_names_py314.pkgs > data/waiting_py314.pkgs
# env LANG=en_US.utf-8 comm -12 data/todo_py314.pkgs data/copr_names_py314.pkgs > data/failed_py314.pkgs
# rm data/copr_names_py314.pkgs

# post-mass-rebuild query
# get the current progress and find the actual failures + blocked packages
curl https://raw.githubusercontent.com/hroncok/whatdoibuild/python3.14/progress.pkgs |env LANG=en_US.utf-8 sort > data/progress_py314.pkgs
env LANG=en_US.utf-8 comm -12 data/progress_py314.pkgs data/todo_py314.pkgs > data/failed_py314.pkgs
env LANG=en_US.utf-8 comm -13 data/progress_py314.pkgs data/todo_py314.pkgs > data/waiting_py314.pkgs

repoquery -q --repo python314 python3.14 --latest-limit 1 > data/pyver_py314

##############################################################################
# Python 3.15 Data Collection (from Copr)
##############################################################################

# get what was built with python 3.15 in copr
repoquery --repo=python315 --source --whatrequires 'libpython3.15.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.15' --whatrequires 'python3.15dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python315.pkgs

# get everything present in copr for python 3.15
copr monitor @python/python3.15 --output-format text-row --fields name,state | env LANG=en_US.utf-8 sort > data/copr_py315.pkgs
cut -f1 data/copr_py315.pkgs | sort > data/copr_names_py315.pkgs

# get what remains to be built (comparing with python 3.14 base)
env LANG=en_US.utf-8 comm -23 data/python314.pkgs data/python315.pkgs | grep -E -v '^(python3\.14)$' > data/todo_py315.pkgs

# determine waiting and failed packages for python 3.15
env LANG=en_US.utf-8 comm -23 data/todo_py315.pkgs data/copr_names_py315.pkgs > data/waiting_py315.pkgs
env LANG=en_US.utf-8 comm -12 data/todo_py315.pkgs data/copr_names_py315.pkgs > data/failed_py315.pkgs
rm data/copr_names_py315.pkgs

# get python 3.15 version from copr
repoquery -q --repo python315 python3.15 --latest-limit 1 > data/pyver_py315

##############################################################################
# Common Data Collection
##############################################################################

# get packages and their respective maintainers
curl https://src.fedoraproject.org/extras/pagure_owner_alias.json -o data/pagure_owner_alias.json

# get bz urls for failed packages (python 3.14)
python3 scripts/bugzillas.py

# get bz urls for failed packages (python 3.15)
python3 scripts/bugzillas.py --version 3.15

# download the most downloaded packages from PyPI
wget https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json -O data/top-pypi-packages.json
