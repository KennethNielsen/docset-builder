"""A utility for extracting sections from a makefile"""

import re
from pathlib import Path

from attr import Factory, define

MAKEFILE_SECTION_HEADER = re.compile(r"^([\w-]*):([\w ]*)$")


@define
class _Section:
    name: str
    deps: list[str]
    lines: list[str] = Factory(list)


def extract_sections_from_makefile(makefile_path: Path) -> dict[str, list[str]]:  # noqa: C901
    """Extract command sections from makefile at `makefile_path`"""
    # This is obviously sub-optimal, but I didn't find a tool that seemed well-used and
    # maintained at first glace
    with open(makefile_path) as file_:
        sections = {}
        current_section = None
        for line in file_:
            if line.strip() == "":
                continue

            if header_match := MAKEFILE_SECTION_HEADER.match(line):
                if current_section is not None:
                    sections[current_section.name] = current_section

                name, deps_str = header_match.groups()
                if deps_str.strip() != "":
                    deps = deps_str.strip().split(" ")
                else:
                    deps = []
                current_section = _Section(name, deps)
            else:
                if current_section:
                    current_section.lines.append(line.strip())
        if current_section:
            sections[current_section.name] = current_section

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
