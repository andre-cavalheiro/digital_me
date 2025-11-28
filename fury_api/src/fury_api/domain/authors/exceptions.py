from fury_api.lib.exceptions import NotFoundError

__all__ = ["AuthorNotFoundError"]


class AuthorNotFoundError(NotFoundError):
    def __init__(self, author_id: int):
        super().__init__(f"Author with id {author_id} not found")
