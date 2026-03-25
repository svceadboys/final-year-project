import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv

from app.core.security import verify_password, create_access_token

load_dotenv()

router = APIRouter()

class LoginData(BaseModel):
    username: str
    password: str

@router.post("/login", summary="Login to get access token")
def login_for_access_token(data: LoginData):
    """
    Checks the submitted username and password against the environment variables.
    If valid, returns a JWT access token.
    """
    admin_username = os.getenv("ADMIN_USERNAME", "admin@ecosort.com")
    
    # We provide a default hash for 'admin123' if not set in .env
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH", "$2b$12$ZoKU0UYZN7URdRuDLujJ3e6BnMUijpmHumHgfI6re7KzstsCZsptC")

    if data.username != admin_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not verify_password(data.password, admin_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(subject=admin_username)
    return {"access_token": access_token, "token_type": "bearer"}
