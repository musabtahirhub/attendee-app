"""
config.py
---------
Application configuration settings.

The DATABASE_URL is read from the environment variable 'DATABASE_URL'.
If not set, it falls back to a default local PostgreSQL connection string.

To override, create a .env file in the project root or export the variable:
    export DATABASE_URL="postgresql://user:password@host:port/dbname"
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if present)
load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/attendance_db",
)
