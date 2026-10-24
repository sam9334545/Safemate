"""FastAPI Application entry point with lifespan, middleware, and exception handlers."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import deepfake, detect, health, model_info
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.schemas.errors import AppException
from app.services.model_service import model_service
from app.services.video_deepfake_service import video_deepfake_service
from app.utils.request_id import get_request_id, set_request_id

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown lifecycle events."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in '{settings.ENVIRONMENT}' mode.")
    logger.info(f"Configured CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"Configured max upload: {settings.MAX_UPLOAD_MB} MB")

    # Load pretrained still-image model
    logger.info(f"Attempting model startup load for: {settings.MODEL_ID}")
    try:
        model_service.load()
    except Exception as exc:
        logger.warning(f"Initial model loading failed: {type(exc).__name__}. Will report unready until loaded.")

    # Load pretrained video deepfake model
    logger.info(f"Attempting video deepfake startup load for: {settings.VIDEO_DEEPFAKE_MODEL_ID}")
    try:
        video_deepfake_service.load()
    except Exception as exc:
        logger.warning(f"Initial video deepfake model loading failed: {type(exc).__name__}. Will load lazily or report unready.")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}.")
    if model_service.model is not None:
        del model_service.model
        del model_service.processor
        model_service.model = None
        model_service.processor = None
        model_service.is_loaded = False

    if video_deepfake_service.model is not None:
        del video_deepfake_service.model
        del video_deepfake_service.detector
        video_deepfake_service.model = None
        video_deepfake_service.detector = None
        video_deepfake_service.is_loaded = False


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    app = FastAPI(
        title="AI Image Screening API",
        description=(
            "REST API for screening AI-generated images in a women's safety application. "
            "Exposes pre-trained Hugging Face classification with privacy-first, in-memory processing."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Custom Request ID Middleware
    class RequestIDMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            rid = set_request_id(request.headers.get("X-Request-ID"))
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response

    app.add_middleware(RequestIDMiddleware)

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # 3. Exception Handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        rid = exc.request_id or get_request_id()
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                },
                "request_id": rid,
            },
            headers={"X-Request-ID": rid},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        rid = get_request_id()
        # Formulate readable message without exposing internal details
        error_messages = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            msg = err.get("msg", "Validation error")
            error_messages.append(f"{loc}: {msg}" if loc else msg)
        combined_msg = "; ".join(error_messages) or "Request validation failed."

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": combined_msg,
                },
                "request_id": rid,
            },
            headers={"X-Request-ID": rid},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = get_request_id()
        logger.error(f"Unhandled exception on {request.url.path} [ReqID: {rid}]: {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected internal server error occurred. Please contact support with the request ID.",
                },
                "request_id": rid,
            },
            headers={"X-Request-ID": rid},
        )

    # 4. Include Routers
    app.include_router(health.router, prefix=settings.API_V1_PREFIX)
    app.include_router(model_info.router, prefix=settings.API_V1_PREFIX)
    app.include_router(detect.router, prefix=settings.API_V1_PREFIX)
    app.include_router(deepfake.router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
            "ready": f"{settings.API_V1_PREFIX}/health/ready",
            "model_info": f"{settings.API_V1_PREFIX}/model-info",
            "image_screening": f"{settings.API_V1_PREFIX}/detect",
            "video_deepfake_screening": f"{settings.API_V1_PREFIX}/deepfake/detect",
            "video_deepfake_ready": f"{settings.API_V1_PREFIX}/deepfake/ready",
            "video_deepfake_model_info": f"{settings.API_V1_PREFIX}/deepfake/model-info",
        }

    return app


app = create_app()
