"""This module implements the main cli interface"""
import logging
from pathlib import Path
from typing import Sequence

import click
import structlog

from .core import install as core_install
from .directories import log_cache_dirs
from .logging_configuration import configure

configure()
LOG = structlog.get_logger(mod="main")


@click.group()  # This functions works as a grouping mechanism for the cli sub-commands
def cli() -> None:
    """Fancy new cli"""
    pass


def config_verbosity(verbose: bool, very_verbose: bool) -> None:
    """Configure loggers according to whether `verbose` is set"""
    if very_verbose:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.CRITICAL
    LOG.debug("Set log level", log_level=level)
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(level))
    # This is the one logging that should have happened at module level, but that would
    # defeat the verbosity settings, so instead it is wrapped in a function at called here
    log_cache_dirs()


@click.command()
@click.argument("packages", nargs=-1)
@click.option(
    "-b",
    "--build-only",
    default=False,
    is_flag=True,
)
@click.option(
    "-d",
    "--dump-test-files-to",
    default=None,
    type=Path,
)
@click.option(
    "-v",
    "--verbose",
    default=False,
    is_flag=True,
)
@click.option(
    "-vv",
    "--very-verbose",
    default=False,
    is_flag=True,
)
def install(
    packages: Sequence[str],
    build_only: bool,
    dump_test_files_to: Path | None,
    verbose: bool,
    very_verbose: bool,
) -> None:
    """Install docsets for one or more `packages`"""
    config_verbosity(verbose, very_verbose)
    LOG.info(
        "install",
        packages=packages,
        build_only=build_only,
        dump_test_files=dump_test_files_to,
    )
    core_install(packages, build_only=build_only, test_file_dump_path=dump_test_files_to)


cli.add_command(install)


if __name__ == "__main__":
    cli()
