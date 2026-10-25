from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "running", "msg": "MuleShield AI Backend is Active"}

@router.get("/")
@router.get("/login")
async def login_page():
    return FileResponse("Loginpage.html")

@router.get("/dashboard")
async def dashboard():
    return FileResponse("index.html")

@router.get("/register")
async def signup_page():
    return FileResponse("Signup.html")