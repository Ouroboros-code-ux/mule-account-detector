from datetime import datetime, timedelta
import secrets
import logging
from fastapi import APIRouter, HTTPException, Depends
from jose import jwt, JWTError
from ..database import get_db
from ..models import User
from ..internal_types import LoginRequest, SignupRequest
from ..config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, BASE_URL
)
from ..limiter import limiter
from fastapi import Request
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

async def get_optional_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username:
            return db.query(User).filter(User.username == username).first()
    except:
        pass
    return None

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

router = APIRouter()
logger = logging.getLogger(__name__)

import bcrypt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def send_verification_email(email: str, otp: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        err = "SMTP credentials missing in Environment Variables."
        logger.warning(f"Email to {email} not sent: {err}")
        return False, err
    
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = email
    msg['Subject'] = f"{otp} is your MuleShield AI Verification Code"
    
    body = f"""
    Hello,
    
    Thank you for registering with MuleShield AI.
    
    Your verification code is:
    
    {otp}
    
    Please enter this code on the signup page to activate your account.
    
    If you did not sign up for an account, please ignore this email.
    """
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        return True, ""
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send verification email to {email}: {error_msg}")
        return False, error_msg

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()

    if user:
        stored_pw = user.password
        if isinstance(stored_pw, str):
            stored_pw = stored_pw.encode('utf-8')
            
        if verify_password(credentials.password, stored_pw):
            if user.is_verified == 1:
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": credentials.username}, expires_delta=access_token_expires
                )
                return {"message": "Login successful.", "token": access_token}
            else:
                raise HTTPException(status_code=403, detail="Email not verified. Please sign up again to resend code.")
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

@router.post("/signup")
@limiter.limit("5/minute")
async def signup(request: Request, user: SignupRequest, db: Session = Depends(get_db)):
    
    existing_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    
    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    hashed_password = get_password_hash(user.password)

    if existing_user:
        if existing_user.is_verified == 1:
            raise HTTPException(status_code=400, detail="Account with this email or username already exists.")
        else:
            
            existing_user.verification_token = otp
            
            existing_user.password = hashed_password
            db.commit()
            
            email_sent, smtp_error = send_verification_email(existing_user.email, otp)
            if email_sent:
                return {
                    "message": "Verification code resent. Please check your email.",
                    "username": existing_user.username
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Found your account, but email failed: {smtp_error}. Please check your Render SMTP settings."
                )
    
    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    hashed_password = get_password_hash(user.password)
    
    try:
        new_user = User(
            username=user.username,
            password=hashed_password,
            email=user.email,
            is_verified=0,
            verification_token=otp
        )
        db.add(new_user)
        db.commit()
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.warning(f"User creation failed: {error_msg}")
        if "UNIQUE constraint failed" in error_msg:
            if "users.email" in error_msg:
                raise HTTPException(status_code=400, detail="An account with this email already exists.")
            else:
                raise HTTPException(status_code=400, detail="Username is already taken.")
        raise HTTPException(status_code=400, detail="Registration failed. Please try again.")
    
    logger.info(f"Verification token for {user.email}: {otp}")
    
    email_sent, smtp_error = send_verification_email(user.email, otp)
    
    if email_sent:
        return {"message": "Account created. Please enter the 6-digit code sent to your email."}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Account created, but email failed: {smtp_error}. Please check your Render Env Vars."
        )

@router.post("/api/verify-otp")
@limiter.limit("10/minute")
async def verify_otp(request: Request, data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    otp = str(data.get("otp", "")).strip()
    
    user = db.query(User).filter(
        (User.username == username) | (User.email == username),
        User.verification_token == otp
    ).first()
    
    if user:
        user.is_verified = 1
        db.commit()
        return {"message": "Email verified successfully."}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP code.")

@router.post("/api/resend-otp")
@limiter.limit("5/minute")
async def resend_otp(request: Request, data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_verified == 1:
        raise HTTPException(status_code=400, detail="Account is already verified.")
        
    otp = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    user.verification_token = otp
    db.commit()
    
    email_sent, smtp_error = send_verification_email(user.email, otp)
    if email_sent:
        return {"message": "New verification code sent."}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to send email: {smtp_error}. Check Render Env Vars."
        )

@router.get("/verify/{token}")
@limiter.limit("10/minute")
async def verify_email_page(request: Request, token: str):
    
    from fastapi.responses import FileResponse
    return FileResponse("Verify.html")

@router.get("/api/verify/{token}")
@limiter.limit("10/minute")
async def verify_email_api(request: Request, token: str, db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.verification_token == token).first()
    
    if user:
        user.is_verified = 1
        
        db.commit()
        return {"message": "Email verified successfully."}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")