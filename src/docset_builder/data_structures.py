"""This module implements shared data structures"""
from contextlib import contextmanager
from json import dump
from pathlib import Path
from typing import Mapping, Optional, Tuple, TypeVar, cast, Iterator, Any

from attr import Attribute, asdict, define, field, fields
from click import ClickException
from rich.console import Console
from rich.table import Table
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

ValueType = TypeVar("ValueType")


def _on_setattr(
    instance: "DocBuildInfo", attribute: Attribute[ValueType], value: ValueType
) -> ValueType:
    """Enforce set-once-sourced behavior

    This function is called when certain attrs properties are set. Its purpose is to make sure
    that a property can only be set once and can only be set if the object knows the source of
    the set (as indicated by the `set_source` context manager).

    """
    if not instance._current_source:
        raise ValueError(
            f"Disallowed to set property '{attribute.name}' without source set. Please only set "
            "properties of this class inside the `set_source` context manager."
        )

    # Enforce set-once behavior by returning the existing value, if it has already been set
    if attribute.name in instance._sources:
        return cast(ValueType, getattr(instance, attribute.name))

    instance._sources[attribute.name] = instance._current_source
    return value


@define
class DocBuildInfo:
    """Build information

    Attributes:
        package_name (str): The name of the package
        basedir_for_building_docs (Path): The directory from which to build the docs
        doc_build_command_deps (tuple[str]): The doc build dependencies
        doc_build_commands (tuple[str]): Command that will build the docs
        all_deps (list[str]): All dependencies found
        use_icon (bool): Indicate whether an icon should be used
        icon_path (Path): Path of the project icon
        start_page (str): The name of the start page within the docbuild folder

    """

    package_name: Optional[str] = field(default=None, on_setattr=_on_setattr)
    basedir_for_building_docs: Optional[Path] = field(default=None, on_setattr=_on_setattr)
    doc_build_command_deps: Optional[list[str]] = field(default=None, on_setattr=_on_setattr)
    doc_build_commands: Optional[list[str]] = field(default=None, on_setattr=_on_setattr)
    all_deps: Optional[list[str]] = field(default=None, on_setattr=_on_setattr)
    use_icon: bool = field(default=False, on_setattr=_on_setattr)
    icon_path: Optional[Path] = field(default=None, on_setattr=_on_setattr)
    start_page: Optional[str] = field(default=None, on_setattr=_on_setattr)

    _sources: dict[str, str] = field(init=False, factory=dict, alias="_sources")
    _current_source: Optional[str] = field(init=False, default=None, alias="_current_source")

    def __attrs_post_init__(self) -> None:
        """Mark attributes set (different from default) during __init__ as overrides"""
        for field_ in fields(self.__class__):
            if field_.name.startswith("_"):
                continue
            if getattr(self, field_.name) != field_.default:
                self._sources[field_.name] = "[bold bright_blue]OVERRIDE[/bold bright_blue]"

    @contextmanager
    def set_source(self, source_name: str) -> Iterator["DocBuildInfo"]:
        """Set the information source to `source_name`within this context manager"""
        self._current_source = source_name
        yield self
        self._current_source = None

    def print_values_and_sources(self) -> None:
        """Print out the attribute names, values and source in a rich table"""
        table = Table(title=f"{self.__class__.__name__} Properties And Values")
        table.add_column("Name", justify="right", style="cyan", no_wrap=True)
        table.add_column("Value", style="magenta")
        table.add_column("Source", style="green")

        for field_ in fields(self.__class__):
            name = field_.name
            if name.startswith("_"):
                continue

            value = getattr(self, name)
            source = self._sources.get(name, "[bold red]NONE[/bold red]")
            table.add_row(name, str(value), source)

        console = Console()
        console.print(table)

    def missing_information_keys(self) -> Tuple[str, ...]:
        """Return the names of missing pieces of information, if any"""
        # In lieu of class variables https://github.com/python-attrs/attrs/issues/220 we
        # just store the required keys here
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
        """Return whether this package needs and icon to build the docs"""
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
        raise NotImplementedError  # Update later
        return cls(
            basedir_for_building_docs=Path(data["basedir_for_building_docs"])
            if data["basedir_for_building_docs"]
            else None,
            doc_build_command_deps=tuple(data["deps"]) if data["deps"] else None,
            doc_build_commands=tuple(data["commands"]) if data["commands"] else None,
            icon_path=Path(data["icon_path"]) if data["icon_path"] else None,
            start_page=data["start_page"],
        )

    def ensure_info_is_sufficient(self) -> None:
        """Raise ClickException if this object has insufficient info to proceed"""
        if missing_keys := self.missing_information_keys():
            error_message = (
                "Unable to extract all necessary information from the repo to proceed\n"
                f"Got {self}\n"
                f"Missing the following pieces of information: {missing_keys}\n"
                f"Consider improving the heuristic for extraction or writing an override "
                f"for this module: {self.package_name}"
            )
            raise ClickException(error_message)
