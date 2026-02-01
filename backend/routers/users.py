"""
Users Router - Authentication and User Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from database import get_db
import models
import schemas
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_admin, require_manager_or_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Log the login
    audit_log = models.AuditLog(
        action="user_login",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details=f"User {user.email} logged in"
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/register", response_model=schemas.UserResponse)
async def register(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if email exists
    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = models.User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Log the registration
    audit_log = models.AuditLog(
        action="user_registered",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        details=f"New user {user.email} registered with role {user.role.value}"
    )
    db.add(audit_log)
    db.commit()
    
    return user


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: models.User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.get("/", response_model=List[schemas.UserResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_admin)
):
    """Get all users (Manager/Admin only)"""
    return db.query(models.User).all()


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user by ID"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Update user (Admin only)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    
    # Log the update
    audit_log = models.AuditLog(
        action="user_updated",
        entity_type="user",
        entity_id=user.id,
        user_id=current_user.id,
        details=f"User {user.email} updated"
    )
    db.add(audit_log)
    db.commit()
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Delete user (Admin only)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    email = user.email
    db.delete(user)
    db.commit()
    
    # Log the deletion
    audit_log = models.AuditLog(
        action="user_deleted",
        entity_type="user",
        entity_id=user_id,
        user_id=current_user.id,
        details=f"User {email} deleted"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "User deleted successfully"}
