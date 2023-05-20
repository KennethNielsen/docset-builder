"""This module implements shared data structures"""
from json import dump
from pathlib import Path
from typing import Tuple, Mapping, cast, Dict

from attr import frozen, asdict
from typing_extensions import Self, TypedDict

from docset_builder.directories import REPOSITORIES_DIR


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

    def dump_test_file(self, dump_file_path: Path) -> None:
        """Dump this object to a JSON file for testing purposes"""
        with open(dump_file_path, "w") as file_:
            dump(asdict(self), file_, indent=4)

    @classmethod
    def from_dict(cls, data: Mapping[str, str]) -> Self:
        """Return a PyPIInfo object from `data`"""
        return cls(**data)


DocBuildInfoDict = TypedDict(
    "DocBuildInfoDict",
    {
        "docdir": str,
        "deps": list[str],
        "commands": list[str],
        "icon_path": str,
        "start_page": str,
    },
)


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

    def dump_test_file(self, dump_file_path: Path) -> None:
        """Dump this object to a JSON file for testing purposes"""
        data = asdict(self)
        data["docdir"] = str(data["docdir"].relative_to(REPOSITORIES_DIR))
        print(self)
        with open(dump_file_path, "w") as file_:
            dump(data, file_, indent=4)

    @classmethod
    def from_dict(cls, data: DocBuildInfoDict) -> Self:
        """Return DocBuildInfo from json `data`"""
        return cls(
            docdir = Path(data["docdir"]) if data["docdir"] else None,
            deps = tuple(data["deps"]) if data["deps"] else None,
            commands = tuple(data["commands"]) if data["commands"] else None,
            icon_path = Path(data["icon_path"]) if data["icon_path"] else None,
            start_page = data["start_page"],
        )
