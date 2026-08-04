from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict

class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: Optional[str] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    department: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AttendanceCheckIn(BaseModel):
    employee_id: int
    status: Optional[str] = "present"

class AttendanceCheckOut(BaseModel):
    pass

class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in: datetime
    check_out: Optional[datetime] = None
    status: str

    model_config = ConfigDict(from_attributes=True)

class AttendanceWithEmployee(AttendanceResponse):
    employee: EmployeeResponse

    model_config = ConfigDict(from_attributes=True)

class DailyReportResponse(BaseModel):
    date: date
    total_present: int
    total_late: int
    total_absent: int
    records: list[AttendanceResponse]
