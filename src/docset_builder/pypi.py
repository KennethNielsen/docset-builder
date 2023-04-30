"""This module extracts information from PyPI"""

import json
from distutils.version import StrictVersion

import urllib3
from attrs import evolve

from docset_builder.cache import load_pypi_info, cache_pypi_info
from docset_builder.data_structures import PyPIInfo
from docset_builder.overrides import PYPI_OVERRIDES

HTTP = urllib3.PoolManager()


def get_information_for_package(package: str) -> PyPIInfo | None:
    """Return information extracted from PyPI"""
    if pypi_info := load_pypi_info(package_name=package):
        return pypi_info

    response = HTTP.request("GET", f"https://pypi.org/pypi/{package}/json")
    if response.status != 200:
        return None

    # Get possible overrides
    pypi_info = PYPI_OVERRIDES.get(package, PyPIInfo())

    # Extract repository url
    if pypi_info.repository_url is None:
        data = json.loads(response.data.decode("utf-8"))
        try:
            repository_url = data["info"]["project_urls"]["Repository"]
        except KeyError:
            pass
        else:
            pypi_info = evolve(pypi_info, repository_url=repository_url)

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
