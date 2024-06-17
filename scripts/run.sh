#! /bin/bash
mkdir -p data

# post-mass-rebuild query - use koji now as a source for data
repoquery --repo=koji --source --whatrequires 'libpython3.13.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.13' --whatrequires 'python3.13dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python313.pkgs

# get what's built with old python in koji
repoquery --repo=koji --source --whatrequires 'libpython3.12.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.12' --whatrequires 'python3.12dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python312.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python312.pkgs data/python313.pkgs | grep -E -v '^(python3\.12)$' > data/todo.pkgs

# get the current progress and find the actual failures + blocked packages
curl https://raw.githubusercontent.com/hroncok/whatdoibuild/python3.13/progress.pkgs |env LANG=en_US.utf-8 sort > data/progress.pkgs

env LANG=en_US.utf-8 comm -12 data/progress.pkgs data/todo.pkgs > data/failed.pkgs
env LANG=en_US.utf-8 comm -3 data/progress.pkgs data/todo.pkgs > data/waiting.pkgs
rm data/todo.pkgs

# get packages and their respective maintainers
curl https://src.fedoraproject.org/extras/pagure_owner_alias.json -o data/pagure_owner_alias.json

# get bz urls for failed packages
python3 scripts/bugzillas.py
