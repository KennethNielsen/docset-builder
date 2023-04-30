"""This module contains information overrides for specific modules"""
from typing import Mapping

from frozendict import frozendict

from docset_builder.data_structures import PyPIInfo, DocBuildInfo


# Fill into overrides in these data structures when needed
PYPI_OVERRIDES: Mapping[str, PyPIInfo] = frozendict()
DOC_BUILD_INFO_OVERRIDES: Mapping[str, DocBuildInfo] = frozendict()
