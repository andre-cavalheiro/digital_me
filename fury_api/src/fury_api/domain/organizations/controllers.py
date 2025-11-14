from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Security, status

from fury_api.domain import paths
from fury_api.lib.dependencies import (
    get_service,
    get_uow_any_tenant,
    get_uow_ro,
)
from fury_api.lib.factories.service_factory import ServiceFactory, ServiceType
from fury_api.domain.organizations import exceptions
from fury_api.domain.users.models import User
from fury_api.domain.organizations.models import (
    Organization,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from fury_api.lib.security import get_current_user, get_current_user_new_organization
from fury_api.domain.users.services import UsersService
from .services import OrganizationsService


# from fury_api.lib.dependencies import get_stripe_client, get_prefect_client
# from fury_api.lib.integrations import StripeClient, PrefectClient
# from fury_api.domain.organizations.integration_services import create_stripe_customer, create_prefect_support_user


user_auth_router = APIRouter(dependencies=[Security(get_current_user)])
user_auth_new_organization_router = APIRouter(dependencies=[Depends(get_current_user_new_organization)])

@user_auth_router.get(paths.ORGANIZATIONS_SELF, response_model=OrganizationRead)
async def get_organization_me(
    organization_service: Annotated[
        OrganizationsService,
        Depends(
            get_service(
                ServiceType.ORGANIZATIONS,
                read_only=True,
                uow=Depends(get_uow_ro),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Organization:
    organization = await organization_service.get_item(current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


@user_auth_router.put(paths.ORGANIZATIONS_SELF, response_model=OrganizationRead)
async def update_organization_me(
    organization_update: OrganizationUpdate,
    organization_service: Annotated[
        OrganizationsService,
        Depends(get_service(ServiceType.ORGANIZATIONS)),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Organization:
    organization = await organization_service.get_item(current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    try:
        updated_organization = await organization_service.update_item(
            current_user.organization_id,
            organization_update
        )
        return updated_organization
    except exceptions.OrganizationsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@user_auth_router.delete(paths.ORGANIZATIONS_SELF, status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization_me(
    organization_service: Annotated[
        OrganizationsService,
        Depends(get_service(ServiceType.ORGANIZATIONS)),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    organization = await organization_service.get_item(current_user.organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    try:
        users_service: UsersService = ServiceFactory.create_service(
            ServiceType.USERS,
            organization_service.uow,
            auth_user=current_user,
            has_system_access=True,
        )

        users = [user async for user in users_service.get_items()]
        for user in users:
            await users_service.delete_item(user)

        await organization_service.delete_item(organization)
    except exceptions.OrganizationsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@user_auth_new_organization_router.post(
    paths.ORGANIZATIONS,
    response_model=OrganizationRead,
    response_model_exclude_unset=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    organization: OrganizationCreate,
    organization_service: Annotated[
        OrganizationsService,
        Depends(
            get_service(
                ServiceType.ORGANIZATIONS,
                read_only=False,
                uow=Depends(get_uow_any_tenant),
                auth_user=Depends(get_current_user_new_organization),
            )
        ),
    ],
    users_service: Annotated[
        UsersService,
        Depends(
            get_service(
                ServiceType.USERS,
                has_system_access=True,
                uow=Depends(get_uow_any_tenant),
                auth_user=Depends(get_current_user_new_organization),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user_new_organization)],
    # stripe_client: Annotated[StripeClient, Depends(get_stripe_client)],
    # prefect_client: Annotated[PrefectClient, Depends(get_prefect_client)],

) -> Organization:
    existing_user = await users_service.get_user_by_email(email=current_user.email)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with that email already exists")

    organization_obj = Organization.model_validate(organization)
    try:
        new_organization = await organization_service.create_organization_with_user(
            organization_obj,
            current_user
        )

        # Stripe
        """
        new_organization = await services.create_stripe_customer(new_organization, current_user.email)
        async with uow.with_organization(organization_id=new_organization.id):
            new_organization = await services.update_organization(uow, new_organization.id, new_organization)
        """

        # Prefect
        """
        async with uow.with_organization(organization_id=new_organization.id):
            await services.create_prefect_support_user(uow, new_organization.id, prefect_client)
        """

    except exceptions.OrganizationsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return new_organization

organization_router = APIRouter()
organization_router.include_router(user_auth_router)
organization_router.include_router(user_auth_new_organization_router)
