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
        existing_user = db.query(User).filter(User.username == 'sahil').first()
        if not existing_user:
            salt = bcrypt.gensalt()
            admin_pw = os.getenv("ADMIN_PASSWORD")
            if not admin_pw:
                print("WARNING: ADMIN_PASSWORD is missing from environment. Using insecure dev password. Do not use in production!")
                admin_pw = "4197546"
            hashed_pw = bcrypt.hashpw(admin_pw.encode('utf-8'), salt)
            
            new_user = User(
                username='sahil',
                password=hashed_pw,
                email='sahil@muleshield.ai',
                is_verified=1
            )
            db.add(new_user)
            db.commit()
    finally:
        db.close()
