from fury_api.lib.exceptions import FuryAPIError

__all__ = [
    "ConversationError",
    "MessageError",
]


class ConversationError(FuryAPIError):
    pass


class MessageError(FuryAPIError):
    pass
