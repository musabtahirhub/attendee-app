# 🗄️ Alembic Database Migration Guide

This document explains the database migration setup added to the **Attendee** project using **Alembic** and **SQLAlchemy**.

---

## 📌 Overview

Previously, database tables were created dynamically on application startup via `Base.metadata.create_all(bind=engine)`. While this creates initial tables, it cannot track schema changes over time (such as adding columns, changing data types, or creating new indexes) without dropping existing data.

To solve this, **Alembic** has been integrated into the project. Alembic provides version-controlled database migrations, allowing schema upgrades and rollbacks without data loss.

---

## 📁 Files Created & Configured

| File Path | Description |
|---|---|
| [`requirements.txt`](file:///c:/Users/Musab%20Tahir/Desktop/attendee-app/requirements.txt) | Updated to include `alembic` dependency. |
| [`alembic.ini`](file:///c:/Users/Musab%20Tahir/Desktop/attendee-app/alembic.ini) | Primary configuration file for Alembic, specifying migration folder paths and loggers. |
| [`alembic/env.py`](file:///c:/Users/Musab%20Tahir/Desktop/attendee-app/alembic/env.py) | Environment script that hooks Alembic into `app.config.DATABASE_URL` and connects `target_metadata` to `Base.metadata` from `app.models`. |
| [`alembic/script.py.mako`](file:///c:/Users/Musab%20Tahir/Desktop/attendee-app/alembic/script.py.mako) | Revision script template used when generating new migration files. |
| [`alembic/versions/001_initial_migration.py`](file:///c:/Users/Musab%20Tahir/Desktop/attendee-app/alembic/versions/001_initial_migration.py) | Initial baseline migration creating `employees` and `attendance_records` tables with all constraints and indexes. |

---

## 🛠️ Initial Migration Breakdown

The baseline revision `001_initial_migration.py` sets up the initial PostgreSQL database schema:

1. **`employees` Table**:
   - `id` (Integer, Primary Key, Autoincrement, Indexed)
   - `name` (String 100, Non-null)
   - `email` (String 150, Unique, Non-null, Indexed)
   - `department` (String 100, Nullable)
   - `created_at` (DateTime)

2. **`attendance_records` Table**:
   - `id` (Integer, Primary Key, Autoincrement, Indexed)
   - `employee_id` (Integer, Foreign Key → `employees.id` ON DELETE CASCADE, Indexed)
   - `date` (Date, Non-null)
   - `check_in` (DateTime, Non-null)
   - `check_out` (DateTime, Nullable)
   - `status` (String 20, Non-null)

---

## 🚀 Commands & Usage

### 1. Apply Migrations
To bring your database schema up to the latest version:
```bash
alembic upgrade head
```

### 2. Generate a New Migration
When you add or modify models in [`app/models.py`](file:///c:/Users/Musab%20Tahir/Desktop/attendee-app/app/models.py), generate a new migration automatically:
```bash
alembic revision --autogenerate -m "add_phone_number_to_employee"
```
*Note: Always inspect the generated script in `alembic/versions/` before applying it.*

### 3. Roll Back a Migration
To undo the last applied migration:
```bash
alembic downgrade -1
```

To roll back all migrations completely:
```bash
alembic downgrade base
```

### 4. Check Current Migration Status
To view the current database revision:
```bash
alembic current
```

To view the history of all migration revisions:
```bash
alembic history
```
