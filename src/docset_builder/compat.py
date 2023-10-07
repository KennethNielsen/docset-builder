"""This module contains import compatability hacks"""

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias