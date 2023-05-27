"""This module configures the logging"""

import structlog
from structlog.dev import ConsoleRenderer, YELLOW, RESET_ALL

class ConsoleRendererWithModule(ConsoleRenderer):
    """ConsoleRenderer that patches the module (given by the 'mod' key in the event_dict)
    into the log string after the date time

    """

    def __call__(self, logger, log_level, event_dict):
        module = event_dict.pop("mod", "")
        original_string = super().__call__(logger, log_level, event_dict)
        # original_string is something like:
        # 2023-05-27 21:40:17 [info     ] Hi
        # But keep in mind that there are color format markers in there as well, so it is
        # not feasible to search for [
        date, time, rest = original_string.split(" ", 2)
        return f"{date} {time} {YELLOW}{module: <6}{RESET_ALL} {rest}"


def configure():
    """Configure structlog with a consolere renderer that displays the module"""
    console_renderer_with_module = ConsoleRendererWithModule()
    processors = structlog.get_config()["processors"]
    processors[-1] = console_renderer_with_module
    structlog.configure(processors=processors)
