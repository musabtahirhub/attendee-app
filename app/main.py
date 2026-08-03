"""
main.py
-------
Entry point for the FastAPI Attendance System application.

This module:
1. Creates the FastAPI application instance with metadata (title, description,
   version) that populates the auto-generated Swagger / ReDoc documentation.
2. Registers a **startup event** that creates all database tables if they
   don't already exist (safe to run repeatedly).
3. Includes the `employees` and `attendance` routers under their respective
   URL prefixes so all endpoints are properly namespaced.
4. Exposes a simple root health-check endpoint at `/`.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

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
)


# ──────────────────── Register Routers ────────────────────


app.include_router(
    employees.router,
    prefix="/employees",
    tags=["Employees"],
)

app.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["Attendance"],
)


# ──────────────────── Root / Health Check ────────────────────


@app.get("/", tags=["Health"])
def root():
    """
    Simple health-check endpoint. Returns a welcome message
    confirming the API is running.
    """
    return {
        "message": "Welcome to the Attendance System API",
        "docs": "/docs",
        "version": "1.0.0",
    }
