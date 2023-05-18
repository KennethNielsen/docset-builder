"""This module implements the main cli interface"""
from pathlib import Path
from typing import Sequence

import click
import structlog

from .core import install as core_install

LOG = structlog.get_logger(mod="main")


@click.group()  # This functions works as a grouping mechanism for the cli sub-commands
def cli() -> None:
    """Fancy new cli"""
    pass


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
def install(
    packages: Sequence[str], build_only: bool, dump_test_files_to: Path | None
) -> None:
    """Install docsets for one or more `packages`"""
    LOG.msg(
        "install",
        packages=packages,
        build_only=build_only,
        dump_test_files=dump_test_files_to,
    )
    core_install(
        packages, build_only=build_only, test_file_dump_path=dump_test_files_to
    )


cli.add_command(install)


if __name__ == "__main__":
    cli()
