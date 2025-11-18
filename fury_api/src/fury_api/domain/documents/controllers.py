from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from fury_api.domain import paths
from fury_api.domain.users.models import User
from fury_api.lib.dependencies import (
    FiltersAndSortsParser,
    ServiceType,
    get_models_filters_parser_factory,
    get_service,
    get_uow_tenant,
    get_uow_tenant_ro,
)
from . import exceptions
from .models import (
    Document,
    DocumentCreate,
    DocumentRead,
    DocumentUpdate,
    DocumentContentRead,
    DocumentContentUpsert,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from .services import DocumentsService, DocumentContentsService
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

document_router = APIRouter()

DOCUMENTS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Document,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "title": get_default_ops_for_type(str),
        "user_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "title", "created_at", "updated_at"},
)

@document_router.post(paths.DOCUMENTS, response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    document_service: Annotated[
        DocumentsService,
        Depends(
            get_service(
                ServiceType.DOCUMENTS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Document:
    converted_document = Document(
        title=document.title,
        metadata_=document.metadata_,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return await document_service.create_item(converted_document)


@document_router.get(paths.DOCUMENTS, response_model=CursorPage[DocumentRead])
async def get_documents(
    document_service: Annotated[
        DocumentsService,
        Depends(
            get_service(
                ServiceType.DOCUMENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(DOCUMENTS_FILTERS_DEFINITION))
    ],
) -> CursorPage[DocumentRead]:
    return await document_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@document_router.get(paths.DOCUMENTS_ID, response_model=DocumentRead)
async def get_document(
    id_: int,
    document_service: Annotated[
        DocumentsService,
        Depends(
            get_service(
                ServiceType.DOCUMENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> DocumentRead:
    document = await document_service.get_item(id_)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


@document_router.put(paths.DOCUMENTS_ID, response_model=DocumentRead)
async def update_document(
    id_: int,
    document_update: DocumentUpdate,
    document_service: Annotated[
        DocumentsService,
        Depends(get_service(ServiceType.DOCUMENTS)),
    ],
) -> Document:
    document = await document_service.get_item(id_)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        updated_document = await document_service.update_item(id_, document_update)
        return updated_document
    except exceptions.DocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@document_router.delete(paths.DOCUMENTS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    id_: int,
    document_service: Annotated[
        DocumentsService,
        Depends(get_service(ServiceType.DOCUMENTS)),
    ],
) -> None:
    document = await document_service.get_item(id_)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        await document_service.delete_item(document)
    except exceptions.DocumentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@document_router.get(paths.DOCUMENT_CONTENT, response_model=list[DocumentContentRead])
async def get_document_content(
    id_: int,
    document_content_service: Annotated[
        DocumentContentsService,
        Depends(
            get_service(
                ServiceType.DOCUMENT_CONTENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> list[DocumentContentRead]:
    return await document_content_service.get_sections(id_)


@document_router.put(paths.DOCUMENT_CONTENT, response_model=list[DocumentContentRead])
async def replace_document_content(
    id_: int,
    document_content_update: DocumentContentUpsert,
    document_content_service: Annotated[
        DocumentContentsService,
        Depends(get_service(ServiceType.DOCUMENT_CONTENTS)),
    ],
) -> list[DocumentContentRead]:
    return await document_content_service.replace_sections(id_, document_content_update.sections)
