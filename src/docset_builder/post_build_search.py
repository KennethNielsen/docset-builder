from pathlib import Path
from typing import Generator

from click import ClickException

from docset_builder.data_structures import DocBuildInfo


def _search_for_built_docs(docbuild_information: DocBuildInfo, local_repository: Path) -> Path:
    subdir_patterns = (("_build", "html"),)
    for subdir_pattern in subdir_patterns:
        for candidate in docs_potential_base_dirs(docbuild_information, local_repository):
            for dir_ in subdir_pattern:
                candidate /= dir_
            if candidate.exists():
                return candidate
    raise ClickException(
        f"Unable to find dir with built docs amongst candidates: {subdir_patterns}"
    )


def docs_potential_base_dirs(
    docbuild_information: DocBuildInfo, local_repository: Path
) -> Generator[Path, None, None]:
    """Return a generator of potential docs build locations"""
    # First yield the basedir for building docs as a guess
    yield docbuild_information.basedir_for_building_docs

    # Then try "doc" and "docs" folders
    for guess_doc_dir in ("doc", "docs"):
        guess = local_repository / guess_doc_dir
        if guess.exists():
            yield guess

    # Then try all folders
    yield from local_repository.rglob("")
