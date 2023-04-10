"""This module extracts information from PyPI"""

import json
from distutils.version import StrictVersion

from attrs import define
import urllib3


HTTP = urllib3.PoolManager()


@define
class PyPIInfo:
    """PyPI information about package"""
    url: str
    latest_release: str

def get_information_for_package(package: str) -> PyPIInfo | None:
    """Return information extracted from PyPI"""
    response = HTTP.request("GET", f"https://pypi.org/pypi/{package}/json")
    if response.status != 200:
        return None

    data = json.loads(response.data.decode("utf-8"))
    try:
        repository_url = data["info"]["project_urls"]["Repository"]
    except KeyError:
        return None

    try:
        releases = tuple(data["releases"].keys())
    except KeyError:
        releases = (())
    sorted_releases = sorted(releases, key=StrictVersion)
    try:
        latest_release = sorted_releases[-1]
    except IndexError:
        latest_release = None

    return PyPIInfo(url=repository_url, latest_release=latest_release)
