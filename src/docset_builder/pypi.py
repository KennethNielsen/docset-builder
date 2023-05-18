"""This module extracts information from PyPI"""

import json
from distutils.version import StrictVersion
from pathlib import Path

import urllib3
from attrs import evolve

from docset_builder.cache import cache_pypi_info, load_pypi_info
from docset_builder.data_structures import PyPIInfo
from docset_builder.overrides import PYPI_OVERRIDES

HTTP = urllib3.PoolManager()


def get_information_for_package(
    package: str, package_test_dump_path: Path | None
) -> PyPIInfo | None:
    """Return information extracted from PyPI"""
    if (
        pypi_info := load_pypi_info(package_name=package)
    ) and not package_test_dump_path:
        return pypi_info

    response = urllib3.request("GET", f"https://pypi.org/pypi/{package}/json")  # type: ignore
    if response.status != 200:
        return None

    if package_test_dump_path:
        with open(package_test_dump_path / "pypi_raw.json", "w") as file_:
            json.dump(response.json(), file_)

    # Get possible overrides
    pypi_info = PYPI_OVERRIDES.get(package, PyPIInfo())

    # Extract repository url
    if pypi_info.repository_url is None:
        data = response.json()
        for key in ("Repository",):  # "Source Code"):
            try:
                repository_url = data["info"]["project_urls"][key]
            except KeyError:
                pass
            else:
                pypi_info = evolve(pypi_info, repository_url=repository_url)
                break

    # Extract latest release
    if pypi_info.latest_release is None:
        try:
            releases = tuple(data["releases"].keys())
        except KeyError:
            releases = ()
        sorted_releases = sorted(releases, key=StrictVersion)

        try:
            latest_release = sorted_releases[-1]
        except IndexError:
            pass
        else:
            pypi_info = evolve(pypi_info, latest_release=latest_release)

    cache_pypi_info(package_name=package, pypi_info=pypi_info)

    return pypi_info
