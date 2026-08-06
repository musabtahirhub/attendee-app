from datetime import datetime, date
import re
from typing import Optional
from langchain_core.tools import tool

from app.database import SessionLocal
from app import queries
from app.logger import get_logger

logger = get_logger(__name__)


def find_employee(db, query: str):
    query = str(query).strip()

    if query.isdigit():
        emp = queries.get_employee_by_id(db, int(query))
        if emp:
            return emp

    id_match = re.search(r'\b(\d+)\b', query)
    if id_match and any(keyword in query.lower() for keyword in ['id', 'employee', '#']):
        emp = queries.get_employee_by_id(db, int(id_match.group(1)))
        if emp:
            return emp

    return queries.get_employee_by_name(db, query)


@tool(description="Checks an employee's attendance status or approved leave for today given their Employee ID or Name (e.g. '1', 'ID 1', or 'Hassan Ali').")
def check_employee_status(employee_query: str) -> str:
    logger.info("Tool check_employee_status called for query='%s'", employee_query)
    db = SessionLocal()
    try:
        employee = find_employee(db, employee_query)
        if not employee:
            return f"Employee matching '{employee_query}' (by ID or Name) was not found."

        today = date.today()
        att_record = queries.get_attendance_by_employee_and_date(db, employee.id, today)
        if att_record:
            check_in_str = att_record.check_in.strftime("%H:%M:%S") if att_record.check_in else "N/A"
            check_out_str = att_record.check_out.strftime("%H:%M:%S") if att_record.check_out else "Not checked out yet"
            return (
                f"Employee {employee.name} (ID: {employee.id}, Dept: {employee.department or 'N/A'}) "
                f"is marked as '{att_record.status}' today ({today}). Check-in: {check_in_str}, Check-out: {check_out_str}."
            )

        leave_record = queries.get_approved_leave_by_employee_and_date(db, employee.id, today)
        if leave_record:
            return (
                f"Employee {employee.name} (ID: {employee.id}) is on APPROVED LEAVE today ({today}) "
                f"from {leave_record.start_date} to {leave_record.end_date}. Reason: {leave_record.reason}."
            )

        return (
            f"Employee {employee.name} (ID: {employee.id}) has no attendance or approved leave record for today ({today})."
        )
    except Exception as e:
        logger.exception("Error in check_employee_status tool")
        return f"Error checking status: {str(e)}"
    finally:
        db.close()


@tool(description="Submits a leave request for an employee by Employee ID or Name. Dates must be formatted as YYYY-MM-DD.")
def apply_employee_leave(employee_query: str, start_date: str, end_date: str, reason: str) -> str:
    logger.info("Tool apply_employee_leave called for query='%s', dates=%s to %s", employee_query, start_date, end_date)
    db = SessionLocal()
    try:
        employee = find_employee(db, employee_query)
        if not employee:
            return f"Employee matching '{employee_query}' (by ID or Name) was not found."

        try:
            start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD for start_date and end_date."

        if start_d > end_d:
            return "Start date cannot be after end date."

        leave_req = queries.create_leave_request(
            db,
            employee_id=employee.id,
            start_date=start_d,
            end_date=end_d,
            reason=reason,
        )
        return (
            f"Leave request created successfully for {employee.name} (ID: {employee.id})! "
            f"Leave ID: {leave_req.id}, Duration: {start_date} to {end_date}, Status: {leave_req.status}."
        )
    except Exception as e:
        logger.exception("Error in apply_employee_leave tool")
        db.rollback()
        return f"Error applying for leave: {str(e)}"
    finally:
        db.close()


@tool(description="Approves a pending leave request given the leave ID. User role must be 'manager' or 'admin'.")
def approve_employee_leave(leave_id: int, user_role: str) -> str:
    logger.info("Tool approve_employee_leave called for leave_id=%s, user_role='%s'", leave_id, user_role)
    if user_role.lower() not in ["manager", "admin"]:
        return f"Permission denied. Role '{user_role}' is not authorized to approve leave requests. Requires 'manager' or 'admin'."

    db = SessionLocal()
    try:
        approved_leave = queries.approve_leave_request(db, leave_id)
        if not approved_leave:
            return f"Leave request with ID {leave_id} was not found."

        employee = queries.get_employee_by_id(db, approved_leave.employee_id)
        emp_name = employee.name if employee else f"Employee ID {approved_leave.employee_id}"

        return (
            f"Leave request #{approved_leave.id} for {emp_name} has been APPROVED successfully by {user_role}!"
        )
    except Exception as e:
        logger.exception("Error in approve_employee_leave tool")
        db.rollback()
        return f"Error approving leave: {str(e)}"
    finally:
        db.close()


@tool(description="Lists all pending leave requests requiring approval. User role must be 'manager' or 'admin'.")
def list_pending_leaves(user_role: str) -> str:
    logger.info("Tool list_pending_leaves called for user_role='%s'", user_role)
    if user_role.lower() not in ["manager", "admin"]:
        return f"Permission denied. Role '{user_role}' is not authorized to view pending leave requests. Requires 'manager' or 'admin'."

    db = SessionLocal()
    try:
        pending_leaves = queries.get_pending_leaves(db)
        if not pending_leaves:
            return "There are currently no pending leave requests."

        results = ["Pending Leave Requests:"]
        for req in pending_leaves:
            emp = queries.get_employee_by_id(db, req.employee_id)
            emp_name = emp.name if emp else f"Employee #{req.employee_id}"
            results.append(
                f"- Leave ID #{req.id}: {emp_name} (ID: {req.employee_id}) | "
                f"Dates: {req.start_date} to {req.end_date} | Reason: {req.reason} | Status: {req.status}"
            )
        return "\n".join(results)
    except Exception as e:
        logger.exception("Error in list_pending_leaves tool")
        return f"Error fetching pending leave requests: {str(e)}"
    finally:
        db.close()


@tool(description="Checks the status and history of leave requests for an employee given their Employee ID or Name (e.g. '1', 'ID 1', or 'Hassan Ali').")
def check_my_leave_requests(employee_query: str) -> str:
    logger.info("Tool check_my_leave_requests called for query='%s'", employee_query)
    db = SessionLocal()
    try:
        employee = find_employee(db, employee_query)
        if not employee:
            return f"Employee matching '{employee_query}' (by ID or Name) was not found."

        leave_requests = queries.get_leave_requests_by_employee(db, employee.id)
        if not leave_requests:
            return f"No leave requests found for employee {employee.name} (ID: {employee.id})."

        results = [f"Leave Requests for {employee.name} (ID: {employee.id}):"]
        for req in leave_requests:
            results.append(
                f"- Leave ID #{req.id}: Status '{req.status.upper()}' | "
                f"Dates: {req.start_date} to {req.end_date} | Reason: {req.reason}"
            )
        return "\n".join(results)
    except Exception as e:
        logger.exception("Error in check_my_leave_requests tool")
        return f"Error fetching leave requests: {str(e)}"
    finally:
        db.close()
