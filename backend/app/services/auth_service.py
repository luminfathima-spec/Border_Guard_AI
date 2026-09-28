from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.audit import AuditLog
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def login(db: Session, login_data: LoginRequest, ip_address: Optional[str] = None) -> Token:
        user = AuthService.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Contact platform administrator.",
            )

        token_str = create_access_token(
            subject=user.email,
            role=user.role,
            name=user.name,
        )

        # Log authentication audit trail
        audit_log = AuditLog(
            user_id=user.id,
            user_email=user.email,
            action="LOGIN_SUCCESS",
            resource_type="User",
            resource_id=str(user.id),
            details={"role": user.role, "name": user.name},
            ip_address=ip_address or "127.0.0.1",
        )
        db.add(audit_log)
        db.commit()

        return Token(
            access_token=token_str,
            token_type="bearer",
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=UserResponse.model_validate(user),
        )
