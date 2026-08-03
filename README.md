# 📋 Attendee — Attendance Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1.svg?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A high-performance, full-stack attendance management system built with **FastAPI**, **SQLAlchemy ORM**, and **PostgreSQL**. Features a RESTful API backend alongside a responsive, light-themed single-page frontend served directly by FastAPI.

---

## ✨ Features

- 👥 **Employee Directory Management**: Complete CRUD operations (Create, Read, Update, Delete) with duplicate email prevention and automatic cascade cleanups.
- ⏱️ **Daily Check-In & Check-Out**: Automated time recording with guards against duplicate same-day check-ins and invalid double check-outs.
- 📊 **Real-Time Attendance Summaries**: Automated daily report aggregation categorising employee statuses into *Present*, *Late*, and *Absent*.
- 🎨 **Built-In Responsive Frontend**: Modern, light-themed Single Page Application (SPA) built with vanilla HTML5, CSS3, and JavaScript—zero extra frontend server required.
- 📖 **Interactive API Documentation**: Auto-generated OpenAPI (Swagger UI) and ReDoc interfaces available out of the box.
- ☁️ **Cloud Deployment Ready**: Out-of-the-box configuration with `Procfile`, environment variable management (`python-dotenv`), and static file mounting.

---

## 🛠️ Tech Stack

| Domain | Technology | Description |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Asynchronous, high-performance Python web framework |
| **Database ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) | Declarative relational mapping with connection pooling |
| **Database** | [PostgreSQL](https://www.postgresql.org/) | Enterprise relational database management system |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Strict data parsing and model validation |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | High-performance ASGI server implementation |
| **Frontend** | HTML5 / CSS3 / JavaScript | Responsive SPA with light glassmorphism aesthetics |

---

## 📁 Repository Structure

```
attendee-app/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Application entry point & middleware
│   ├── config.py            # Environment-driven database configuration
│   ├── database.py          # SQLAlchemy engine, session factory & dependencies
│   ├── models.py            # SQLAlchemy database models (Employee, AttendanceRecord)
│   ├── schemas.py           # Pydantic validation & serialization schemas
│   └── routers/
│       ├── __init__.py      # Router package init
│       ├── employees.py     # Employee management endpoints (/api/employees)
│       └── attendance.py    # Check-in, check-out & report endpoints (/api/attendance)
├── static/
│   ├── index.html           # Single Page Application UI
│   ├── style.css            # Light theme design tokens & layout
│   └── app.js               # Async API client & dynamic UI logic
├── .env.example             # Template for environment configuration
├── .gitignore               # Ignored runtime & build artifacts
├── Procfile                 # Process configuration for cloud platforms (Render/Railway)
├── requirements.txt         # Production dependencies
└── README.md                # System documentation
```

---

## ⚙️ Configuration & Environment Variables

The application reads configuration parameters from environment variables or a local `.env` file via `python-dotenv`.

| Variable | Required | Default Value | Description |
|---|---|---|---|
| `DATABASE_URL` | No | `postgresql://postgres:postgres@localhost:5432/attendance_db` | PostgreSQL connection string |
| `PORT` | No | `8000` | Port for Uvicorn server |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- PostgreSQL server running locally or remotely

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and set your PostgreSQL connection string:
```bash
cp .env.example .env
```

### 3. Run Development Server
```bash
uvicorn app.main:app --reload
```

- **Web Application UI**: `http://127.0.0.1:8000/`
- **Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Specifications**: `http://127.0.0.1:8000/redoc`

---

## 🔌 API Overview

All API endpoints are prefixed with `/api`.

### Employees Endpoint (`/api/employees`)
- `POST /api/employees/` — Register a new employee
- `GET /api/employees/` — List all registered employees (supports pagination)
- `GET /api/employees/{id}` — Fetch details for a specific employee
- `PUT /api/employees/{id}` — Update an existing employee's details
- `DELETE /api/employees/{id}` — Delete employee and cascade-delete attendance history

### Attendance Endpoint (`/api/attendance`)
- `POST /api/attendance/check-in` — Record daily check-in for an employee
- `POST /api/attendance/check-out/{record_id}` — Record check-out timestamp
- `GET /api/attendance/` — Retrieve attendance logs (supports date filtering)
- `GET /api/attendance/employee/{employee_id}` — Retrieve attendance log for a specific employee
- `GET /api/attendance/report` — Fetch daily summary metrics (*present*, *late*, *absent*)

---

## ☁️ Deployment

### Render / Railway (PaaS)
1. Connect repository `musabtahirhub/attendee-app`.
2. Provision a **PostgreSQL** database instance.
3. Configure Environment Variable:
   - `DATABASE_URL` = `<your_postgres_connection_string>`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### VPS (Ubuntu/Debian)
Run behind Gunicorn and Nginx:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).
