"""This module contains commonly used modules"""

from pathlib import Path

import structlog
from appdirs import user_config_dir, user_data_dir

TEAM_NAME = "docset-builder-team"
APPLICATION_NAME = "docset-builder"

LOG = structlog.get_logger(mod="cache")


BASE_CACHE_DIR = Path(user_data_dir(APPLICATION_NAME, TEAM_NAME))
BASE_CACHE_DIR.mkdir(exist_ok=True)
PYPI_CACHE_DIR = BASE_CACHE_DIR / "pypi"
PYPI_CACHE_DIR.mkdir(exist_ok=True)
REPOSITORIES_DIR = BASE_CACHE_DIR / "repositories"
REPOSITORIES_DIR.mkdir(exist_ok=True)
VENV_DIR = BASE_CACHE_DIR / "venvs"
VENV_DIR.mkdir(exist_ok=True)

CONFIG_DIR = Path(user_config_dir(APPLICATION_NAME, TEAM_NAME))
CONFIG_DIR.mkdir(exist_ok=True)
INSTALLED_DOCSETS_INDEX = CONFIG_DIR / "installed_docsets.json"


def log_cache_dirs() -> None:
    """Log the cache dirs"""
    LOG.info(
        "cache dirs",
        base=BASE_CACHE_DIR,
        pypi=PYPI_CACHE_DIR,
        repo=REPOSITORIES_DIR,
        venv=VENV_DIR,
    )
