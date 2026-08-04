from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.logger import get_logger
from app.queries import get_employee_by_id, get_employee_by_email

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee",
)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    logger.info("POST /employees — create request for email='%s'", employee.email)
    try:
        existing = get_employee_by_email(db, employee.email)
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
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating employee")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error occurred. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error while creating employee")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


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
    logger.info("GET /employees — list (skip=%d, limit=%d)", skip, limit)
    try:
        employees = db.query(Employee).offset(skip).limit(limit).all()
        logger.debug("Listed %d employees", len(employees))
        return employees
    except SQLAlchemyError:
        logger.exception("Database error while listing employees")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error occurred. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error while listing employees")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID",
)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    logger.info("GET /employees/%s — fetch by ID", employee_id)
    try:
        employee = get_employee_by_id(db, employee_id)
        if not employee:
            logger.warning("Employee not found: id=%s", employee_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee with id {employee_id} not found.",
            )
        return employee
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("Database error while fetching employee id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error occurred. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error while fetching employee id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


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
    logger.info("PUT /employees/%s — update request", employee_id)
    try:
        employee = get_employee_by_id(db, employee_id)
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
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating employee id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error occurred. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error while updating employee id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an employee",
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    logger.info("DELETE /employees/%s — delete request", employee_id)
    try:
        employee = get_employee_by_id(db, employee_id)
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
    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while deleting employee id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error occurred. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error while deleting employee id=%s", employee_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )
