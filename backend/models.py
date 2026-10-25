from sqlalchemy import Column, String, Integer, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Report(Base):
    __tablename__ = "reports"
    
    address = Column(String(42), primary_key=True, index=True)
    reason = Column(String(500))
    timestamp = Column(Integer)

class ReportLog(Base):
    __tablename__ = "report_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(255), index=True)
    address = Column(String(42), index=True)
    reason = Column(String(500))
    timestamp = Column(Integer)
    verified = Column(Integer, default=0)

class User(Base):
    __tablename__ = "users"
    
    username = Column(String(255), primary_key=True, index=True)
    password = Column(String(255))
    email = Column(String(255), unique=True, index=True)
    is_verified = Column(Integer, default=0)
    verification_token = Column(String(255))