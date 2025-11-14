import asyncio
import argparse

from typing import Optional
from fury_api.lib.factories import ServiceFactory
from fury_api.lib.factories.service_factory import ServiceType
from fury_api.lib.factories import UnitOfWorkFactory


async def main(organization_id: int, user_id: Optional[int] = None, push_to_prefect: bool = False):
    async with UnitOfWorkFactory.get_uow(organization_id=organization_id) as uow:
        users_service = ServiceFactory.create_service(ServiceType.USERS, uow, has_system_access=True)

        if not user_id:
            print(f"Creating system user for organization {organization_id}")
            user = await users_service.create_system_user(organization_id)
            print(f"Created system user: ID: {user.id}, Name: {user.name}")
            if not user:
                raise ValueError("Failed to create system user")
        else:
            user = await users_service.get_item(user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")

        token = await users_service.create_long_lived_token_for_user(user)
        print(f"Token: {token}")

        if push_to_prefect:
            from fury_api.lib.factories.integrations_factory import ClientsFactory
            from fury_api.domain.organizations.integration_services import _push_prefect_secret

            async with ClientsFactory.get_prefect_client() as prefect_client:
                await _push_prefect_secret(organization_id, token, user, prefect_client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a system token for an organization")
    parser.add_argument("organization_id", type=int, help="The ID of the organization")
    parser.add_argument("--user_id", type=int, help="Optional user ID. If not provided, a system user will be created")
    parser.add_argument("--push_to_prefect", action="store_true", help="Push the token to Prefect if set")

    args = parser.parse_args()
    asyncio.run(main(args.organization_id, args.user_id, args.push_to_prefect))
