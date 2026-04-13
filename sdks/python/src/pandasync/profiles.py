"""Operational profiles for PandaSync devices."""

from enum import Enum


class Profile(Enum):
    """PandaSync operational profile.

    The same protocol runs underneath all profiles. The profile changes
    only which features are exposed and which defaults apply.
    """

    SIMPLE = "simple"
    BROADCAST = "broadcast"
    DEVELOPER = "developer"
