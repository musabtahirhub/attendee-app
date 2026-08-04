from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Employee, AttendanceRecord
from app.schemas import AttendanceCheckIn, AttendanceResponse, AttendanceWithEmployee, DailyReportResponse
from app.logger import get_logger
logger = get_logger(__name__)
router = APIRouter()

@router.post('/check-in', response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED, summary='Record employee check-in')
def check_in(data: AttendanceCheckIn, db: Session=Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        logger.warning('Check-in failed — employee not found: id=%s', data.employee_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Employee with id {data.employee_id} not found.')
    today = date.today()
    existing_record = db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == data.employee_id, AttendanceRecord.date == today).first()
    if existing_record:
        logger.warning('Duplicate check-in rejected: employee_id=%s date=%s', data.employee_id, today)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Employee {data.employee_id} has already checked in today.')
    record = AttendanceRecord(employee_id=data.employee_id, date=today, check_in=datetime.utcnow(), status=data.status or 'present')
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("Check-in recorded: record_id=%s employee_id=%s status='%s'", record.id, record.employee_id, record.status)
    return record

@router.post('/check-out/{record_id}', response_model=AttendanceResponse, summary='Record employee check-out')
def check_out(record_id: int, db: Session=Depends(get_db)):
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        logger.warning('Check-out failed — record not found: id=%s', record_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Attendance record with id {record_id} not found.')
    if record.check_out is not None:
        logger.warning('Duplicate check-out rejected: record_id=%s', record_id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Employee has already checked out for this record.')
    record.check_out = datetime.utcnow()
    db.commit()
    db.refresh(record)
    logger.info('Check-out recorded: record_id=%s employee_id=%s', record.id, record.employee_id)
    return record

@router.get('/', response_model=list[AttendanceResponse], summary='List attendance records')
def list_attendance(record_date: date | None=Query(default=None, description='Filter by date (YYYY-MM-DD). Omit for all dates.'), skip: int=0, limit: int=100, db: Session=Depends(get_db)):
    query = db.query(AttendanceRecord)
    if record_date:
        query = query.filter(AttendanceRecord.date == record_date)
    records = query.offset(skip).limit(limit).all()
    logger.debug('Listed %d attendance records (date=%s, skip=%d, limit=%d)', len(records), record_date, skip, limit)
    return records

@router.get('/employee/{employee_id}', response_model=list[AttendanceResponse], summary='Get attendance records for an employee')
def get_employee_attendance(employee_id: int, db: Session=Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        logger.warning('Attendance lookup failed — employee not found: id=%s', employee_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Employee with id {employee_id} not found.')
    records = db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == employee_id).order_by(AttendanceRecord.date.desc()).all()
    logger.debug('Retrieved %d attendance records for employee_id=%s', len(records), employee_id)
    return records

@router.get('/report', response_model=DailyReportResponse, summary='Daily attendance summary report')
def daily_report(report_date: date=Query(default=None, description='Date for the report (YYYY-MM-DD). Defaults to today.'), db: Session=Depends(get_db)):
    if report_date is None:
        report_date = date.today()
    records = db.query(AttendanceRecord).filter(AttendanceRecord.date == report_date).all()
    total_present = sum((1 for r in records if r.status == 'present'))
    total_late = sum((1 for r in records if r.status == 'late'))
    total_absent = sum((1 for r in records if r.status == 'absent'))
    return DailyReportResponse(date=report_date, total_present=total_present, total_late=total_late, total_absent=total_absent, records=records)
