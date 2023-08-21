"""This module contains the implementation for building docsets from the built documentation"""
import subprocess
from pathlib import Path

import structlog
from click import ClickException

from docset_builder.data_structures import DocBuildInfo

LOG = structlog.get_logger(mod="build_ds")


def build_docset(built_docs_dir: Path, docbuild_info: DocBuildInfo, docset_build_dir: Path) -> Path:
    """Build docset into `docset_build_dir` from docs in `build_docs_dir`"""
    LOG.info(
        "Build docset",
        built_docs_dir=built_docs_dir,
        docbuild_info=docbuild_info,
        docset_build_dir=docset_build_dir,
    )
    # doc2dash --index-page index.html
    #   ~/.local/share/docset-builder/repositories/arrow/docs/_build/html/
    run_args: tuple[str, ...] = ("doc2dash",)

    if docbuild_info.start_page:
        run_args += ("--index-page", docbuild_info.start_page)
    else:
        LOG.debug("Built without start page")

    # TODO Downsize icon:
    if docbuild_info.icon_path:
        run_args += ("--icon", str(docbuild_info.icon_path))
    else:
        LOG.debug("Built without icon")

    run_args += (str(built_docs_dir),)
    subprocess.run(run_args, cwd=docset_build_dir)
    for directory in docset_build_dir.iterdir():
        return directory
    raise ClickException(
        "There does not appear to have been built anything in the temporary build dir: "
        f"{docset_build_dir}"
    )
