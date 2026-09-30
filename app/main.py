import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.redis import close_redis, redis_client

settings = get_settings()
logger = logging.getLogger("gatepass")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await close_redis()


app = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error", extra={"request_id": request_id})
        response = JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "request_id": request_id}})
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details, "request_id": request_id}},
    )


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": settings.app_name}


@app.get("/ready", tags=["System"])
async def ready():
    from sqlalchemy import text
    from app.core.database import SessionLocal
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        await redis_client.ping()
    except Exception as exc:
        logger.exception("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(exc) if settings.debug else "dependency unavailable"})
    return {"status": "ready", "dependencies": {"mysql": "ok", "redis": "ok"}}


app.include_router(api_router, prefix=settings.api_v1_prefix)
