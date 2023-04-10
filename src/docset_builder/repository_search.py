"""This module implements searching the repository for doc build information"""
import configparser
from pathlib import Path

from attrs import frozen, evolve

from .overrides import get_overrides

@frozen
class DocBuildInfo:
    """Build information"""
    docdir: Path = None
    deps: tuple[str] = None
    commands: tuple[str] = None
    icon_path : Path = None

    def is_complete(self):
        return all((self.docdir, self.deps, self.commands, self.icon_path))


def get_docbuild_information(name, repository_path: Path):
    """Return docbuild information"""
    overrides = get_overrides(name)
    docbuild_info = DocBuildInfo(**overrides)
    docbuild_info = _extract_docbuild_information(docbuild_info, repository_path)
    return docbuild_info


def _extract_docbuild_information(docbuild_info: DocBuildInfo, repository_path: Path) -> DocBuildInfo:
    tox_ini_path = repository_path / "tox.ini"
    if tox_ini_path.exists():
        docbuild_info = _extract_from_tox_ini(docbuild_info, tox_ini_path)
    # NOTE when we add more sources, confirm if is_complete before continuing
    return docbuild_info


def _extract_from_tox_ini(docbuild_info, tox_ini_path) -> DocBuildInfo:
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
        docbuild_info = evolve(docbuild_info, docdir= tox_ini_path.parent / changedir)

    # Update dependencies
    if (deps := doc_section.get("deps")) and not docbuild_info.deps:
        docbuild_info = evolve(docbuild_info, deps= deps.strip().split("\n"))

    # Update build commands
    if (commands := doc_section.get("commands")) and not docbuild_info.commands:
        docbuild_info = evolve(docbuild_info, commands = commands.strip().split("\n"))

    return docbuild_info