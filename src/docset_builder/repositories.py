"""This module handles manipulation of (git) repositories"""
import re
import subprocess
from functools import partial
from pathlib import Path
from typing import Callable, cast

import structlog
from structlog import BoundLogger

from .data_structures import PyPIInfo
from .directories import REPOSITORIES_DIR

LOG = structlog.get_logger(mod="repos")


def clone_or_update(name: str, pypi_info: PyPIInfo) -> tuple[Path, str]:
    """Clone of update the package repository"""
    logger = LOG.bind(name=name)
    logger.info("Clone and/or update")

    repository_dir = REPOSITORIES_DIR / name
    if not repository_dir.exists():
        _clone_repository(repository_dir, pypi_info, logger)
    checked_out_tag = update_repository(repository_dir, logger)
    return repository_dir, checked_out_tag


def _clone_repository(repository_dir: Path, pypi_info: PyPIInfo, _logger: BoundLogger) -> None:
    """Clone the repository"""
    _logger.info("Clone", dir=repository_dir)
    # TODO check out packages for git interaction
    result = subprocess.run(
        # Do a partial clone, filtering out blobs, to save on initial clone time
        # NOTE: Support for partial clones of submodules seems scetchy at present:
        # https://stackoverflow.com/questions/2144406/how-to-make-shallow-git-submodules/47374702#47374702
        # so for now, don't do them
        ["git", "clone", "--recurse-submodules", "--filter=blob:none", pypi_info.repository_url],
        cwd=repository_dir.parent,
    )
    result.check_returncode()


def update_repository(repository_dir: Path, _logger: BoundLogger) -> str:
    """Update the repository at `repository_dir`"""
    _logger.info("Update", repoitory_dir=repository_dir)
    run = partial(subprocess.run, cwd=repository_dir)
    silent_run = partial(run, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check_output = cast(
        Callable[[list[str]], bytes], partial(subprocess.check_output, cwd=repository_dir)
    )

    # Get the name of primary branch
    full_primary_branch_name = check_output(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
    )
    # Example: refs/remotes/origin/main
    primary_branch_name = full_primary_branch_name.strip().decode("utf-8").split("/")[-1]
    _logger.info(
        "Detected primary branch name, now check it out", primary_branch_name=primary_branch_name
    )
    result = silent_run(["git", "checkout", primary_branch_name])
    result.check_returncode()

    # Fetch new objects from upstream and update repo
    result = run(["git", "fetch", "origin"])
    result.check_returncode()

    # Reset at upstream head
    result = silent_run(["git", "reset", "--hard", f"origin/{primary_branch_name}"])
    result.check_returncode()
    _logger.debug("Primary branch reset at head of upstream primary branch")

    # submodules = check_output("git submodule")
    # print(repr(submodules))
    result = silent_run(["git", "submodule", "update"])
    result.check_returncode()

    # Check out last release
    tags_raw = check_output(["git", "tag"])
    tags = reversed(tags_raw.decode("utf-8").strip().split())
    for tag in tags:
        if is_version_like(tag, _logger):
            _logger.debug("Found last release tag, now check it out", tag=tag)
            break
    else:
        _logger.info("UNABLE TO FIND RELEASE TAG; PROCEED WITH HEAD")
        return "HEAD"

    result = silent_run(["git", "checkout", tag])
    result.check_returncode()
    result = silent_run(["git", "submodule", "update"])
    result.check_returncode()

    return tag


def is_version_like(tag: str, _logger: BoundLogger) -> bool:
    """Return whether `tag` looks like a version"""
    for regular_expression in (r"^v\d.*$", r"^\d*?\.\d*.*?\d*?$"):
        if re.match(regular_expression, tag):
            _logger.info("Matched release tag", re=regular_expression, tag=tag)
            return True
    return False


if __name__ == "__main__":
    update_repository(
        Path("/home/kenneth/.local/share/docset-builder/repositories/arrow"),
        LOG,
    )
