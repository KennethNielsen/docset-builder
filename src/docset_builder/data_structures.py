"""This module implements shared data structures"""

from pathlib import Path
from typing import Tuple

from attr import frozen


@frozen
class PyPIInfo:
    """PyPI information about package"""

    repository_url: str | None = None
    latest_release: str | None = None

    def missing_information_keys(self) -> Tuple[str, ...]:
        """Return the names of missing pieces of information, if any"""
        # In lieu of class variables https://github.com/python-attrs/attrs/issues/220 we
        # just store the required keys kere
        necessary_keys: tuple[str] = ("repository_url",)
        return tuple(k for k in necessary_keys if getattr(self, k) is None)


@frozen
class DocBuildInfo:
    """Build information"""

    docdir: Path = None
    deps: tuple[str, ...] = None
    commands: tuple[str, ...] = None
    icon_path: Path = None
    start_page: str = None

    def is_complete(self) -> bool:
        """Return whether the information is complete to proceed"""
        return all((self.docdir, self.deps, self.commands, self.icon_path))
