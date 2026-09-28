from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash
from app.api.deps import RoleChecker

router = APIRouter(prefix="/users", tags=["Users Management"])

@router.get("", response_model=List[UserResponse], dependencies=[Depends(RoleChecker(["ADMIN", "SECURITY_ANALYST"]))])
def list_users(db: Session = Depends(get_db)):
    """List all registered system users (Admins & Analysts only)."""
    return db.query(User).order_by(User.id.asc()).all()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RoleChecker(["ADMIN"]))])
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new operator/analyst user (Admin only)."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = User(
        name=user_in.name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role.value,
        is_active=user_in.is_active,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(RoleChecker(["ADMIN"]))])
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    """Update user role, status, or details (Admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_in.name is not None:
        user.name = user_in.name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.role is not None:
        user.role = user_in.role.value
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password is not None:
        user.password_hash = get_password_hash(user_in.password)

    db.commit()
    db.refresh(user)
    return user
