"""
routers/employees.py
--------------------
CRUD (Create, Read, Update, Delete) endpoints for managing employees.

All endpoints are prefixed with `/employees` (set when including the router
in main.py) and tagged under "Employees" in the Swagger docs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ────────────────────────── CREATE ──────────────────────────


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Register a new employee in the system.

    - **name**: Full name (required).
    - **email**: Must be unique across all employees (required).
    - **department**: Optional department name.

    Returns the newly created employee with its generated `id` and `created_at`.
    """
    # Check for duplicate email
    existing = db.query(Employee).filter(Employee.email == employee.email).first()
    if existing:
        logger.warning("Duplicate email rejected: %s", employee.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An employee with email '{employee.email}' already exists.",
        )

    # Create ORM instance from the validated Pydantic schema
    db_employee = Employee(
        name=employee.name,
        email=employee.email,
        department=employee.department,
    )
    db.add(db_employee)   # Stage the INSERT
    db.commit()           # Execute the INSERT
    db.refresh(db_employee)  # Reload to get DB-generated values (id, created_at)
    logger.info("Employee created: id=%s name='%s' email='%s'", db_employee.id, db_employee.name, db_employee.email)
    return db_employee


# ────────────────────────── READ (list) ──────────────────────────


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
    """
    Retrieve a paginated list of all employees.

    - **skip**: Number of records to skip (for pagination).
    - **limit**: Maximum number of records to return (default 100).
    """
    employees = db.query(Employee).offset(skip).limit(limit).all()
    logger.debug("Listed %d employees (skip=%d, limit=%d)", len(employees), skip, limit)
    return employees


# ────────────────────────── READ (single) ──────────────────────────


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID",
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single employee by their unique ID.

    Raises **404** if the employee does not exist.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        logger.warning("Employee not found: id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found.",
        )
    return employee


# ────────────────────────── UPDATE ──────────────────────────


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
    """
    Update one or more fields of an existing employee.

    Only the fields provided in the request body will be updated;
    omitted fields remain unchanged.

    Raises **404** if the employee does not exist.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        logger.warning("Update failed — employee not found: id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {employee_id} not found.",
        )

    # `exclude_unset=True` ensures only explicitly-provided fields are updated.
    update_data = employee_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    logger.info("Employee updated: id=%s fields=%s", employee_id, list(update_data.keys()))
    return employee


# ────────────────────────── DELETE ──────────────────────────


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an employee",
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """
    Permanently delete an employee and all their associated attendance records
    (cascade delete is configured in the ORM model).

    Raises **404** if the employee does not exist.
    """
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
    return None  # 204 No Content — no body returned
