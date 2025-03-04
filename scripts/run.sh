#! /bin/bash -eu
mkdir -p data

# get what was built with new python in copr
repoquery --repo=python314 --source --whatrequires 'libpython3.14.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.14' --whatrequires 'python3.14dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python314.pkgs

# # post-mass-rebuild query - use koji now as a source for data
# repoquery --repo=koji --source --whatrequires 'libpython3.13.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.13' --whatrequires 'python3.13dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python313.pkgs

# get what's built with old python in koji
repoquery --repo=koji --source --whatrequires 'libpython3.13.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.13' --whatrequires 'python3.13dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python313.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python313.pkgs data/python314.pkgs | grep -E -v '^(python3\.13)$' > data/todo.pkgs

# get everything present in copr
copr monitor @python/python3.14 --output-format text-row --fields name,state | env LANG=en_US.utf-8 sort > data/copr.pkgs
cut -f1 data/copr.pkgs | sort > data/copr_names.pkgs
env LANG=en_US.utf-8 comm -23 data/todo.pkgs data/copr_names.pkgs > data/waiting.pkgs
env LANG=en_US.utf-8 comm -12 data/todo.pkgs data/copr_names.pkgs > data/failed.pkgs
rm data/copr_names.pkgs

# # post-mass-rebuild query
# # get the current progress and find the actual failures + blocked packages
# curl https://raw.githubusercontent.com/hroncok/whatdoibuild/python3.13/progress.pkgs |env LANG=en_US.utf-8 sort > data/progress.pkgs
# env LANG=en_US.utf-8 comm -12 data/progress.pkgs data/todo.pkgs > data/failed.pkgs
# env LANG=en_US.utf-8 comm -13 data/progress.pkgs data/todo.pkgs > data/waiting.pkgs

repoquery -q --repo python314 python3.14 --latest-limit 1 > data/pyver

# get packages and their respective maintainers
curl https://src.fedoraproject.org/extras/pagure_owner_alias.json -o data/pagure_owner_alias.json

# get bz urls for failed packages
python3 scripts/bugzillas.py

# download the most downloaded packages from PyPI
wget https://hugovk.github.io/top-pypi-packages/top-pypi-packages.min.json -O data/top-pypi-packages.json
