from fastapi import APIRouter


from fury_api.domain import paths
from fury_api.domain.health_check.controllers import health_router
from fury_api.domain.admin.controllers import admin_router
from fury_api.domain.organizations.controllers import organization_router
from fury_api.domain.users.controllers import user_router
from fury_api.domain.plugins.controllers import plugin_router
from fury_api.domain.documents.controllers import document_router
from fury_api.domain.conversations.controllers import conversation_router
from fury_api.domain.content.controllers import content_router
from fury_api.domain.sources.controllers import sources_router

__all__ = ["create_router"]


def create_router() -> APIRouter:
    router = APIRouter(prefix=paths.API_ROOT)

    router.include_router(admin_router, tags=["Admin"], include_in_schema=False)
    router.include_router(health_router, tags=["Health Check"])
    router.include_router(organization_router, tags=["Organizations"])
    router.include_router(user_router, tags=["Users"])
    router.include_router(plugin_router, tags=["Plugins"])
    router.include_router(document_router, tags=["Documents"])
    router.include_router(conversation_router, tags=["Conversations"])
    router.include_router(content_router, tags=["Content"])
    router.include_router(sources_router, tags=["Sources"])

    return router
