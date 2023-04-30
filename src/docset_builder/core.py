"""Toplevel functions for each of the primary tasks"""

import tempfile
from pathlib import Path
from typing import Sequence

import structlog

from .build_docsets import build_docset
from .pypi import get_information_for_package
from .docset_library import install_docset
from .repositories import clone_or_update
from .repository_search import get_docbuild_information
from .virtual_environments import build_docs

LOG = structlog.get_logger(mod="core")


def install(package_names: Sequence[str], build_only: bool = False) -> None:
    """Install docsets for `packages`"""

    for package_name in package_names:
        logger = LOG.bind(package=package_name)
        logger.msg("Installing")

        pypi_info = get_information_for_package(package_name)
        logger.msg("Retrieved pypi info", pypi_info=pypi_info)
        if missing_keys := pypi_info.missing_information_keys():
            print("Unable to extract all necessary information from PyPI to proceed")
            print(f"Got {pypi_info}")
            print(f"Missing the following pieces of information: {missing_keys}")
            print(
                f"Consider improving the heuristic for extraction or writing an override "
                f"for this module: {package_name}"
            )

        local_repository_path = clone_or_update(package_name, pypi_info=pypi_info)
        logger.msg("Local repository dir", dir=local_repository_path)

        docbuild_information = get_docbuild_information(package_name, local_repository_path)
        logger.msg("docbuild information", docbuild_information=docbuild_information)

        built_docs_dir = build_docs(
            name=package_name,
            local_repository=local_repository_path,
            docbuild_information=docbuild_information,
        )

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            docset_build_dir = build_docset(
                built_docs_dir=built_docs_dir,
                docset_build_dir=tmp_dir,
            )

            if not build_only:
                install_docset(docset_build_dir)
