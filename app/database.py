"""
database.py
-----------
Sets up the SQLAlchemy engine, session factory, and declarative Base.

- `engine`       : The SQLAlchemy engine connected to PostgreSQL.
- `SessionLocal`  : A configured session factory (each call produces a new Session).
- `Base`          : Declarative base class — all ORM models inherit from this.
- `get_db()`      : FastAPI dependency that yields a database session and ensures
                    it is closed after the request completes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL

# Create the SQLAlchemy engine.
# `pool_pre_ping=True` ensures stale connections are recycled automatically.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory: calling SessionLocal() returns a new Session object.
# `autocommit=False` — we control commits explicitly.
# `autoflush=False`  — we flush manually or on commit, avoiding surprises.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM model classes.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy database session.

    Usage in a route:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...

    The `yield` makes this a generator-based dependency.
    FastAPI calls `next()` to get the session, and after the response
    is sent, it continues past the yield into the `finally` block
    to close the session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
