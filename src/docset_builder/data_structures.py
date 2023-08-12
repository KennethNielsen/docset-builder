"""This module implements shared data structures"""
from json import dump
from pathlib import Path
from typing import Mapping, Tuple

from attr import asdict, frozen
from typing_extensions import Self, TypedDict

from docset_builder.directories import REPOSITORIES_DIR

# FIXME figure out if I can use annotated types to set required fields


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
    """Build information

    Attributes:
        basedir_for_building_docs (Path): The directory from which to build the docs
        deps (tuple[str]): The doc build dependencies
        commands (tuple[str]): Command that will build the docs
        icon_path (Path): Path of the project icon
        start_page (str): The name of the start page within the docbuild folder

    """

    basedir_for_building_docs: Path = None
    deps: tuple[str, ...] = None
    commands: tuple[str, ...] = None
    icon_path: Path = None
    start_page: str = None

    def missing_information_keys(self) -> Tuple[str, ...]:
        """Return the names of missing pieces of information, if any"""
        # In lieu of class variables https://github.com/python-attrs/attrs/issues/220 we
        # just store the required keys kere
        necessary_keys = ("basedir_for_building_docs", "deps", "commands")
        return tuple(k for k in necessary_keys if getattr(self, k) is None)

    def dump_test_file(self, dump_file_path: Path) -> None:
        """Dump this object to a JSON file for testing purposes"""
        data = asdict(self)
        data["basedir_for_building_docs"] = str(
            data["basedir_for_building_docs"].relative_to(REPOSITORIES_DIR)
        )
        print(self)
        with open(dump_file_path, "w") as file_:
            dump(data, file_, indent=4)

    @classmethod
    def from_dict(cls, data: DocBuildInfoDict) -> Self:
        """Return DocBuildInfo from json `data`"""
        return cls(
            basedir_for_building_docs=Path(data["basedir_for_building_docs"])
            if data["basedir_for_building_docs"]
            else None,
            deps=tuple(data["deps"]) if data["deps"] else None,
            commands=tuple(data["commands"]) if data["commands"] else None,
            icon_path=Path(data["icon_path"]) if data["icon_path"] else None,
            start_page=data["start_page"],
        )
