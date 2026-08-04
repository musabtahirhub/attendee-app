from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attendances = relationship(
        "AttendanceRecord",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name='{self.name}', email='{self.email}')>"

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, default=date.today)
    check_in = Column(DateTime, nullable=False, default=datetime.utcnow)
    check_out = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="present")

    employee = relationship("Employee", back_populates="attendances")

    def __repr__(self) -> str:
        return (
            f"<AttendanceRecord(id={self.id}, employee_id={self.employee_id}, "
            f"date={self.date}, status='{self.status}')>"
        )
