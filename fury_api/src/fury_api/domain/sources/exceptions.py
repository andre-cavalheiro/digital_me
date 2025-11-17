from fury_api.lib.exceptions import FuryAPIError

__all__ = [
    "SourceError",
    "ContentError",
    "SourceGroupError",
    "SourceGroupMemberError",
    "DocumentSourceConfigError",
    "CitationError",
]


class SourceError(FuryAPIError):
    pass


class ContentError(FuryAPIError):
    pass


class SourceGroupError(FuryAPIError):
    pass


class SourceGroupMemberError(FuryAPIError):
    pass


class DocumentSourceConfigError(FuryAPIError):
    pass


class CitationError(FuryAPIError):
    pass
