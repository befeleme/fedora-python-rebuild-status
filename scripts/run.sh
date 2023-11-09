#! /bin/bash
mkdir -p data

# get what was built with new python in copr
repoquery --repo=python313 --source --whatrequires 'libpython3.13.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.13' --whatrequires 'python3.13dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python313.pkgs

# get what's built with old python in koji
repoquery --repo=koji --source --whatrequires 'libpython3.12.so.1.0()(64bit)' --whatrequires 'python(abi) = 3.12' --whatrequires 'python3.12dist(*)' | pkgname | env LANG=en_US.utf-8 sort | uniq > data/python312.pkgs

# get what remains to be built
env LANG=en_US.utf-8 comm -23 data/python312.pkgs data/python313.pkgs | grep -E -v '^(python3\.12)$' > data/todo.pkgs

# get eveything present in copr
copr monitor @python/python3.13 --output-format text-row --fields name | env LANG=en_US.utf-8 sort > data/copr.pkgs
env LANG=en_US.utf-8 comm -23 data/todo.pkgs data/copr.pkgs > data/waiting.pkgs