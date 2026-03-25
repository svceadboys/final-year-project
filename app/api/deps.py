import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from dotenv import load_dotenv

from app.core.security import ALGORITHM, SECRET_KEY

load_dotenv()

# We expect the token to be sent in the Authorization header: `Bearer <token>`
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_admin(token: str = Depends(oauth2_scheme)):
    """
    Dependency to verify the JWT token and ensure the user is an admin.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
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
        
    # In a full system we would fetch the user from the DB here.
    # Since we have a single admin, we just verify the username matches the env.
    admin_username = os.getenv("ADMIN_USERNAME", "admin@ecosort.com")
    if username != admin_username:
        raise credentials_exception
        
    return username
