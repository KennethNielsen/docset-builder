"""This module extracts information from PyPI"""

import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Protocol

import structlog
import urllib3
from attrs import evolve
from click import ClickException
from packaging import version

from docset_builder.cache import cache_pypi_info, load_pypi_info
from docset_builder.data_structures import PyPIInfo
from docset_builder.overrides import PYPI_OVERRIDES

LOG = structlog.get_logger(mod="pypi")
HTTP = urllib3.PoolManager()


class LoadPyPIInfo(Protocol):
    """Mypy function signature for load_pypi_info"""

    def __call__(self, package_name: str) -> PyPIInfo:  # noqa
        ...


class CachePyPIInfo(Protocol):
    """Mypy function signature for cache_pypi_info"""

    def __call__(self, package_name: str, pypi_info: PyPIInfo) -> None:  # noqa
        ...


def get_information_for_package(
    package: str,
    package_test_dump_path: Path | None = None,
    use_cache: bool = True,
    _load_pypi_info: LoadPyPIInfo = load_pypi_info,
    _cache_pypi_info: CachePyPIInfo = cache_pypi_info,
    _urllib3: ModuleType = urllib3,
) -> PyPIInfo:
    """Return information extracted from PyPI"""
    if (
        use_cache
        and (pypi_info := _load_pypi_info(package_name=package))
        and not package_test_dump_path
    ):
        LOG.info("Return pypi info from cache", pypi_info=pypi_info)
        return pypi_info

    pypi_info_url = f"https://pypi.org/pypi/{package}/json"
    response = urllib3.request("GET", pypi_info_url)
    if response.status != 200:
        raise ClickException(
            f"Unable to get information for '{package}' from PyPI. Attempted to get it at "
            f"URL: {pypi_info_url}. Got error statue code {response.status}"
        )

    pypi_info_json = response.json()

    if package_test_dump_path:
        LOG.debug("Dumped raw PyPI info")
        with open(package_test_dump_path / "pypi_raw.json", "w") as file_:
            json.dump(pypi_info_json, file_)

    # Get possible overrides
    pypi_info = PYPI_OVERRIDES.get(package, PyPIInfo())
    LOG.debug("PyPI overrides", pypi_info=pypi_info)
    pypi_info = extract_information_from_pypi(pypi_info=pypi_info, pypi_info_json=pypi_info_json)

    _cache_pypi_info(package_name=package, pypi_info=pypi_info)
    LOG.debug("PyPI info assembled and cached")

    return pypi_info


def extract_information_from_pypi(pypi_info: PyPIInfo, pypi_info_json: Dict[str, Any]) -> PyPIInfo:
    """Return new `pypi_info` with information extract from PyPI `response`"""
    # Extract repository url
    print(pypi_info_json["info"]["project_urls"])
    if pypi_info.repository_url is None:
        for key in ("Repository", "Source Code", "Source"):
            try:
                repository_url = pypi_info_json["info"]["project_urls"][key]
            except KeyError:
                pass
            else:
                pypi_info = evolve(pypi_info, repository_url=repository_url)
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
            pypi_info = evolve(pypi_info, latest_release=latest_release)

    return pypi_info


def ensure_pypi_info_is_sufficient(package_name: str, pypi_info: PyPIInfo) -> None:
    """Raise ClickException if `pypi_info` has insufficient info to proceed"""
    if missing_keys := pypi_info.missing_information_keys():
        error_message = (
            "Unable to extract all necessary information from PyPI to proceed\n"
            f"Got {pypi_info}\n"
            f"Missing the following pieces of information: {missing_keys}\n"
            f"Consider improving the heuristic for extraction or writing an override "
            f"for this module: {package_name}"
        )
        raise ClickException(error_message)
