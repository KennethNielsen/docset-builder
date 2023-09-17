"""This module implements searching the repository for doc build information"""
import configparser
from pathlib import Path
from typing import Generator

import structlog
from click import ClickException

from docset_builder.data_structures import DocBuildInfo
from docset_builder.overrides import DOC_BUILD_INFO_OVERRIDES

LOG = structlog.get_logger(mod="reposearch")
ICON_NAME_CANDIDATES = ("favicon.png",)


def _add_icon_file(repository_path: Path, docbuild_info: DocBuildInfo) -> DocBuildInfo:
    start_paths = [
        repository_path / p
        for p in ("doc", "docs")
        if (repository_path / p).exists() and (repository_path / p).is_dir()
    ]
    start_paths.append(repository_path)

    # Break-else-continue-break-else is ugly ass Python for break out of two loops
    for start_path in start_paths:
        for file_ in start_path.rglob("*"):
            if file_.name.lower() in ICON_NAME_CANDIDATES:
                break
        else:
            continue
        break
    else:
        return docbuild_info
    docbuild_info.icon_path = file_
    return docbuild_info


def get_docbuild_information(name: str, repository_path: Path) -> DocBuildInfo:
    """Return docbuild information"""
    LOG.info("Get docbuild information", name=name, repository_path=repository_path)
    docbuild_info = DOC_BUILD_INFO_OVERRIDES.get(name, DocBuildInfo())
    LOG.debug("Got overrides", docbuild_info=docbuild_info)

    tox_ini_path = repository_path / "tox.ini"
    if tox_ini_path.exists():
        LOG.debug("Found tox.ini file")
        docbuild_info = _extract_from_tox_ini(docbuild_info, tox_ini_path)

    docbuild_info = _add_all_requirements(docbuild_info, repository_path)

    docbuild_info = _add_start_page_info(
        repository_path=repository_path, docbuild_info=docbuild_info
    )
    docbuild_info = _add_icon_file(repository_path=repository_path, docbuild_info=docbuild_info)

    return docbuild_info


def _extract_from_tox_ini(docbuild_info: DocBuildInfo, tox_ini_path: Path) -> DocBuildInfo:
    """Return a `docbuild_info` with information (possibly) added from .tox file"""
    logger = LOG.bind(source="tox.ini")
    config_parser = configparser.ConfigParser()
    config_parser.read(tox_ini_path)

    toxinidir = tox_ini_path.parent

    # Extract docs section, if any
    for section in config_parser:
        if "docs" in section:
            break
    else:
        return docbuild_info

    doc_section = config_parser[section]

    # Update docdir
    if (changedir := doc_section.get("changedir")) and not docbuild_info.basedir_for_building_docs:
        logger.debug("Add basedir_for_building_docs", docdir=changedir)
        docbuild_info.basedir_for_building_docs = toxinidir / changedir
    else:
        docbuild_info.basedir_for_building_docs = toxinidir

    # Update doc build dependencies
    if not docbuild_info.doc_build_command_deps:
        deps = ("tox",)
        logger.debug("Add doc build command deps", deps=deps)
        docbuild_info.doc_build_command_deps = deps

    # Update build commands
    if not docbuild_info.doc_build_commands:
        if ":" in section:
            tox_env_name = section.split(":")[1]
        else:
            tox_env_name = section
        commands = (f"tox -e {tox_env_name}",)
        logger.debug("Add commands", commands=commands)
        docbuild_info.doc_build_commands = commands

    return docbuild_info


def _add_all_requirements(doc_build_info: DocBuildInfo, repository_path: Path) -> DocBuildInfo:
    """Add all requirements from requirements files, is requirements are missing"""
    if doc_build_info.all_deps:
        return doc_build_info

    all_dependencies = []
    for file_ in repository_path.rglob("requirements*.txt"):
        for requirement in _requirements_from_file(file_):
            all_dependencies.append(requirement)
    doc_build_info.all_deps = all_dependencies
    return doc_build_info


def _add_start_page_info(repository_path: Path, docbuild_info: DocBuildInfo) -> DocBuildInfo:
    """Return a `DocBuildInfo` with (possibly) added information about the docs start page"""
    if docbuild_info.start_page:
        return docbuild_info

    depends_on_sphinx = any("sphinx" in r for r in docbuild_info.all_deps)
    if depends_on_sphinx:
        LOG.debug(
            "Found sphinx in requirements, assume main page is index.html",
            all_requirements=docbuild_info.all_deps,
        )
        docbuild_info.start_page = "index.html"

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
