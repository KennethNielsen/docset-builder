"""This module contains the implementation of configuration"""
from pathlib import Path
from typing import Any


def __getattr__(name: str) -> Any:
    """Return configuration item `name`"""
    if name == "install_base_dir":
        return Path("~/").expanduser() / ".local" / "share" / "Zeal" / "Zeal" / "docsets"
    else:
        raise ValueError(f"Config key '{name} is not known")
