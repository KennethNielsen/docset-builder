"""Toplevel functions for each of the primary tasks"""

from typing import Sequence

import structlog

from .cache import get_pypi_info
from .repositories import clone_or_update
from .repository_search import get_docbuild_information


LOG = structlog.get_logger(mod="core")

def install(packages: Sequence[str]) -> None:
    """Install docsets for `packages`"""
    for package in packages:
        logger= LOG.bind(package=package)
        logger.msg("Installing")

        pypi_info = get_pypi_info(package)
        logger.msg("Retrieved pypi info", pypi_info=pypi_info)

        local_repository = clone_or_update(name=package, pypi_info=pypi_info)
        logger.msg("Local repository dir", dir=local_repository)

        docbuild_information = get_docbuild_information(package, local_repository)
        logger.msg("docbuild information", docbuild_information=docbuild_information)


    # Search for doc build and icon information
    # Build docs
    # Install into seal