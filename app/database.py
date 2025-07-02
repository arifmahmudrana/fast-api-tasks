# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv


def init_db():
    load_dotenv()
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

    if not SQLALCHEMY_DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set or is empty")

    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        return engine, SessionLocal, Base
    except Exception as e:
        raise ValueError(f"Failed to initialize database: {str(e)}")


# Initialize at module level for normal usage
engine, SessionLocal, Base = init_db()
