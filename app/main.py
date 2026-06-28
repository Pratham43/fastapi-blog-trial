from typing import Annotated

from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.middleware import LoggingMiddleware
from app.models import models
from sqlalchemy import select
from sqlalchemy.orm import Session
import uvicorn


from app.config import settings
from app.db.database import get_db, engine
from app.schemas.post_schema import PostCreate, PostResponse
from app.schemas.user_schema import UserCreate

from app.api.v1.users import user_router
from app.api.v1.posts import post_router
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

origins = [
    "http://localhost:8080",
    "http://0.0.0.0:8080",
    "http://127.0.0.1:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           
    allow_credentials=True,           
    allow_methods=["*"],              
    allow_headers=["*"],            
)

app.add_middleware(
    LoggingMiddleware
)

app.include_router(user_router)
app.include_router(post_router) 



@app.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
        
    except Exception as e:
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8060)
