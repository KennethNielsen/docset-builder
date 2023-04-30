"""This modules implements functions for docset library management"""
import json
import shutil
from pathlib import Path
from typing import cast

import structlog

from . import config
from .directories import INSTALLED_DOCSETS_INDEX

LOG = structlog.get_logger(mod="docset_library")


def install_docset(docset_build_dir: Path) -> None:
    """Install the built docset at `built_docs_dir`"""
    name = docset_build_dir.name
    install_base_dir = cast(Path, config.install_base_dir)
    install_dir = install_base_dir / name

    if install_dir.exists():
        LOG.msg("Removes ")
        shutil.rmtree(install_dir)

    shutil.move(docset_build_dir, install_base_dir)

    try:
        with open(INSTALLED_DOCSETS_INDEX) as file_:
            installed_docsets_index = json.load(file_)
    except FileNotFoundError:
        installed_docsets_index = {}

    installed_docsets_index[name] = "version"
    with open(INSTALLED_DOCSETS_INDEX, "w") as file_:
        json.dump(installed_docsets_index, file_)
