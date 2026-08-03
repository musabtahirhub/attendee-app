"""
schemas.py
----------
Pydantic models (schemas) used for request validation and response serialisation.

Naming convention:
    *Create  — fields required when creating a resource  (request body).
    *Update  — fields that may be updated (all optional)  (request body).
    *Response — fields returned to the client               (response body).

The `model_config` with `from_attributes = True` tells Pydantic v2 to read
data from SQLAlchemy model attributes (instead of requiring a dict).
"""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


# ──────────────────────────── Employee Schemas ────────────────────────────


class EmployeeCreate(BaseModel):
    """Schema for creating a new employee (POST request body)."""

    name: str
    email: str
    department: Optional[str] = None


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee (PUT request body). All fields optional."""

    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None


class EmployeeResponse(BaseModel):
    """Schema for returning employee data in API responses."""

    id: int
    name: str
    email: str
    department: Optional[str] = None
    created_at: datetime

    # Pydantic v2 config — allows reading data from ORM model attributes.
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────── Attendance Schemas ───────────────────────────


class AttendanceCheckIn(BaseModel):
    """Schema for the check-in request body."""

    employee_id: int
    status: Optional[str] = "present"  # "present", "late"


class AttendanceCheckOut(BaseModel):
    """Schema for the check-out request body (currently unused — ID is in the path)."""

    pass


class AttendanceResponse(BaseModel):
    """Schema for returning a single attendance record in API responses."""

    id: int
    employee_id: int
    date: date
    check_in: datetime
    check_out: Optional[datetime] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class AttendanceWithEmployee(AttendanceResponse):
    """Extended response that nests the employee info inside the attendance record."""

    employee: EmployeeResponse

    model_config = ConfigDict(from_attributes=True)


class DailyReportResponse(BaseModel):
    """Schema for the daily attendance summary report."""

    date: date
    total_present: int
    total_late: int
    total_absent: int
    records: list[AttendanceResponse]
