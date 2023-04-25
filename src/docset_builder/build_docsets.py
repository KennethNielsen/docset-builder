"""This module contains the implementation for building docsets from the built documentation"""
import subprocess
from pathlib import Path


def build_docset(built_docs_dir: Path, docset_build_dir: Path) -> Path:
    # doc2dash --index-page index.html
    #   ~/.local/share/docset-builder/repositories/arrow/docs/_build/html/
    subprocess.run(
        ["doc2dash", "--index-page", "index.html", str(built_docs_dir)],
        cwd=docset_build_dir
    )
    for directory in docset_build_dir.iterdir():
        return directory
    raise RuntimeError(
        "There does not appear to have been built anything in the temporary build dir: "
        f"{docset_build_dir}"
    )
