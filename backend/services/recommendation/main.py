"""
推荐服务主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config import settings
from shared.database import init_db, close_db
from shared.exceptions import AppException
from fastapi.responses import JSONResponse
from fastapi import Request

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=f"{settings.app_name} - Recommendation Service",
    description="智能推荐服务",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "recommendation-service"}


app.include_router(router)
