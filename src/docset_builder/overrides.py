"""This module contains information overrides for specific modules"""

from frozendict import frozendict

from .cache import get_icon_path_from_url


OVERRIDES = frozendict(
    arrow = {
        "icon_path": "https://em-content.zobj.net/thumbs/160/google/350/bow-and-arrow_1f3f9.png"
    }
)

def get_overrides(package_name):
    overrides = OVERRIDES.get(package_name, {})
    if icon_path := overrides.get("icon_path"):
        if icon_path.startswith("http"):
            overrides["icon_path"] = get_icon_path_from_url(package_name, icon_path)
    return overrides