"""This module contains the implementation of configuration"""
from pathlib import Path
from typing import Any


def __getattr__(name) -> Any:
    if name == "install_base_dir":
        return Path("~/").expanduser() / ".local" / "share" / "Zeal" / "Zeal" / "docsets"
    else:
        raise ValueError(f"Config key '{name} is not known")
