from typing import Annotated

from fastapi import APIRouter, Depends

from fury_api.domain import paths
from fury_api.lib.dependencies import (
    get_uow_any_tenant,
)
from fury_api.lib.security import validate_admin_token

from fury_api.domain.organizations import services
from fury_api.domain.organizations.models import (
    Organization,
)
from fury_api.lib.unit_of_work import UnitOfWork

admin_router = APIRouter(dependencies=[Depends(validate_admin_token)])


@admin_router.get(paths.ADMIN_ORGANIZATIONS, response_model=list[Organization])
async def get_active_organizations(
    uow: Annotated[UnitOfWork, Depends(get_uow_any_tenant)],
) -> list[Organization]:
    return await services.get_organizations(uow)
