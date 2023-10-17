"""A utility for extracting sections from a makefile"""

import re
from pathlib import Path

from attr import Factory, define

MAKEFILE_SECTIONS = r"([\.\w -]*): *(.*)?((?:\n\t.*)*)?"


@define
class _Section:
    name: str
    deps: list[str]
    lines: list[str] = Factory(list)


def extract_sections_from_makefile(makefile_path: Path) -> dict[str, list[str]]:  # noqa: C901
    """Extract sections from makefile and resolve dependencies"""
    with open(makefile_path) as file_:
        makefile_content = file_.read()

    sections = {}
    for match in re.findall(MAKEFILE_SECTIONS, makefile_content):
        name_group, deps_str, lines = match
        if lines == "":
            deps_str, lines = lines, deps_str
        lines = [line.strip() for line in lines.strip().split("\n")]
        deps = deps_str.split(" ") if deps_str else []

        for name in re.findall(r"[\.\w-]+", name_group.strip()):
            sections[name] = _Section(name, deps, lines)

    # Resolve dependencies
    while True:
        some_left_to_resolve = False
        for name, section in sections.items():
            some_left_to_resolve = some_left_to_resolve or bool(section.deps)
            while section.deps:
                dep_to_resolve = section.deps[-1]
                dependency_section = sections[dep_to_resolve]
                # Before adding dependencies, make sure they are resolved
                if dependency_section.deps:
                    break
                section.lines = dependency_section.lines + section.lines
                section.deps = section.deps[:-1]

        if not some_left_to_resolve:
            break

    sections_just_lines = {name: section.lines for name, section in sections.items()}

    return sections_just_lines
