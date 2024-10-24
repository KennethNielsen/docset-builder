"""This module extracts information from PyPI"""

import re
from types import ModuleType
from typing import Any, Dict, Protocol

import structlog
import urllib3
from click import ClickException
from packaging import version

from docset_builder.cache import cache_pypi_info, load_pypi_info
from docset_builder.data_structures import PyPIInfo
from docset_builder.overrides import PYPI_OVERRIDES

LOG = structlog.get_logger(mod="pypi")
HTTP = urllib3.PoolManager()


GITHUB_PROJECT_URL = r"^https:\/\/github\.com\/\w*?\/\w*?$"


class LoadPyPIInfo(Protocol):
    """Mypy function signature for load_pypi_info"""

    def __call__(self, package_name: str) -> PyPIInfo:  # noqa
        ...


class CachePyPIInfo(Protocol):
    """Mypy function signature for cache_pypi_info"""

    def __call__(self, package_name: str, pypi_info: PyPIInfo) -> None:  # noqa
        ...


def get_information_for_package(
    package_name: str,
    use_cache: bool = True,
    _load_pypi_info: LoadPyPIInfo = load_pypi_info,
    _cache_pypi_info: CachePyPIInfo = cache_pypi_info,
    _urllib3: ModuleType = urllib3,
) -> PyPIInfo:
    """Return information extracted from PyPI"""
    if use_cache and (pypi_info := _load_pypi_info(package_name=package_name)):
        LOG.info("Return pypi info from cache", pypi_info=pypi_info)
        return pypi_info

    pypi_info_url = f"https://pypi.org/pypi/{package_name}/json"
    response = urllib3.request("GET", pypi_info_url)
    if response.status != 200:
        raise ClickException(
            f"Unable to get information for '{package_name}' from PyPI. Attempted to get it at "
            f"URL: {pypi_info_url}. Got error statue code {response.status}"
        )

    pypi_info_json = response.json()

    # Get possible overrides
    pypi_info = PYPI_OVERRIDES.get(package_name, PyPIInfo())
    pypi_info.package_name = package_name
    LOG.debug("PyPI overrides", pypi_info=pypi_info)
    pypi_info = extract_information_from_pypi(pypi_info=pypi_info, pypi_info_json=pypi_info_json)

    _cache_pypi_info(package_name=package_name, pypi_info=pypi_info)
    LOG.debug("PyPI info assembled and cached")

    return pypi_info


def is_repository_url(repository_url: str) -> bool:
    """Check whether a URL is a git cloneable link"""
    # As a quick hack, for now, just check if the URL has the structure of a GitHub project
    return re.match(GITHUB_PROJECT_URL, repository_url) is not None


def extract_information_from_pypi(pypi_info: PyPIInfo, pypi_info_json: Dict[str, Any]) -> PyPIInfo:
    """Return new `pypi_info` with information extract from PyPI `response`"""
    # Extract repository url
    if pypi_info.repository_url is None:
        for key in ("Repository", "Source Code", "Source", "Homepage"):
            try:
                repository_url = pypi_info_json["info"]["project_urls"][key]
            except KeyError:
                continue

            if key == "Homepage" and not is_repository_url(repository_url):
                continue

            pypi_info.repository_url = repository_url
            LOG.debug("Added repository url", key=key, repository_url=repository_url)
            break

    # Extract latest release
    if pypi_info.latest_release is None:
        try:
            releases = tuple(pypi_info_json["releases"].keys())
        except KeyError:
            releases = ()
        sorted_releases = sorted(releases, key=version.parse)

        try:
            latest_release = sorted_releases[-1]
        except IndexError:
            pass
        else:
            LOG.debug("Added latest release", latest_release=latest_release)
            pypi_info.latest_release = latest_release

    return pypi_info
