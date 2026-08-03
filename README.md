# 📋 Attendance System API

A RESTful attendance management system built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

## Quick Start

### 1. Prerequisites
- Python 3.10+
- PostgreSQL running locally (or a remote instance)

### 2. Create the Database
```sql
CREATE DATABASE attendance_db;
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database URL (optional)
Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/attendance_db
```

### 5. Run the Server
```bash
uvicorn app.main:app --reload
```

### 6. Open the Docs
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## API Endpoints

### Employees
| Method | Endpoint                  | Description          |
|--------|---------------------------|----------------------|
| POST   | `/api/employees/`         | Create employee      |
| GET    | `/api/employees/`         | List all employees   |
| GET    | `/api/employees/{id}`     | Get employee by ID   |
| PUT    | `/api/employees/{id}`     | Update employee      |
| DELETE | `/api/employees/{id}`     | Delete employee      |

### Attendance
| Method | Endpoint                          | Description                |
|--------|-----------------------------------|----------------------------|
| POST   | `/api/attendance/check-in`        | Record check-in            |
| POST   | `/api/attendance/check-out/{id}`  | Record check-out           |
| GET    | `/api/attendance/`                | List records (date filter) |
| GET    | `/api/attendance/employee/{id}`   | Records for an employee    |
| GET    | `/api/attendance/report`          | Daily summary report       |

## Deployment

### Deploy to Render (Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/attendance-system.git
   git push -u origin main
   ```

2. **Create a PostgreSQL database on Render**
   - Go to [render.com](https://render.com) → New → PostgreSQL
   - Copy the **Internal Database URL**

3. **Create a Web Service on Render**
   - New → Web Service → connect your GitHub repo
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add env variable: `DATABASE_URL` = *(paste the Internal Database URL)*
   - Click **Deploy**

4. Your API is live at `https://your-app.onrender.com/docs`

### Deploy to Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add a **PostgreSQL** plugin (one click)
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Railway auto-injects `DATABASE_URL` — deploy!

### Deploy to a VPS (DigitalOcean / AWS / Linode)

```bash
# On your server:
sudo apt update && sudo apt install postgresql python3-pip python3-venv
git clone <your-repo> && cd attendance-system
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt gunicorn

# Create the database:
sudo -u postgres psql -c "CREATE DATABASE attendance_db;"

# Run in production:
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Use **Nginx** as a reverse proxy and **systemd** to keep it running.

## Project Structure
```
attendance system/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py         # Configuration
│   ├── database.py       # SQLAlchemy setup
│   ├── models.py         # ORM models
│   ├── schemas.py        # Pydantic schemas
│   └── routers/
│       ├── __init__.py
│       ├── employees.py  # Employee CRUD
│       └── attendance.py # Attendance endpoints
├── static/
│   ├── app.js            # Frontend JavaScript app logic
│   ├── index.html        # Single-page application UI
│   └── style.css         # Light-theme styling
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules
├── Procfile              # Platform start command
├── requirements.txt      # Python dependencies
├── DOCUMENTATION.md      # Full documentation
└── README.md
```

## License
MIT
