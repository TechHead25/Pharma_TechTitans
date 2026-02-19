from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# SQLite database setup
DATABASE_URL = "sqlite:///./pharmaguard.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    email_verification_code = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VCFRecord(Base):
    __tablename__ = "vcf_records"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    username = Column(String, index=True)
    filename = Column(String)
    file_path = Column(String)
    analyzed_drugs = Column(String)  # Comma-separated drug IDs
    vcf_content = Column(Text, nullable=True)  # Raw VCF text content
    analysis_result = Column(Text)  # JSON string of analysis results
    phenotypes = Column(Text)  # JSON string of detected phenotypes
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, analyzing, completed, failed


# Create tables
Base.metadata.create_all(bind=engine)


def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
