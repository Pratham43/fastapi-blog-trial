from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from typing import Annotated
from app.models import models
from app.schemas.post_schema import PostCreate, PostResponse, PostUpdate, PaginatedPostsResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.auth import CurrentUser
from app.config import settings

from app.db.database import get_db
from app.utils.cache import cache

post_router = APIRouter(prefix="/api/v1/posts", tags=["posts"])




@post_router.get("", response_model=PaginatedPostsResponse)
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    cache_key = f"posts:list:skip={skip}:limit={limit}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        try:
            return PaginatedPostsResponse.model_validate_json(cached_data)
        except Exception:
            pass

    count_result = await db.execute(select(func.count()).select_from(models.Post))
    total = count_result.scalar() or 0 
    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()

    has_more = (skip + len(posts)) < total

    response_data = PaginatedPostsResponse(
        posts=[PostResponse.model_validate(post) for post in posts],
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more
    )

    await cache.set(
        cache_key,
        response_data.model_dump_json(),
        expire=settings.redis_cache_expire_seconds
    )
    return response_data


@post_router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreate,
    current_user: CurrentUser, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=current_user.id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    
    # Invalidate list cache
    await cache.clear_pattern("posts:list:*")
    return new_post


@post_router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    cache_key = f"posts:detail:{post_id}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        try:
            return PostResponse.model_validate_json(cached_data)
        except Exception:
            pass

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()
    if post:
        response_data = PostResponse.model_validate(post)
        await cache.set(
            cache_key,
            response_data.model_dump_json(),
            expire=settings.redis_cache_expire_seconds
        )
        return response_data
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@post_router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, 
    post_data: PostCreate, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to update this post",
        )
        
    post.title = post_data.title
    post.content = post_data.content

    await db.commit()
    await db.refresh(post)
    
    # Invalidate cache
    await cache.clear_pattern("posts:list:*")
    await cache.delete(f"posts:detail:{post_id}")
    return post


@post_router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int, 
    post_data: PostUpdate, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to update this post"
        )

    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    
    # Invalidate cache
    await cache.clear_pattern("posts:list:*")
    await cache.delete(f"posts:detail:{post_id}")
    return post


@post_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete this post"
        )

    await db.delete(post)
    await db.commit()
    
    # Invalidate cache
    await cache.clear_pattern("posts:list:*")
    await cache.delete(f"posts:detail:{post_id}")

    