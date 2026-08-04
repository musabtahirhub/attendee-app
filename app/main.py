import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine, Base
from app.models import Employee, AttendanceRecord
from app.routers import employees, attendance
from app.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up.")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created / verified.")
    except SQLAlchemyError:
        logger.exception("Failed to initialise database tables.")
        raise
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title="Attendance System API",
    description=(
        "A RESTful API for managing employee attendance. "
        "Built with FastAPI, SQLAlchemy, and PostgreSQL."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ──────────────────── Global Exception Handlers ────────────────────


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception(
        "Database error on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "A database error occurred. Please try again later.",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


# ──────────────────── Middleware ────────────────────


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "%s %s -> UNHANDLED EXCEPTION (%.1fms)",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ──────────────────── Routers ────────────────────


app.include_router(
    employees.router,
    prefix="/api/employees",
    tags=["Employees"],
)

app.include_router(
    attendance.router,
    prefix="/api/attendance",
    tags=["Attendance"],
)


# ──────────────────── Static Files & Frontend ────────────────────


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/api/health", tags=["Health"])
def health_check():
    logger.debug("Health check requested.")
    return {
        "status": "healthy",
        "message": "Attendance System API is running",
        "version": "1.0.0",
    }


@app.get("/", tags=["Frontend"], include_in_schema=False)
def serve_frontend():
    return FileResponse(str(STATIC_DIR / "index.html"))

