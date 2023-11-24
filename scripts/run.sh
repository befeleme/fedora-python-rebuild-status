#! /bin/bash
mkdir -p data

# get what was built with new python in copr
repoquery --repo=python313 --source --whatrequires 'libpython3.13.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.13' --whatrequires 'python3.13dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python313.pkgs

# get what's built with old python in koji
repoquery --repo=koji --source --whatrequires 'libpython3.12.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.12' --whatrequires 'python3.12dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python312.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python312.pkgs data/python313.pkgs | grep -E -v '^(python3\.12)$' > data/todo.pkgs

# get everything present in copr
copr monitor @python/python3.13 --output-format text-row --fields name,state | env LANG=en_US.utf-8 sort > data/copr.pkgs
cut -f1 data/copr.pkgs | sort > data/copr_names.pkgs
env LANG=en_US.utf-8 comm -23 data/todo.pkgs data/copr_names.pkgs > data/waiting.pkgs
env LANG=en_US.utf-8 comm -12 data/todo.pkgs data/copr_names.pkgs > data/failed.pkgs
rm data/copr_names.pkgs data/todo.pkgs

# get packages and their respective maintainers
curl https://src.fedoraproject.org/extras/pagure_owner_alias.json -o data/pagure_owner_alias.json

# get bz urls for failed packages
python3 scripts/bugzillas.py
