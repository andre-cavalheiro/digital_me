from typing import Any
from collections.abc import Iterable
from .models import Author
from fury_api.domain.content.enums import Platform
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User
from fury_api.lib.service import SqlService, with_uow

__all__ = [
    "AuthorsService",
]


class AuthorsService(SqlService[Author]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Author, uow, auth_user=auth_user, **kwargs)

    @with_uow
    async def get_by_platform_id(
        self,
        *,
        platform: str,
        external_id: str,
    ) -> Author | None:
        return await self.repository.get_by_platform_id(self.session, platform=platform, external_id=external_id)

    @with_uow
    async def get_by_platform_handle(
        self,
        *,
        platform: str,
        handle: str,
    ) -> Author | None:
        """Get author by platform and handle (username)."""
        return await self.repository.get_by_platform_handle(self.session, platform=platform, handle=handle)

    def convert_x_author_payload(self, author_obj: Any) -> Author:
        """Convert X author object/dict to Author model."""
        # Handle both dict and Pydantic model/object
        if hasattr(author_obj, "model_dump"):
            data = author_obj.model_dump()
        elif hasattr(author_obj, "__dict__"):
            data = author_obj.__dict__
        else:
            data = author_obj

        if not isinstance(data, dict):
            # Fallback if we can't get a dict representation
            data = {}

        external_id = data.get("id")
        # If passed object has .id attribute but model_dump didn't catch it
        if not external_id and hasattr(author_obj, "id"):
            external_id = author_obj.id

        display_name = data.get("name") or ""
        handle = data.get("username") or ""
        avatar_url = data.get("profile_image_url") or ""
        profile_url = f"https://x.com/{handle}" if handle else ""

        # Extract metrics safely
        metrics = data.get("public_metrics", {})

        return Author(
            platform=Platform.X.value,
            external_id=external_id,
            display_name=display_name,
            handle=handle,
            avatar_url=avatar_url,
            profile_url=profile_url,
            bio=data.get("description"),
            follower_count=metrics.get("followers_count"),
            following_count=metrics.get("following_count"),
        )

    @with_uow
    async def ensure_x_author(
        self,
        *,
        author_data: Any,
    ) -> Author | None:
        """Ensure the author exists, create or update if needed."""
        # Extract ID to check existence first
        external_id = None
        if isinstance(author_data, dict):
            external_id = author_data.get("id")
        elif hasattr(author_data, "id"):
            external_id = author_data.id

        if not external_id:
            return None

        platform = Platform.X.value

        author = await self.get_by_platform_id(platform=platform, external_id=external_id)
        if not author:
            author_model = self.convert_x_author_payload(author_data)
            author = await self.create_item(author_model)

        return author

    @with_uow
    async def ensure_x_authors_batch(
        self,
        posts: Iterable[Any],
    ) -> dict[str, int]:
        """Make sure all authors exist and return an id map by external id."""
        author_id_map: dict[str, int] = {}
        for post in posts:
            if not post.author:
                continue

            # Check if we already have it in the map to avoid redundant calls
            if post.author_id in author_id_map:
                continue

            author = await self.ensure_x_author(
                author_data=post.author,
            )
            if author and author.id:
                author_id_map[post.author_id] = author.id

        return author_id_map
