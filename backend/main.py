"""FastAPI application entrypoint for MedQuAD Clinical Assistant."""

import logging
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes.chat import router as chat_router
from backend.api.routes.evaluations import router as evaluations_router
from backend.api.routes.feedback import router as feedback_router
from backend.api.routes.health import router as health_router
from backend.api.routes.sessions import router as sessions_router
from backend.api.routes.telemetry import router as telemetry_router
from backend.core.config import get_settings
from backend.core.logging import setup_logging
from backend.core.telemetry import setup_telemetry

settings = get_settings()
setup_logging(log_level=settings.log_level)
logger = logging.getLogger("backend.main")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info(
        "Initializing %s v%s in %s environment...",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    setup_telemetry()
    yield
    logger.info("Shutting down %s...", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agent Clinical Assistant over NIH MedQuAD Knowledge Grounding Corpus",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    """Middleware attaching a unique request ID and X-Process-Time header."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-MS"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global unhandled exception wrapper returning structured error JSON."""
    logger.error("Unhandled exception processing %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "requestId": getattr(request.state, "request_id", None),
        },
    )


# Include API Routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(feedback_router)
app.include_router(telemetry_router)
app.include_router(evaluations_router)

# Mount Static Files & UI Root
STATIC_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"message": "MedQuAD Backend Online. Web UI loading..."})


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
