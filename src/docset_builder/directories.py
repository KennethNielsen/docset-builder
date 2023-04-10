"""This module contains commonly used modules"""

from pathlib import Path
from appdirs import user_data_dir
import structlog

LOG = structlog.get_logger(mod="cache")


BASE_CACHE_DIR = Path(user_data_dir("docset-builder", "docset-builder-team"))
BASE_CACHE_DIR.mkdir(exist_ok=True)
PYPI_CACHE_DIR = BASE_CACHE_DIR / "pypi"
PYPI_CACHE_DIR.mkdir(exist_ok=True)
REPOSITORIES_DIR = BASE_CACHE_DIR / "repositories"
REPOSITORIES_DIR.mkdir(exist_ok=True)
LOG.msg("cache dirs", base=BASE_CACHE_DIR, pypi=PYPI_CACHE_DIR, repo=REPOSITORIES_DIR)
