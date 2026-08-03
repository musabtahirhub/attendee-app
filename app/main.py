"""
main.py
-------
Entry point for the FastAPI Attendance System application.

This module:
1. Creates the FastAPI application instance with metadata (title, description,
   version) that populates the auto-generated Swagger / ReDoc documentation.
2. Registers a **startup event** that creates all database tables if they
   don't already exist (safe to run repeatedly).
3. Includes the `employees` and `attendance` routers under `/api/` prefix
   so they don't collide with the frontend routes.
4. Serves the frontend static files (HTML, CSS, JS).
5. Adds CORS middleware for local development.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.models import Employee, AttendanceRecord  # noqa: F401 — import so Base knows about them
from app.routers import employees, attendance


# ──────────────────── Lifespan (startup / shutdown) ────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager that runs on application startup and shutdown.

    On startup:
        Creates all tables defined in Base.metadata if they don't exist.
        This is equivalent to running CREATE TABLE IF NOT EXISTS for each model.

    On shutdown:
        (nothing to clean up in this simple app)
    """
    # --- STARTUP ---
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created / verified.")
    yield
    # --- SHUTDOWN ---
    print("[INFO] Application shutting down.")


# ──────────────────── Application Instance ────────────────────


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


# ──────────────────── CORS Middleware ────────────────────


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────── Register Routers (under /api) ────────────────────


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


# ──────────────────── Static Files ────────────────────

# Resolve the static directory relative to the project root
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ──────────────────── Frontend & Health Check ────────────────────


@app.get("/api/health", tags=["Health"])
def health_check():
    """
    Health-check endpoint. Returns a JSON status confirming the API is running.
    """
    return {
        "status": "healthy",
        "message": "Attendance System API is running",
        "version": "1.0.0",
    }


@app.get("/", tags=["Frontend"], include_in_schema=False)
def serve_frontend():
    """
    Serve the frontend single-page application.
    """
    return FileResponse(str(STATIC_DIR / "index.html"))
