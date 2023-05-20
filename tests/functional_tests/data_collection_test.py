"""This module tests that data collections remain the same

This is the primary functional tests and the repository should contain data files for this
test for each of the modules that is supported. The data are collected by FIXME

"""
import json
from os import listdir
from pathlib import Path
from unittest.mock import Mock

from pytest import mark

from docset_builder.data_structures import PyPIInfo, DocBuildInfo
from docset_builder.directories import REPOSITORIES_DIR
from docset_builder.pypi import get_information_for_package
from docset_builder.repositories import clone_or_update
from docset_builder.repository_search import get_docbuild_information

THIS_DIR = Path(__file__).parent.resolve()
DATA_DIR = THIS_DIR / "data"
MODULES = listdir(DATA_DIR)


@mark.parametrize("package_name", MODULES)
def test_fetching_and_parsing_data_from_pypi(package_name):
    with open(DATA_DIR / package_name / "pypi_raw.json") as file_:
        json_from_request = json.load(file_)
    with open(DATA_DIR / package_name / "pypi.json") as file_:
        pypi_info_as_json = json.load(file_)
    expected_pypi_info = PyPIInfo.from_dict(pypi_info_as_json)

    mock_load_pypi_cache = Mock()
    mock_load_pypi_cache.return_value = None
    mock_cache_pypi_info = Mock()
    mock_response = Mock()
    mock_response.json.return_value = json_from_request
    mock_urllib = Mock()
    mock_urllib.request.return_value = mock_response

    pypi_info = get_information_for_package(
        package_name,
        _load_pypi_info=mock_load_pypi_cache,
        _cache_pypi_info=mock_cache_pypi_info,
        _urllib3=mock_urllib,
    )

    assert pypi_info == expected_pypi_info


@mark.parametrize("package_name", MODULES)
def test_getting_docbuild_information_from_repo(package_name):
    with open(DATA_DIR / package_name / "pypi.json") as file_:
        pypi_info_as_json = json.load(file_)
    pypi_info = PyPIInfo.from_dict(pypi_info_as_json)
    local_repository_path, checked_out_tag = clone_or_update(
        package_name, pypi_info=pypi_info
    )

    with open(DATA_DIR / package_name / "docbuild.json") as file_:
        docbuild_json = json.load(file_)
    docbuild_json["docdir"] = REPOSITORIES_DIR / docbuild_json["docdir"]
    docbuild_information_expected = DocBuildInfo.from_dict(docbuild_json)
    docbuild_information = get_docbuild_information(
        package_name, local_repository_path
    )
    assert docbuild_information == docbuild_information_expected