from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models import Employee, AttendanceRecord, LeaveRequest
from app.logger import get_logger

logger = get_logger(__name__)


def get_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
    logger.debug("Fetching employee by id=%s", employee_id)
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employee_by_email(db: Session, email: str) -> Optional[Employee]:
    logger.debug("Fetching employee by email='%s'", email)
    return db.query(Employee).filter(Employee.email == email).first()


def get_employee_by_name(db: Session, name: str) -> Optional[Employee]:
    logger.debug("Fetching employee by name='%s'", name)
    return db.query(Employee).filter(Employee.name.ilike(f"%{name}%")).first()


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


def create_leave_request(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date,
    reason: str,
) -> LeaveRequest:
    logger.debug("Creating leave request for employee_id=%s from %s to %s", employee_id, start_date, end_date)
    leave_req = LeaveRequest(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status="pending",
    )
    db.add(leave_req)
    db.commit()
    db.refresh(leave_req)
    return leave_req


def get_pending_leaves(db: Session) -> List[LeaveRequest]:
    logger.debug("Fetching all pending leave requests")
    return db.query(LeaveRequest).filter(LeaveRequest.status == "pending").all()


def approve_leave_request(db: Session, leave_id: int) -> Optional[LeaveRequest]:
    logger.debug("Approving leave request id=%s", leave_id)
    leave_req = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if leave_req:
        leave_req.status = "approved"
        db.commit()
        db.refresh(leave_req)
    return leave_req


def get_approved_leave_by_employee_and_date(
    db: Session,
    employee_id: int,
    target_date: date,
) -> Optional[LeaveRequest]:
    logger.debug("Checking approved leave for employee_id=%s on date=%s", employee_id, target_date)
    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "approved",
            LeaveRequest.start_date <= target_date,
            LeaveRequest.end_date >= target_date,
        )
        .first()
    )


def get_leave_requests_by_employee(db: Session, employee_id: int) -> List[LeaveRequest]:
    logger.debug("Fetching leave requests for employee_id=%s", employee_id)
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.employee_id == employee_id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )

