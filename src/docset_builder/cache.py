"""Cache implementation"""
import json

import structlog
from attrs import asdict

from .data_structures import PyPIInfo
from .directories import PYPI_CACHE_DIR

LOG = structlog.get_logger(mod="cache")


def load_pypi_info(package_name: str) -> PyPIInfo | None:
    """Return PyPi information"""
    cache_path = PYPI_CACHE_DIR / f"{package_name}.json"
    if cache_path.is_file():
        LOG.msg("pypi cache hit", package_name=package_name)
        with open(cache_path) as file_:
            return PyPIInfo(**json.load(file_))
    LOG.msg("pypi cache miss", package_name=package_name)
    return None


def cache_pypi_info(package_name: str, pypi_info: PyPIInfo) -> None:
    """Cache the `pypi_info` for `package_name`"""
    cache_path = PYPI_CACHE_DIR / f"{package_name}.json"
    with open(cache_path, "w") as file_:
        json.dump(asdict(pypi_info), file_)
    LOG.msg("Cached pypi info", package_name=package_name, pypi_info=pypi_info)
