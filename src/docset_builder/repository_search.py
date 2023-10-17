"""This module implements searching the repository for doc build information"""
import configparser
import itertools
from pathlib import Path
from typing import Generator

import structlog
import toml

from .data_structures import DocBuildInfo
from .overrides import DOC_BUILD_INFO_OVERRIDES
from .utils import extract_sections_from_makefile

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
    docbuild_info.package_name = name
    LOG.debug("Got overrides", docbuild_info=docbuild_info)

    docbuild_info = _add_all_requirements(docbuild_info, repository_path)

    tox_ini_path = repository_path / "tox.ini"
    if tox_ini_path.exists():
        LOG.debug("Found tox.ini file")
        docbuild_info = _extract_from_tox_ini(docbuild_info, tox_ini_path)

    make_file_path = repository_path / "Makefile"
    if make_file_path.exists() and docbuild_info.missing_information_keys():
        LOG.debug("Found Makefile")
        docbuild_info = _extract_from_makefile(docbuild_info, make_file_path, repository_path)

    docbuild_info = _add_start_page_info(
        repository_path=repository_path, docbuild_info=docbuild_info
    )
    docbuild_info = _add_icon_file(repository_path=repository_path, docbuild_info=docbuild_info)

    # docbuild_info = _look_for_docs_dir(repository_path=repository_path,
    # docbuild_info=docbuild_info)

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
        deps = ["tox"]
        logger.debug("Add doc build command deps", deps=deps)
        docbuild_info.doc_build_command_deps = deps

    # Update build commands
    if not docbuild_info.doc_build_commands:
        if ":" in section:
            tox_env_name = section.split(":")[1]
        else:
            tox_env_name = section
        commands = [f"tox -e {tox_env_name}"]
        logger.debug("Add commands", commands=commands)
        docbuild_info.doc_build_commands = commands

    return docbuild_info


def _extract_from_makefile(
    docbuild_info: DocBuildInfo, make_file_path: Path, repository_path: Path
) -> DocBuildInfo:
    logger = LOG.bind(source="Makefile")
    sections = extract_sections_from_makefile(make_file_path)
    commands = []
    for section_name in ("docs-init", "docs"):
        commands += sections.get(section_name, [])

    # Update doc build dependencies
    if docbuild_info.doc_build_commands is None:
        logger.debug("Add doc build commands", commands=commands)
        docbuild_info.doc_build_commands = commands

    if docbuild_info.doc_build_command_deps is None:
        logger.debug("Set docbuild command deps to no deps")
        docbuild_info.doc_build_command_deps = docbuild_info.all_deps

    if docbuild_info.basedir_for_building_docs is None:
        logger.debug("Add basedir for building docs", basedir_for_building_docs=repository_path)
        docbuild_info.basedir_for_building_docs = repository_path

    return docbuild_info


def _add_all_requirements(doc_build_info: DocBuildInfo, repository_path: Path) -> DocBuildInfo:
    """Add all requirements from requirements files, is requirements are missing"""
    if doc_build_info.all_deps:
        return doc_build_info

    all_dependencies = []
    all_requirements_files = itertools.chain(
        repository_path.rglob("requirements*.txt"),
        (repository_path / "requirements").glob("*.txt"),
    )
    for file_path in all_requirements_files:
        for requirement in _requirements_from_file(file_path):
            all_dependencies.append(requirement)

    if (pyproject_path := repository_path / "pyproject.toml").exists():
        with open(pyproject_path) as file_:
            pyproject = toml.load(file_)
        try:
            all_dependencies += pyproject["project"]["dependencies"]
        except KeyError:
            pass

        try:
            for section_name, dependencies in pyproject["project"]["optional-dependencies"].items():
                all_dependencies += dependencies
        except KeyError:
            pass

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


def _look_for_docs_dir(repository_path: Path, docbuild_info: DocBuildInfo) -> DocBuildInfo:
    """Look for a "docs" dir and add information from that"""
    if not docbuild_info.missing_information_keys():
        return docbuild_info

    LOG.error("UGLY docs dir FALLBACK")

    for docdir_name in ("docs", "doc", "documentation"):
        if not (docdir_path := repository_path / docdir_name).exists():
            continue

        if not all((docdir_path / filename).exists() for filename in ("conf.py", "Makefile")):
            continue

        with open(docdir_path / "Makefile") as file_:
            if "sphinx" not in file_.read():
                continue

        docbuild_info.basedir_for_building_docs = docdir_path
        docbuild_info.doc_build_command_deps = docbuild_info.all_deps
        docbuild_info.doc_build_commands = ["make html"]

    return docbuild_info
