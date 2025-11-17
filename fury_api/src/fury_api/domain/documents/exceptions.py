from fury_api.lib.exceptions import FuryAPIError

__all__ = [
    "DocumentError",
    "DocumentContentError",
]


class DocumentError(FuryAPIError):
    pass


class DocumentContentError(FuryAPIError):
    pass
