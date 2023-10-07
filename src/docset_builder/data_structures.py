"""This module implements shared data structures"""
from json import dump
from pathlib import Path
from typing import Mapping, Tuple, Optional

from attr import asdict, define
from click import ClickException
from typing_extensions import Self, TypedDict

from docset_builder.directories import REPOSITORIES_DIR


# FIXME figure out if I can use annotated types to set required fields


@define
class PyPIInfo:
    """PyPI information about package"""

    package_name: Optional[str] = None
    repository_url: Optional[str] = None
    latest_release: Optional[str] = None

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

    def ensure_pypi_info_is_sufficient(self) -> None:
        """Raise ClickException if `pypi_info` has insufficient info to proceed"""
        if missing_keys := self.missing_information_keys():
            error_message = (
                "Unable to extract all necessary information from PyPI to proceed\n"
                f"Got {self}\n"
                f"Missing the following pieces of information: {missing_keys}\n"
                f"Consider improving the heuristic for extraction or writing an override "
                f"for this module: {self.package_name}"
            )
            raise ClickException(error_message)


DocBuildInfoDict = TypedDict(
    "DocBuildInfoDict",
    {
        "basedir_for_building_docs": str,
        "deps": list[str],
        "commands": list[str],
        "icon_path": str,
        "start_page": str,
    },
)


@define
class DocBuildInfo:
    """Build information

    Attributes:
        basedir_for_building_docs (Path): The directory from which to build the docs
        doc_build_command_deps (tuple[str]): The doc build dependencies
        doc_build_commands (tuple[str]): Command that will build the docs
        all_deps (list[str]): All dependencies found
        use_icon (bool): Indicate whether an icon should be used
        icon_path (Path): Path of the project icon
        start_page (str): The name of the start page within the docbuild folder

    """

    basedir_for_building_docs: Path = None
    doc_build_command_deps: list[str, ...] = None
    doc_build_commands: list[str, ...] = None
    all_deps: list[str, ...] = None
    use_icon: bool = False
    icon_path: Path = None
    start_page: str = None

    def missing_information_keys(self) -> Tuple[str, ...]:
        """Return the names of missing pieces of information, if any"""
        # In lieu of class variables https://github.com/python-attrs/attrs/issues/220 we
        # just store the required keys kere
        necessary_keys = [
            "basedir_for_building_docs",
            "doc_build_command_deps",
            "doc_build_commands",
            "start_page",
        ]
        if self.needs_icon:
            necessary_keys.append("icon_path")
        return tuple(k for k in necessary_keys if getattr(self, k) is None)

    @property
    def needs_icon(self) -> bool:
        return self.use_icon and self.icon_path is None

    def dump_test_file(self, dump_file_path: Path) -> None:
        """Dump this object to a JSON file for testing purposes"""
        data = asdict(self)
        data["basedir_for_building_docs"] = str(
            data["basedir_for_building_docs"].relative_to(REPOSITORIES_DIR)
        )
        with open(dump_file_path, "w") as file_:
            dump(data, file_, indent=4)

    @classmethod
    def from_dict(cls, data: DocBuildInfoDict) -> Self:
        """Return DocBuildInfo from json `data`"""
        raise NotImplementedError  # Update lates
        return cls(
            basedir_for_building_docs=Path(data["basedir_for_building_docs"])
            if data["basedir_for_building_docs"]
            else None,
            doc_build_command_deps=tuple(data["deps"]) if data["deps"] else None,
            doc_build_commands=tuple(data["commands"]) if data["commands"] else None,
            icon_path=Path(data["icon_path"]) if data["icon_path"] else None,
            start_page=data["start_page"],
        )
