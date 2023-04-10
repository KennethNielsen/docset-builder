"""Cache implementation"""
import json
from pathlib import Path

import structlog
from attrs import define, asdict

from .pypi import get_information_for_package, PyPIInfo
from .directories import PYPI_CACHE_DIR

LOG = structlog.get_logger(mod="cache")




@define
class LocalRepository:
    path: Path
    exists: bool

def get_pypi_info(package_name, _get_from_pypi_function=get_information_for_package) -> PyPIInfo:
    """Return PyPi information"""
    cache_path = PYPI_CACHE_DIR / f"{package_name}.json"
    if cache_path.is_file():
        LOG.msg("pypi cache hit", package_name=package_name)
        with open(cache_path) as file_:
            return PyPIInfo(**json.load(file_))

    LOG.msg("pypi cache miss, get from PyPI")
    pypi_info = _get_from_pypi_function(package_name)
    if pypi_info:
        with open(cache_path, "w") as file_:
            json.dump(asdict(pypi_info), file_)

    return pypi_info


def get_icon_path_from_url(package_name, url):
    return url

