from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db, User, SessionToken
from models.auth import UserRegisterRequest, UserLoginRequest, UserResponse, AuthResponse
from auth.security import (
    get_password_hash, authenticate_user, create_access_token,
    get_current_user
)
from config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": db_user.id}, expires_delta=access_token_expires
    )
    
    # Store session token
    session_token = SessionToken(
        user_id=db_user.id,
        token_hash=get_password_hash(access_token),
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(session_token)
    db.commit()
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(db_user)
    )

@router.post("/login", response_model=AuthResponse)
async def login(user_data: UserLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Store session token
    session_token = SessionToken(
        user_id=user.id,
        token_hash=get_password_hash(access_token),
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(session_token)
    db.commit()
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(user)
    )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Revoke all user's active session tokens
    db.query(SessionToken).filter(
        SessionToken.user_id == current_user.id,
        SessionToken.revoked_at.is_(None)
    ).update({SessionToken.revoked_at: datetime.utcnow()})
    
    db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)