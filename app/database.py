import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

from app.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

raw_database_url = os.getenv("DATABASE_URL")

if raw_database_url:
    if raw_database_url.startswith("postgres://"):
        raw_database_url = raw_database_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = raw_database_url
else:
    db_driver = os.getenv("DB_DRIVER", "postgresql+psycopg2")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port_str = os.getenv("DB_PORT", "5432")
    db_port = int(db_port_str) if db_port_str.isdigit() else 5432
    db_name = os.getenv("DB_NAME", "attendance_db")
    db_sslmode = os.getenv("DB_SSLMODE", "require")

    query_params = {"sslmode": db_sslmode} if db_sslmode else {}

    DATABASE_URL = URL.create(
        drivername=db_driver,
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port,
        database=db_name,
        query=query_params,
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    logger.debug("DB session opened: %s", id(db))
    try:
        yield db
    except Exception:
        logger.exception("Unhandled error during DB session — rolling back")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("DB session closed: %s", id(db))
