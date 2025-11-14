from fury_api.lib.exceptions import FuryAPIError

__all__ = [
    "PluginError",
]


class PluginError(FuryAPIError):
    pass
