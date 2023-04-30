"""This module implements the main cli interface"""
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
def install(packages: Sequence[str]) -> None:
    """Install docsets for one or more `packages`"""
    LOG.msg("install", packages=packages)
    core_install(packages)


cli.add_command(install)


if __name__ == "__main__":
    cli()
