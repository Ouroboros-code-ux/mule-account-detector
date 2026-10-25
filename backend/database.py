import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from .config import DATABASE_URL
from .models import Base, User

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        users_to_seed = [
            ("admin", os.getenv("ADMIN_PASSWORD") or "admin123", "admin@muleshield.ai"),
            ("analyst", "analyst123", "analyst@muleshield.ai"),
            ("demo", "demo123", "demo@muleshield.ai"),
            ("sahil", "4197546", "sahil@muleshield.ai")
        ]
        for uname, pwd, email in users_to_seed:
            existing = db.query(User).filter(User.username == uname).first()
            if not existing:
                salt = bcrypt.gensalt()
                hashed_pw = bcrypt.hashpw(pwd.encode('utf-8'), salt)
                new_user = User(
                    username=uname,
                    password=hashed_pw,
                    email=email,
                    is_verified=1
                )
                db.add(new_user)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database users: {e}")
    finally:
        db.close()
