"""This module contains information overrides for specific modules"""
from typing import Mapping

from frozendict import frozendict

from docset_builder.data_structures import DocBuildInfo, PyPIInfo

# Fill into overrides in these data structures when needed
PYPI_OVERRIDES: Mapping[str, PyPIInfo] = frozendict()  # type: ignore
DOC_BUILD_INFO_OVERRIDES: Mapping[str, DocBuildInfo] = frozendict()  # type: ignore

# Note: No idea why mypy complains about the lines above
