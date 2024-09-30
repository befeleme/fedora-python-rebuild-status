# SPDX-License-Identifier: BSD-2-Clause
# Taken and heavily adjusted from:
# https://github.com/meshy/pythonwheels/blob/fb1d09e6e2ae718db8f2379ecf854570ad86ebb9/utils.py

import json
import urllib.request


PYPI_URL = "https://pypi.org/pypi/{name}/json"

NEWEST_PYTHON_ABI_TAG = "cp313"


def get_top_360_packages():
    print("Generating packages...")
    with open("data/top-pypi-packages.json") as data_file:
        packages = json.load(data_file)["rows"]

    package_list = []
    for package in packages[:360]:
        package_list.append(package["project"])

    return package_list


def find_wheels(packages):
    results = []
    for package in packages:
        print(f"Fetching {package} data")
        has_newest_wheel = False
        try:
            response = urllib.request.urlopen(PYPI_URL.format(name=package))
            data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            print(f"Failed to fetch '{package}': {e}")
            results.append((package, has_newest_wheel))
            continue

        for download in data["urls"]:
            if download["packagetype"] == "bdist_wheel":
                abi_tag = download["filename"].split("-")[-2]
                # wheel can be universal or compiled for the specific Python version
                # there can be additional letters at the end of the abi tag
                # e.g. "cp313t" built for free-threading
                if abi_tag in ["none", "abi3"] or abi_tag.startswith(NEWEST_PYTHON_ABI_TAG):
                    has_newest_wheel = True
        results.append((package, has_newest_wheel))
    return results


def generate_wheel_readiness_data():
    results = find_wheels(get_top_360_packages())
    do_support = sum(result[1] for result in results)
    print("Done")
    return results, do_support
