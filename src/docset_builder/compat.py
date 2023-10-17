# ruff: noqa: F401
"""This module contains import compatability hacks"""

try:
    from typing import TypeAlias  # type: ignore
except ImportError:
    from typing_extensions import TypeAlias


__all__ = ["TypeAlias"]
