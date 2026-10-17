from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
)
from app.auth_utils.security import (
    get_current_user,
    require_role,
    hash_password,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    email = str(data.email).lower()

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    new_user = User(
        full_name=data.full_name,
        email=email,
        hashed_password=hash_password(data.password),
        role="investigator",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    email = str(data.email).lower()

    existing_user = db.query(User).filter(User.email == email).first()

    if not existing_user or not verify_password(
        data.password, existing_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not existing_user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive",
        )

    token = create_access_token(
        existing_user.id,
        existing_user.role,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/admin-check")
def admin_check(
    current_user: User = Depends(require_role("admin")),
):
    return {
        "message": "Admin access verified",
        "user_id": current_user.id,
        "role": current_user.role,
    }
