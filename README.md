# Fedora Python Rebuild Status

Report of the progress of integration of the new Python version to future Fedora which can be found on GitHub Pages.

See: [Fedora Python Rebuild Status](https://befeleme.github.io/fedora-python-rebuild-status/)

The engine of the page is a nightly GitHub Action run on a Fedora container which:
- pulls all the relevant data from Python rebuild Copr and Fedora Rawhide Koji repositories ([scripts/run.sh](scripts/run.sh), repo configs: [config/copr.repo](config/copr.repo), [config/koji.repo](config/koji.repo))
- for packages that failed to build, looks for their open bugzilla ticket URLs ([scripts/bugzillas.py](scripts/bugzillas.py))
- fills in all the calculated bits into Jinja templates with Flask
- creates static HTML pages with freezeyt ([.github/workflows/ci.yaml](.github/workflows/ci.yaml))

The necessary packages are defined in `requirements.txt`.
The license is [MIT](LICENSE).
