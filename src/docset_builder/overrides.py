"""This module contains information overrides for specific modules"""
from typing import Mapping

from docset_builder.data_structures import DocBuildInfo, PyPIInfo

# Fill into overrides in these data structures when needed
PYPI_OVERRIDES: Mapping[str, PyPIInfo] = {}
DOC_BUILD_INFO_OVERRIDES: Mapping[str, DocBuildInfo] = {
    # arrow has a unicode char as their icon as part of the name
    "arrow": DocBuildInfo(use_icon=False),
}

# Note: No idea why mypy complains about the lines above
