
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):

    existing = db.query(Employee).filter(Employee.email == employee.email).first()
    if existing:
        logger.warning("Duplicate email rejected: %s", employee.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An employee with email '{employee.email}' already exists.",
        )

    db_employee = Employee(
        name=employee.name,
        email=employee.email,
        department=employee.department,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    logger.info("Employee created: id=%s name='%s' email='%s'", db_employee.id, db_employee.name, db_employee.email)
    return db_employee

@router.get(
    "/",
    response_model=list[EmployeeResponse],
    summary="List all employees",
)
def list_employees(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    employees = db.query(Employee).offset(skip).limit(limit).all()
    logger.debug("Listed %d employees (skip=%d, limit=%d)", len(employees), skip, limit)
    return employees

@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID",
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        logger.warning("Employee not found: id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found.",
        )
    return employee

@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update an employee",
)
def update_employee(
    employee_id: int,
    employee_update: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        logger.warning("Update failed — employee not found: id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found.",
        )

    update_data = employee_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    logger.info("Employee updated: id=%s fields=%s", employee_id, list(update_data.keys()))
    return employee

@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an employee",
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        logger.warning("Delete failed — employee not found: id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found.",
        )

    db.delete(employee)
    db.commit()
    logger.info("Employee deleted: id=%s", employee_id)
    return None
