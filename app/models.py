"""
models.py
---------
SQLAlchemy ORM models that map Python classes to PostgreSQL tables.

Tables
------
1. **employees**          – stores employee master data.
2. **attendance_records** – stores daily check-in / check-out timestamps
                           for each employee, linked via a foreign key.
"""

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
    """
    Represents an employee in the organisation.

    Columns
    -------
    id         : Auto-incrementing primary key.
    name       : Full name of the employee (required).
    email      : Unique email address (required).
    department : Optional department name.
    created_at : Timestamp when the record was created (auto-set).

    Relationships
    -------------
    attendances : One-to-many relationship to AttendanceRecord.
                  `cascade="all, delete-orphan"` means deleting an employee
                  also deletes all their attendance records.
    """

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship: one employee -> many attendance records
    attendances = relationship(
        "AttendanceRecord",
        back_populates="employee",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name='{self.name}', email='{self.email}')>"


class AttendanceRecord(Base):
    """
    Represents a single attendance entry for one employee on one day.

    Columns
    -------
    id          : Auto-incrementing primary key.
    employee_id : Foreign key referencing employees.id.
    date        : The calendar date of the attendance record.
    check_in    : Timestamp when the employee checked in.
    check_out   : Timestamp when the employee checked out (nullable — they
                  may not have checked out yet).
    status      : Attendance status string. Possible values:
                  • "present"  – checked in on time
                  • "late"     – checked in after the threshold
                  • "absent"   – no check-in recorded

    Relationships
    -------------
    employee : Many-to-one back-reference to the Employee model.
    """

    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, default=date.today)
    check_in = Column(DateTime, nullable=False, default=datetime.utcnow)
    check_out = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="present")

    # Back-reference to the parent Employee
    employee = relationship("Employee", back_populates="attendances")

    def __repr__(self) -> str:
        return (
            f"<AttendanceRecord(id={self.id}, employee_id={self.employee_id}, "
            f"date={self.date}, status='{self.status}')>"
        )
