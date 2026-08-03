"""
streamlit_app.py
----------------
Streamlit frontend for the Attendance System.
Connects to the FastAPI backend API to manage employees and attendance.

Run locally:
    streamlit run streamlit_app.py
"""

import os
import requests
import datetime
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────
# Page Configuration & Light Theme Styling
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Attendance System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Light Theme Styling
st.markdown(
    """
    <style>
    /* Main container background */
    .stApp {
        background-color: #f8f9fc;
        color: #1a1d2e;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e8ecf4;
    }
    
    /* Metrics card styling */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    /* Button primary styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    /* Hide default Streamlit footer padding */
    .footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Base URL for FastAPI Backend
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

# ─────────────────────────────────────────────────────────────
# API Helper Functions
# ─────────────────────────────────────────────────────────────

def fetch_data(endpoint: str, params: dict = None):
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        st.error(f"API Error ({response.status_code}): {response.text}")
    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Cannot connect to FastAPI backend at `{API_URL}`. Ensure FastAPI server is running!")
    except Exception as e:
        st.error(f"Error: {e}")
    return None

def post_data(endpoint: str, payload: dict):
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=5)
        if response.status_code in (200, 201):
            return response.json(), None
        return None, response.json().get("detail", "Error processing request.")
    except Exception as e:
        return None, str(e)

def put_data(endpoint: str, payload: dict):
    try:
        response = requests.put(f"{API_URL}{endpoint}", json=payload, timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return None, response.json().get("detail", "Error processing request.")
    except Exception as e:
        return None, str(e)

def delete_data(endpoint: str):
    try:
        response = requests.delete(f"{API_URL}{endpoint}", timeout=5)
        if response.status_code == 204:
            return True, None
        return False, response.json().get("detail", "Error deleting record.")
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────────────────────

st.sidebar.title("📋 Attendee")
st.sidebar.caption("Attendance Management System")

menu = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "👥 Employees", "⏱️ Attendance Check-In/Out", "📈 Daily Reports"],
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Backend API URL:** `{API_URL}`")

# ─────────────────────────────────────────────────────────────
# 1. Dashboard Page
# ─────────────────────────────────────────────────────────────

if menu == "📊 Dashboard":
    st.title("📊 Today's Dashboard")
    st.write(f"Overview for **{datetime.date.today().strftime('%B %d, %Y')}**")

    # Fetch stats
    employees = fetch_data("/employees/") or []
    report = fetch_data(f"/attendance/report?report_date={datetime.date.today()}") or {}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Employees", len(employees))
    with col2:
        st.metric("Present Today", report.get("total_present", 0))
    with col3:
        st.metric("Late Today", report.get("total_late", 0))
    with col4:
        st.metric("Absent Today", report.get("total_absent", 0))

    st.markdown("---")
    st.subheader("Today's Attendance Logs")

    records = report.get("records", [])
    if records:
        df = pd.DataFrame(records)
        # Reorder / format columns
        df = df[["id", "employee_id", "check_in", "check_out", "status"]]
        df["check_in"] = pd.to_datetime(df["check_in"]).dt.strftime("%H:%M:%S")
        df["check_out"] = pd.to_datetime(df["check_out"]).dt.strftime("%H:%M:%S").fillna("—")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No attendance records logged for today yet.")

# ─────────────────────────────────────────────────────────────
# 2. Employees Page
# ─────────────────────────────────────────────────────────────

elif menu == "👥 Employees":
    st.title("👥 Employee Directory")

    tab_list, tab_add, tab_edit = st.tabs(["List Employees", "➕ Add Employee", "✏️ Edit / Delete"])

    employees = fetch_data("/employees/") or []

    with tab_list:
        if employees:
            df = pd.DataFrame(employees)
            df = df[["id", "name", "email", "department", "created_at"]]
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No employees registered yet.")

    with tab_add:
        st.subheader("Register New Employee")
        with st.form("add_emp_form", clear_on_submit=True):
            name = st.text_input("Full Name *")
            email = st.text_input("Email Address *")
            department = st.text_input("Department (Optional)")
            submitted = st.form_submit_button("Add Employee")

            if submitted:
                if not name or not email:
                    st.warning("Please fill in all required fields (*).")
                else:
                    res, err = post_data("/employees/", {"name": name, "email": email, "department": department or None})
                    if res:
                        st.success(f"Successfully added employee: **{name}** (ID: {res['id']})")
                        st.rerun()
                    else:
                        st.error(err)

    with tab_edit:
        st.subheader("Manage Existing Employee")
        if employees:
            emp_map = {f"ID {e['id']}: {e['name']} ({e['email']})": e for e in employees}
            selected_label = st.selectbox("Select Employee to Manage", list(emp_map.keys()))
            selected_emp = emp_map[selected_label]

            col_edit, col_del = st.columns([2, 1])

            with col_edit:
                with st.form("edit_emp_form"):
                    new_name = st.text_input("Name", value=selected_emp["name"])
                    new_email = st.text_input("Email", value=selected_emp["email"])
                    new_dept = st.text_input("Department", value=selected_emp["department"] or "")
                    update_sub = st.form_submit_button("Update Employee")

                    if update_sub:
                        res, err = put_data(f"/employees/{selected_emp['id']}", {
                            "name": new_name,
                            "email": new_email,
                            "department": new_dept or None
                        })
                        if res:
                            st.success("Employee updated successfully!")
                            st.rerun()
                        else:
                            st.error(err)

            with col_del:
                st.markdown("**Danger Zone**")
                if st.button("❌ Delete Employee", type="secondary"):
                    success, err = delete_data(f"/employees/{selected_emp['id']}")
                    if success:
                        st.success("Employee deleted!")
                        st.rerun()
                    else:
                        st.error(err)
        else:
            st.info("No employees available to edit.")

# ─────────────────────────────────────────────────────────────
# 3. Attendance Check-In/Out Page
# ─────────────────────────────────────────────────────────────

elif menu == "⏱️ Attendance Check-In/Out":
    st.title("⏱️ Attendance Check-In & Check-Out")

    employees = fetch_data("/employees/") or []

    if not employees:
        st.warning("Please add employees first before recording attendance.")
    else:
        emp_options = {f"ID {e['id']}: {e['name']}": e['id'] for e in employees}

        col_in, col_out = st.columns(2)

        with col_in:
            st.subheader("📥 Check-In")
            selected_emp_label = st.selectbox("Select Employee for Check-In", list(emp_options.keys()))
            emp_id = emp_options[selected_emp_label]
            status_val = st.selectbox("Status", ["present", "late"])

            if st.button("Check In Employee", type="primary"):
                res, err = post_data("/attendance/check-in", {"employee_id": emp_id, "status": status_val})
                if res:
                    st.success(f"Checked in successfully at {res['check_in'].split('T')[1][:8]}!")
                    st.rerun()
                else:
                    st.error(err)

        with col_out:
            st.subheader("📤 Check-Out")
            records = fetch_data(f"/attendance/?record_date={datetime.date.today()}") or []
            # Filter to active check-ins (check_out is null)
            active_records = [r for r in records if r["check_out"] is None]

            if active_records:
                record_options = {f"Record #{r['id']} (Emp ID {r['employee_id']}) - In at {r['check_in'].split('T')[1][:8]}": r['id'] for r in active_records}
                selected_record_label = st.selectbox("Select Active Check-In", list(record_options.keys()))
                record_id = record_options[selected_record_label]

                if st.button("Check Out Employee"):
                    res, err = post_data(f"/attendance/check-out/{record_id}", {})
                    if res:
                        st.success(f"Checked out successfully at {res['check_out'].split('T')[1][:8]}!")
                        st.rerun()
                    else:
                        st.error(err)
            else:
                st.info("No active check-ins requiring check-out today.")

# ─────────────────────────────────────────────────────────────
# 4. Daily Reports Page
# ─────────────────────────────────────────────────────────────

elif menu == "📈 Daily Reports":
    st.title("📈 Attendance Reports")

    selected_date = st.date_input("Select Date for Report", value=datetime.date.today())

    if selected_date:
        report = fetch_data(f"/attendance/report?report_date={selected_date}") or {}

        st.subheader(f"Report for {selected_date.strftime('%B %d, %Y')}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Present", report.get("total_present", 0))
        with col2:
            st.metric("Late", report.get("total_late", 0))
        with col3:
            st.metric("Absent", report.get("total_absent", 0))

        records = report.get("records", [])
        if records:
            df = pd.DataFrame(records)
            df = df[["id", "employee_id", "date", "check_in", "check_out", "status"]]
            df["check_in"] = pd.to_datetime(df["check_in"]).dt.strftime("%H:%M:%S")
            df["check_out"] = pd.to_datetime(df["check_out"]).dt.strftime("%H:%M:%S").fillna("—")
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"No records found for {selected_date}.")
