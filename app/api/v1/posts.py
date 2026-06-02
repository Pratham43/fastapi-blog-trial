from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Annotated
from models import models
from schemas.post_schema import PostCreate, PostResponse, PostUpdate
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.utils.auth import CurrentUser

from db.database import get_db

post_router = APIRouter(prefix="/api/v1/posts", tags=["posts"])




@post_router.get("/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@post_router.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    post: PostCreate,
    current_user: CurrentUser, 
    db: Annotated[Session, Depends(get_db)]
):
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=current_user.id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@post_router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@post_router.put("/{post_id}", response_model=PostResponse)
def update_post_full(
    post_id: int, 
    post_data: PostCreate, 
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
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

    db.commit()
    db.refresh(post)
    return post


@post_router.patch("/{post_id}", response_model=PostResponse)
def update_post_partial(
    post_id: int, 
    post_data: PostUpdate, 
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
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

    db.commit()
    db.refresh(post)
    return post


@post_router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def get_post(
    post_id: int, 
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not Authorized to delete this post"
        )

    db.delete(post)
    db.commit()

    