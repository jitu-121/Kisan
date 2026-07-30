"""
Database initialization and session management using SQLAlchemy ORM.
Engine is configured for SQLite, allowing future migration to server-based DB
(PostgreSQL/MySQL) via connection string change.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "kisan.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """
    Import all ORM models and create table metadata if not existing.
    """
    import database.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
