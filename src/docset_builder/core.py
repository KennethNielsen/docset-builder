"""Toplevel functions for each of the primary tasks"""

import tempfile
from pathlib import Path
from typing import Sequence

import structlog

from .build_docsets import build_docset
from .docset_library import install_docset
from .pypi import ensure_pypi_info_is_sufficient, get_information_for_package
from .repositories import clone_or_update
from .repository_search import ensure_docbuild_info_is_sufficient, get_docbuild_information
from .virtual_environments import build_docs

LOG = structlog.get_logger(mod="core")


def install(
    package_names: Sequence[str],
    build_only: bool = False,
    test_file_dump_path: Path | None = None,
) -> None:
    """Install docsets for `packages`"""
    if test_file_dump_path:
        test_file_dump_path.mkdir(parents=True, exist_ok=True)
        LOG.debug("Create base dir for test file dump", test_file_dump_path=test_file_dump_path)

    for package_name in package_names:
        logger = LOG.bind(package=package_name)
        logger.info("Installing", build_only=build_only, test_file_dump_path=test_file_dump_path)

        if test_file_dump_path:
            package_test_dump_path = test_file_dump_path / package_name
            package_test_dump_path.mkdir(exist_ok=True)
            logger.debug("Created package test file dump dir", dump_dir=package_test_dump_path)
        else:
            package_test_dump_path = None

        pypi_info = get_information_for_package(
            package_name, package_test_dump_path=package_test_dump_path
        )
        logger.info("Got PyPI info", pypi_info=pypi_info)
        ensure_pypi_info_is_sufficient(package_name=package_name, pypi_info=pypi_info)

        if test_file_dump_path:
            dump_path = package_test_dump_path / "pypi.json"
            pypi_info.dump_test_file(dump_path)
            logger.debug("Dumped PyPI info", dump_path=dump_path)

        local_repository_path, checked_out_tag = clone_or_update(package_name, pypi_info=pypi_info)
        logger.info("Cloned and/or updated repo", dir=local_repository_path)

        docbuild_information = get_docbuild_information(
            package_name, repository_path=local_repository_path
        )
        logger.info("Got docbuild information", docbuild_information=docbuild_information)
        ensure_docbuild_info_is_sufficient(
            package_name=package_name, doc_build_info=docbuild_information
        )
        if test_file_dump_path:
            dump_path = package_test_dump_path / "docbuild.json"
            docbuild_information.dump_test_file(dump_path)
            logger.debug("DocBuildInfo for tests dumped", dump_path=dump_path)

        built_docs_dir = build_docs(
            package_name=package_name,
            local_repository=local_repository_path,
            docbuild_information=docbuild_information,
        )
        logger.info("Docs built", built_docs_dir=built_docs_dir)

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
