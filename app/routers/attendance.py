"""
routers/attendance.py
---------------------
Endpoints for recording and querying employee attendance.

Key operations:
  • Check-in  — creates a new AttendanceRecord for today.
  • Check-out — updates an existing record with the check-out timestamp.
  • Query     — list records with optional date filtering.
  • Report    — daily summary (present / late / absent counts).
"""

from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee, AttendanceRecord
from app.schemas import (
    AttendanceCheckIn,
    AttendanceResponse,
    AttendanceWithEmployee,
    DailyReportResponse,
)

router = APIRouter()


# ────────────────────────── CHECK-IN ──────────────────────────


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record employee check-in",
)
def check_in(data: AttendanceCheckIn, db: Session = Depends(get_db)):
    """
    Record a check-in for an employee.

    - **employee_id**: The ID of the employee checking in (required).
    - **status**: "present" (default) or "late".

    Business rules:
    1. The employee must exist.
    2. An employee can only check in **once per day**. Attempting a second
       check-in on the same date returns a 400 error.
    """
    # 1. Verify employee exists
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {data.employee_id} not found.",
        )

    # 2. Prevent duplicate check-in for the same day
    today = date.today()
    existing_record = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id == data.employee_id,
            AttendanceRecord.date == today,
        )
        .first()
    )
    if existing_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee {data.employee_id} has already checked in today.",
        )

    # 3. Create the attendance record
    record = AttendanceRecord(
        employee_id=data.employee_id,
        date=today,
        check_in=datetime.utcnow(),
        status=data.status or "present",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ────────────────────────── CHECK-OUT ──────────────────────────


@router.post(
    "/check-out/{record_id}",
    response_model=AttendanceResponse,
    summary="Record employee check-out",
)
def check_out(record_id: int, db: Session = Depends(get_db)):
    """
    Record the check-out time for an existing attendance record.

    - **record_id**: The attendance record ID (path parameter).

    Business rules:
    1. The attendance record must exist.
    2. The employee must not have already checked out (check_out is null).
    """
    record = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with id {record_id} not found.",
        )

    if record.check_out is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee has already checked out for this record.",
        )

    record.check_out = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


# ────────────────────────── LIST RECORDS ──────────────────────────


@router.get(
    "/",
    response_model=list[AttendanceResponse],
    summary="List attendance records",
)
def list_attendance(
    record_date: date | None = Query(
        default=None,
        description="Filter by date (YYYY-MM-DD). Omit for all dates.",
    ),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Retrieve attendance records with optional date filtering and pagination.

    - **record_date**: Filter to a specific date.
    - **skip** / **limit**: Pagination controls.
    """
    query = db.query(AttendanceRecord)

    if record_date:
        query = query.filter(AttendanceRecord.date == record_date)

    records = query.offset(skip).limit(limit).all()
    return records


# ─────────────────────── RECORDS BY EMPLOYEE ──────────────────────


@router.get(
    "/employee/{employee_id}",
    response_model=list[AttendanceResponse],
    summary="Get attendance records for an employee",
)
def get_employee_attendance(
    employee_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve all attendance records for a specific employee, ordered by
    most recent date first.

    Raises **404** if the employee does not exist.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found.",
        )

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.employee_id == employee_id)
        .order_by(AttendanceRecord.date.desc())
        .all()
    )
    return records


# ──────────────────────── DAILY REPORT ────────────────────────


@router.get(
    "/report",
    response_model=DailyReportResponse,
    summary="Daily attendance summary report",
)
def daily_report(
    report_date: date = Query(
        default=None,
        description="Date for the report (YYYY-MM-DD). Defaults to today.",
    ),
    db: Session = Depends(get_db),
):
    """
    Generate a summary report for a given date (defaults to today).

    Returns:
    - **total_present**: Number of employees with status "present".
    - **total_late**: Number of employees with status "late".
    - **total_absent**: Number of employees with status "absent".
    - **records**: The individual attendance records for that day.
    """
    if report_date is None:
        report_date = date.today()

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.date == report_date)
        .all()
    )

    total_present = sum(1 for r in records if r.status == "present")
    total_late = sum(1 for r in records if r.status == "late")
    total_absent = sum(1 for r in records if r.status == "absent")

    return DailyReportResponse(
        date=report_date,
        total_present=total_present,
        total_late=total_late,
        total_absent=total_absent,
        records=records,
    )
