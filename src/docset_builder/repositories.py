"""This module handles manipulation of (git) repositories"""

import subprocess
from pathlib import Path

import structlog

from .data_structures import PyPIInfo
from .directories import REPOSITORIES_DIR

LOG = structlog.get_logger(mod="repos")


def clone_or_update(name: str, pypi_info: PyPIInfo) -> Path:
    """Clone of update the package repository"""
    logger = LOG.bind(name=name, pypi_info=pypi_info)
    logger.msg("Clone or update")

    repository_dir = REPOSITORIES_DIR / name
    if not repository_dir.exists():
        _clone_repository(repository_dir, pypi_info, logger)
    update_repository(repository_dir, logger)
    return repository_dir


def _clone_repository(repository_dir: Path, pypi_info: PyPIInfo, _logger):
    """Clone the repository"""
    _logger.msg("Clone", dir=repository_dir)
    # TODO check out packages for git interaction of init time check for availability of git
    #  command
    result = subprocess.run(["git", "clone", pypi_info.repository_url], cwd=repository_dir.parent)
    result.check_returncode()


def update_repository(repository_dir: Path, _logger):
    _logger.msg("Update", repoitory_dir=repository_dir)
    result = subprocess.run(["git", "fetch", "origin"], cwd=repository_dir)
    result.check_returncode()
    # TODO check out last or specified release
    pass
