import time
from pathlib import Path
from contextlib import asynccontextmanager

from typing import Annotated
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine, Base, get_db
from app.models import User, Employee, AttendanceRecord, LeaveRequest
from app.auth import hash_password, get_current_user
from app.routers import employees, attendance, chatbot
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
        "A RESTful API for managing employee attendance and leave. "
        "Built with FastAPI, SQLAlchemy, PostgreSQL, and LangChain."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


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

app.include_router(
    chatbot.router,
    prefix="/api/chatbot",
    tags=["Chatbot"],
)


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.post("/register", tags=["Authentication"], status_code=status.HTTP_201_CREATED)
def register(username: str, password: str, db: Session = Depends(get_db)):
    """User Registration Route (Saves hashed password to DB)."""
    existing_user = db.query(User).filter(User.username == username.strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    hashed = hash_password(password)
    new_user = User(username=username.strip(), hashed_password=hashed)
    db.add(new_user)
    db.commit()
    return {"message": f"User '{username}' created successfully."}


@app.post("/chat", tags=["Protected"])
def chat(prompt: str, current_user: Annotated[str, Depends(get_current_user)]):
    """Protected Chat Route requiring HTTP Basic Authentication."""
    return {"user": current_user, "reply": f"Processing prompt: '{prompt}'"}


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
