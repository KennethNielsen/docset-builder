"""This module implements searching the repository for doc build information"""
import configparser
from pathlib import Path
from typing import Generator

from attrs import evolve

from docset_builder.data_structures import DocBuildInfo
from docset_builder.overrides import DOC_BUILD_INFO_OVERRIDES


def get_docbuild_information(name: str, repository_path: Path) -> DocBuildInfo:
    """Return docbuild information"""
    docbuild_info = DOC_BUILD_INFO_OVERRIDES.get(name, DocBuildInfo())

    # NOTE when we add more sources, confirm if is_complete before continuing
    tox_ini_path = repository_path / "tox.ini"
    if tox_ini_path.exists():
        docbuild_info = _extract_from_tox_ini(docbuild_info, tox_ini_path)

    docbuild_info = _add_start_page_info(
        repository_path=repository_path, docbuild_info=docbuild_info
    )

    return docbuild_info


def _extract_from_tox_ini(docbuild_info: DocBuildInfo, tox_ini_path: Path) -> DocBuildInfo:
    """Return a `docbuild_info` with information (possibly) added from .tox file"""
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
    if (changedir := doc_section.get("changedir")) and not docbuild_info.docdir:
        docbuild_info = evolve(docbuild_info, docdir=tox_ini_path.parent / changedir)

    # Update dependencies
    if (deps := doc_section.get("deps")) and not docbuild_info.deps:
        docbuild_info = evolve(docbuild_info, deps=tuple(deps.strip().split("\n")))

    # Update build commands
    if (commands := doc_section.get("commands")) and not docbuild_info.commands:
        docbuild_info = evolve(docbuild_info, commands=tuple(commands.strip().split("\n")))

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
        docbuild_info = evolve(docbuild_info, start_page="index.html")

    return docbuild_info


def _requirements_from_file(requirement_path: Path) -> Generator[str, None, None]:
    """Return a generator of requirements from `requirements_path` (recursively)"""
    try:
        with open(requirement_path) as file_:
            for requirement in (r.strip() for r in file_.readlines()):
                if requirement.startswith("-r") and requirement.endswith(".txt"):
                    yield from _requirements_from_file(
                        requirement_path.parent / requirement.removesuffix("-r ")
                    )
                else:
                    yield requirement

    except OSError:
        # FIXME LOG
        print("UNABLE TO READ REQUIREMENTS FROM FILE")
        pass
