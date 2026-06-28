from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status
)

from app.schemas.post_schema import (
    PostCreate,
    PostResponse,
    PostUpdate,
    PaginatedPostsResponse
)

from app.services.post_service import PostService

from app.dependencies.services import (
    get_post_service
)

from app.utils.auth import CurrentUser


post_router = APIRouter(
    prefix="/api/v1/posts",
    tags=["posts"]
)


@post_router.get(
    "",
    response_model=PaginatedPostsResponse
)
async def get_posts(
    service: Annotated[
        PostService,
        Depends(get_post_service)
    ],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.get_posts(
        skip,
        limit
    )


@post_router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_post(
    post: PostCreate,
    current_user: CurrentUser,
    service: Annotated[
        PostService,
        Depends(get_post_service)
    ]
):
    return await service.create_post(
        post,
        current_user.id
    )


@post_router.get(
    "/{post_id}",
    response_model=PostResponse
)
async def get_post(
    post_id: int,
    service: Annotated[
        PostService,
        Depends(get_post_service)
    ]
):
    return await service.get_post(
        post_id
    )


@post_router.put(
    "/{post_id}",
    response_model=PostResponse
)
async def update_post(
    post_id: int,
    post: PostCreate,
    current_user: CurrentUser,
    service: Annotated[
        PostService,
        Depends(get_post_service)
    ]
):
    return await service.update_post(
        post_id,
        post,
        current_user.id
    )


@post_router.patch(
    "/{post_id}",
    response_model=PostResponse
)
async def patch_post(
    post_id: int,
    post: PostUpdate,
    current_user: CurrentUser,
    service: Annotated[
        PostService,
        Depends(get_post_service)
    ]
):
    return await service.patch_post(
        post_id,
        post,
        current_user.id
    )


@post_router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_post(
    post_id: int,
    current_user: CurrentUser,
    service: Annotated[
        PostService,
        Depends(get_post_service)
    ]
):
    await service.delete_post(
        post_id,
        current_user.id
    )