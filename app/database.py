from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL
from app.logger import get_logger

logger = get_logger(__name__)

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

