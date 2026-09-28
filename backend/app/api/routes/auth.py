from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate security personnel with email/password and issue cryptographically signed JWT token.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return AuthService.login(db, login_data, ip_address=client_ip)

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get profile information of currently authenticated user.
    """
    return current_user
