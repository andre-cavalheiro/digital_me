from typing import TYPE_CHECKING

from .models import Organization
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService, with_uow
from fury_api.lib.factories.service_factory import ServiceFactory, ServiceType

if TYPE_CHECKING:
    pass

__all__ = ["OrganizationsService"]


class OrganizationsService(SqlService[Organization]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Organization, uow, auth_user=auth_user, **kwargs)

    @with_uow
    async def create_organization_with_user(
        self,
        organization: Organization,
        user: User,
    ) -> Organization:
        """
        Create an organization and its primary user.
        This is a special method that handles the cross-domain logic.
        """
        await self.create_item(organization)

        async with self.uow.with_organization(organization_id=organization.id):
            users_service = ServiceFactory.create_service(ServiceType.USERS, self.uow)
            # Create primary user for organization
            user.organization_id = organization.id
            if not user.name:
                user.name = user.email
            await users_service.create_item(user)

        return organization
