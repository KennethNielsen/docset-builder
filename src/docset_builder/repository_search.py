"""This module implements searching the repository for doc build information"""
import configparser
from pathlib import Path
from typing import Generator

import structlog
from attrs import evolve
from click import ClickException

from docset_builder.data_structures import DocBuildInfo
from docset_builder.overrides import DOC_BUILD_INFO_OVERRIDES

LOG = structlog.get_logger(mod="reposearch")


def get_docbuild_information(name: str, repository_path: Path) -> DocBuildInfo:
    """Return docbuild information"""
    LOG.info("Get docbuild information", name=name, repository_path=repository_path)
    docbuild_info = DOC_BUILD_INFO_OVERRIDES.get(name, DocBuildInfo())
    LOG.debug("Got overrides", docbuild_info=docbuild_info)

    tox_ini_path = repository_path / "tox.ini"
    if tox_ini_path.exists():
        LOG.debug("Found tox.ini file")
        docbuild_info = _extract_from_tox_ini(docbuild_info, tox_ini_path)

    docbuild_info = _add_start_page_info(
        repository_path=repository_path, docbuild_info=docbuild_info
    )

    return docbuild_info


def _extract_from_tox_ini(docbuild_info: DocBuildInfo, tox_ini_path: Path) -> DocBuildInfo:
    """Return a `docbuild_info` with information (possibly) added from .tox file"""
    logger = LOG.bind(source="tox.ini")
    config_parser = configparser.ConfigParser()
    config_parser.read(tox_ini_path)

    # Extract docs section, if any
    for section in config_parser:
        if "docs" in section:
            break
    else:
        return docbuild_info

    doc_section = config_parser[section]

    # Update docdir
    if (changedir := doc_section.get("changedir")) and not docbuild_info.basedir_for_building_docs:
        logger.debug("Add docdir", docdir=changedir)
        docbuild_info = evolve(
            docbuild_info, basedir_for_building_docs=tox_ini_path.parent / changedir
        )

    # Update dependencies
    if (deps_string := doc_section.get("deps")) and not docbuild_info.deps:
        deps = tuple(deps_string.strip().split("\n"))
        logger.debug("Add deps", deps=deps)
        docbuild_info = evolve(docbuild_info, deps=deps)

    # Update build commands
    if (commands_string := doc_section.get("commands")) and not docbuild_info.commands:
        commands = tuple(commands_string.strip().split("\n"))
        logger.debug("Add commands", commands=commands)
        docbuild_info = evolve(docbuild_info, commands=commands)

    return docbuild_info


def _add_start_page_info(repository_path: Path, docbuild_info: DocBuildInfo) -> DocBuildInfo:
    """Return a `DocBuildInfo` with (possibly) added information about the docs start page"""
    if docbuild_info.start_page:
        return docbuild_info

    # This is a bit of a stretch, but for now simply look for Sphinx in the requirements and
    # if it is there, assume that the start page is "index.html"
    all_requirements: tuple[str, ...] = ()
    for requirement in docbuild_info.deps:
        if requirement.startswith("-r") and requirement.endswith(".txt"):
            requirement_path = repository_path / requirement.removeprefix("-r ")
            for requirement in _requirements_from_file(requirement_path):
                if requirement not in all_requirements:
                    all_requirements += (requirement,)
        else:
            if requirement not in all_requirements:
                all_requirements += (requirement,)

    depends_on_sphinx = any("sphinx" in r for r in all_requirements)
    if depends_on_sphinx:
        LOG.debug(
            "Found sphinx in requirements, assume main page is index.html",
            all_requirements=all_requirements,
        )
        docbuild_info = evolve(docbuild_info, start_page="index.html")

    return docbuild_info


def _requirements_from_file(requirement_path: Path) -> Generator[str, None, None]:
    """Return a generator of requirements from `requirements_path` (recursively)"""
    try:
        with open(requirement_path) as file_:
            for requirement in (r.strip() for r in file_.readlines()):
                if requirement.startswith("-r") and requirement.endswith(".txt"):
                    yield from _requirements_from_file(
                        requirement_path.parent / requirement.removeprefix("-r ")
                    )
                else:
                    yield requirement

    except OSError:
        LOG.error("UNABLE TO READ REQUIREMENTS FROM FILE", requirement_path=requirement_path)


def ensure_docbuild_info_is_sufficient(package_name: str, doc_build_info: DocBuildInfo) -> None:
    """Raise ClickException if `pypi_info` has insufficient info to proceed"""
    if missing_keys := doc_build_info.missing_information_keys():
        error_message = (
            "Unable to extract all necessary information from the repo to proceed\n"
            f"Got {doc_build_info}\n"
            f"Missing the following pieces of information: {missing_keys}\n"
            f"Consider improving the heuristic for extraction or writing an override "
            f"for this module: {package_name}"
        )
        raise ClickException(error_message)
