from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Employee, AttendanceRecord
from app.logger import get_logger

logger = get_logger(__name__)


def get_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
    logger.debug("Fetching employee by id=%s", employee_id)
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employee_by_email(db: Session, email: str) -> Optional[Employee]:
    logger.debug("Fetching employee by email='%s'", email)
    return db.query(Employee).filter(Employee.email == email).first()


def get_attendance_record_by_id(db: Session, record_id: int) -> Optional[AttendanceRecord]:
    logger.debug("Fetching attendance record by id=%s", record_id)
    return db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()


def get_attendance_by_employee_and_date(
    db: Session,
    employee_id: int,
    target_date: date,
) -> Optional[AttendanceRecord]:
    logger.debug("Checking attendance for employee_id=%s on date=%s", employee_id, target_date)
    return (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.date == target_date,
        )
        .first()
    )
