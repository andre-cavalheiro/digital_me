from fury_api.lib.exceptions import NotFoundError

__all__ = ["CollectionNotFoundError"]


class CollectionNotFoundError(NotFoundError):
    def __init__(self, collection_id: int):
        super().__init__(f"Collection with id {collection_id} not found")
