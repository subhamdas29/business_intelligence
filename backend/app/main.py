import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aibi_platform")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# CORS middleware configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
async def health_check():
    """Health check endpoint for Docker & Kubernetes liveness probes"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0"
    }


@app.get(f"{settings.API_V1_STR}/ping", tags=["System"])
async def ping():
    return {"message": "pong", "project": settings.PROJECT_NAME}
