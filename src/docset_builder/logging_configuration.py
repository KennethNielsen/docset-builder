"""This module configures the logging"""
from typing import Any, MutableMapping

import structlog
from structlog.dev import RESET_ALL, YELLOW, ConsoleRenderer

from .compat import TypeAlias

EventDict: TypeAlias = MutableMapping[str, Any]


class ConsoleRendererWithModule(ConsoleRenderer):
    """ConsoleRenderer which includes the module in the format

    The module (given by the 'mod' key in the event_dict) and it is placed after the date time

    """

    def __call__(self, logger: structlog.PrintLogger, log_level: str, event_dict: EventDict) -> str:
        """Return the log string to be displayed"""
        module = event_dict.pop("mod", "N/A")
        original_string = super().__call__(logger, log_level, event_dict)
        # original_string is something like:
        # 2023-05-27 21:40:17 [info     ] Hi
        # But keep in mind that there are color format markers in there as well, so it is
        # not feasible to search for [
        date, time, rest = original_string.split(" ", 2)
        return f"{date} {time} {YELLOW}{module: <10}{RESET_ALL} {rest}"


def configure() -> None:
    """Configure structlog with a consoler renderer that displays the module"""
    console_renderer_with_module = ConsoleRendererWithModule()
    processors = structlog.get_config()["processors"]
    processors[-1] = console_renderer_with_module
    structlog.configure(processors=processors)
