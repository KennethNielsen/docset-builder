"""Toplevel functions for each of the primary tasks

The procedure for bulding docsets is the following:

* Get information from PyPI about the package, most importantly the **source code repository
URL** and the **latest released version**
* Clone or update a local version of the repository
* Extract information from configuration files about how to build the docs, this for now
covers only searching tox.ini, but other configs will be added
* Build the docs, this consists of
  * Making a virtual environment for the package, if it does not already exist
  * Install / upgrade all dependencies for building the docs
  * Build the docs
  * Search for the build docs and return the location of the build docs
* Build the docset from the build docs
* Install (copy) the docset

"""

import tempfile
from pathlib import Path
from typing import Sequence

import structlog

from .build_docsets import build_docset
from .docset_library import install_docset
from .post_build_search import _search_for_built_docs
from .pypi import get_information_for_package
from .repositories import clone_or_update
from .repository_search import ensure_docbuild_info_is_sufficient, get_docbuild_information
from .virtual_environments import build_docs

LOG = structlog.get_logger(mod="core")


def install(
    package_names: Sequence[str],
    build_only: bool = False,
    test_file_dump_path: Path | None = None,
    use_cache: bool = True,
) -> None:
    """Install docsets for `packages`"""
    for package_name in package_names:
        logger = LOG.bind(package=package_name)
        logger.info("Installing", build_only=build_only, test_file_dump_path=test_file_dump_path)

        pypi_info = get_information_for_package(package_name, use_cache=use_cache)
        pypi_info.ensure_pypi_info_is_sufficient()
        logger.info("Got PyPI info", pypi_info=pypi_info)

        local_repository_path, checked_out_tag = clone_or_update(package_name, pypi_info=pypi_info)
        logger.info("Cloned and/or updated repo", dir=local_repository_path)

        docbuild_information = get_docbuild_information(
            package_name, repository_path=local_repository_path
        )
        logger.info("Got docbuild information", docbuild_information=docbuild_information)
        ensure_docbuild_info_is_sufficient(
            package_name=package_name, doc_build_info=docbuild_information
        )

        build_docs(
            package_name=package_name,
            local_repository=local_repository_path,
            docbuild_information=docbuild_information,
        )
        logger.info("Docs built")
        built_docs_dir = _search_for_built_docs(
            docbuild_information=docbuild_information, local_repository=local_repository_path
        )
        logger.info("Docs located", path=built_docs_dir)

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir = Path(tmp_dir_name)
            docset_build_dir = build_docset(
                built_docs_dir=built_docs_dir,
                docbuild_info=docbuild_information,
                docset_build_dir=tmp_dir,
            )
            logger.info("Docset built", docset_build_dir=docset_build_dir)

            if not build_only:
                install_docset(docset_build_dir)
                logger.info("Docset installed")
