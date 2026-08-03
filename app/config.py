import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/attendance_db",
)
