from datetime import UTC, datetime, timedelta
from typing import Annotated

from botocore.exceptions import ClientError
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status
)

from fastapi.security import OAuth2PasswordRequestForm 
from PIL import UnidentifiedImageError
from sqlalchemy import delete as sql_delete
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool
                                                                         
                                                                         
