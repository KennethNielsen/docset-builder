"""This module contains functions for build the docs within a virtual environment"""
import os
import subprocess
from pathlib import Path
from typing import Optional

import structlog

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

    return


def _create_venv(venv_dir: Path) -> None:
    """Create virtual environments in `venv_dir`"""
    subprocess.check_call(
        # Important, for maximum compatibility, this has to point to a cPython, not merely
        # /usr/bin/env python3 which will point to pypy3 if installed
        f"/usr/bin/python3 -m venv {venv_dir}",
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True,
        executable="/bin/bash",
        env=os.environ.copy(),
    )


def _cmd_in_venv(venv_dir: Path, command: str, working_dir: Optional[Path] = None) -> None:
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
