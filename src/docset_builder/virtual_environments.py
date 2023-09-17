"""This module contains functions for build the docs within a virtual environment"""
import os
import subprocess
from pathlib import Path
from typing import Generator

import structlog
from click import ClickException

from .data_structures import DocBuildInfo
from .directories import VENV_DIR

LOG = structlog.get_logger(mod="venvs")


def build_docs(
    package_name: str, local_repository: Path, docbuild_information: DocBuildInfo
) -> Path:
    """Build the docs"""
    venv_dir = VENV_DIR / package_name
    logger = LOG.bind(venv_dir=venv_dir)
    if not venv_dir.exists():
        logger.info("Create virtual env")
        _create_venv(venv_dir)

    for requirement in docbuild_information.doc_build_command_deps:
        if not (requirement.startswith("-r") and requirement.endswith(".txt")):
            requirement = f'"{requirement}"'
        logger.info("Install requirement", req=requirement)
        _cmd_in_venv(venv_dir, f"pip install --upgrade {requirement}", working_dir=local_repository)

    for command in docbuild_information.doc_build_commands:
        logger.info("Execute doc build command", cmd=command)
        _cmd_in_venv(venv_dir, command, working_dir=docbuild_information.basedir_for_building_docs)

    return _search_for_built_docs(docbuild_information, local_repository)


def _create_venv(venv_dir: Path) -> None:
    """Create virtual environments in `venv_dir`"""
    subprocess.check_call(
        f"/usr/bin/env python3 -m venv {venv_dir}",
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
        executable="/bin/bash",
        env=os.environ.copy(),
    )


def _cmd_in_venv(venv_dir: Path, command: str, working_dir: Path | None = None) -> None:
    activate = venv_dir / "bin" / "activate"
    subprocess.check_call(
        f"source {activate} && {command}",
        stdout=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
        executable="/bin/bash",
        env=os.environ.copy(),
        cwd=working_dir,
    )


def docs_potential_base_dirs(
    docbuild_information: DocBuildInfo, local_repository: Path
) -> Generator[Path, None, None]:
    """Return a generator of potential docs build locations"""
    # First yield the basedir for building docs as a guess
    yield docbuild_information.basedir_for_building_docs

    # Then try "doc" and "docs" folders
    for guess_doc_dir in ("doc", "docs"):
        guess = local_repository / guess_doc_dir
        if guess.exists():
            yield guess

    # Then try all folders
    yield from local_repository.rglob("")


# TODO Factor this out into its own file???
def _search_for_built_docs(docbuild_information: DocBuildInfo, local_repository: Path) -> Path:
    subdir_patterns = (("_build", "html"),)
    for subdir_pattern in subdir_patterns:
        for candidate in docs_potential_base_dirs(docbuild_information, local_repository):
            for dir_ in subdir_pattern:
                candidate /= dir_
            if candidate.exists():
                return candidate
    raise ClickException(
        f"Unable to find dir with built docs amongst candidates: {subdir_patterns}"
    )
