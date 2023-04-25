"""Toplevel functions for each of the primary tasks"""
import tempfile
from pathlib import Path
from typing import Sequence

import structlog

from .build_docsets import build_docset
from .cache import get_pypi_info
from .docset_library import install_docset
from .repositories import clone_or_update
from .repository_search import get_docbuild_information
from .virtual_environments import build_docs

LOG = structlog.get_logger(mod="core")


def install(packages: Sequence[str]) -> None:
    """Install docsets for `packages`"""
    for package in packages:
        logger = LOG.bind(package=package)
        logger.msg("Installing")

        pypi_info = get_pypi_info(package)
        logger.msg("Retrieved pypi info", pypi_info=pypi_info)

        local_repository = clone_or_update(name=package, pypi_info=pypi_info)
        logger.msg("Local repository dir", dir=local_repository)

        docbuild_information = get_docbuild_information(package, local_repository)
        logger.msg("docbuild information", docbuild_information=docbuild_information)

        built_docs_dir = build_docs(
            name=package,
            local_repository=local_repository,
            docbuild_information=docbuild_information,
        )

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            docset_build_dir = build_docset(
                built_docs_dir=built_docs_dir, docset_build_dir=tmp_dir,
            )

            install_docset(docset_build_dir)
        # print("BB", built_docs_dir)

    # Search for doc build and icon information
    # Build docs
    # Install into seal
