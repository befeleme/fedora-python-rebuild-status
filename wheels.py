# SPDX-License-Identifier: BSD-2-Clause
# Taken and heavily adjusted from:
# https://github.com/meshy/pythonwheels/blob/fb1d09e6e2ae718db8f2379ecf854570ad86ebb9/utils.py

import json
import urllib.request


PYPI_URL = "https://pypi.org/pypi/{name}/json"

# Map version strings to their ABI tags
VERSION_ABI_TAGS = {
    "314": "cp314",
    "315": "cp315",
}


def get_top_360_packages():
    print("Generating packages...")
    with open("data/top-pypi-packages.json") as data_file:
        packages = json.load(data_file)["rows"]

    package_list = []
    for package in packages[:360]:
        package_list.append(package["project"])

    return package_list


def find_wheels(packages, abi_tag):
    """Find wheels for packages that support the specified Python version.

    Args:
        packages: List of package names to check
        abi_tag: ABI tag to check for (e.g., "cp314", "cp315")

    Returns:
        List of tuples (package_name, has_wheel_for_version)
    """
    results = []
    for package in packages:
        print(f"Fetching {package} data for {abi_tag}")
        has_version_wheel = False
        try:
            response = urllib.request.urlopen(PYPI_URL.format(name=package))
            data = json.loads(response.read())
        except urllib.error.HTTPError as e:
            print(f"Failed to fetch '{package}': {e}")
            results.append((package, has_version_wheel))
            continue

        for download in data["urls"]:
            if download["packagetype"] == "bdist_wheel":
                wheel_abi_tag = download["filename"].split("-")[-2]
                # wheel can be universal or compiled for the specific Python version
                # there can be additional letters at the end of the abi tag
                # e.g. "cp314t" built for free-threading
                if wheel_abi_tag in ["none", "abi3"] or wheel_abi_tag.startswith(abi_tag):
                    has_version_wheel = True
        results.append((package, has_version_wheel))
    return results


def generate_wheel_readiness_data(ver="314"):
    """Generate wheel readiness data for a specific Python version.

    Args:
        ver: Version string (e.g., "314", "315")

    Returns:
        Tuple of (results, support_count) where results is a list of
        (package_name, has_wheel) tuples and support_count is the number
        of packages with wheels
    """
    abi_tag = VERSION_ABI_TAGS.get(ver, "cp314")
    results = find_wheels(get_top_360_packages(), abi_tag)
    do_support = sum(result[1] for result in results)
    print(f"Done generating wheel data for Python {ver}")
    return results, do_support
