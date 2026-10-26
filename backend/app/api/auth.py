from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.auth_utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, SwaggerToken, Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _log(db: Session, user_id, action: str, request: Request, details: str = None):
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type="user",
            resource_id=user_id,
            details=details,
            ip_address=_client_ip(request),
        )
    )
    db.commit()


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, request: Request, db: Session = Depends(get_db)):
    email = data.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Is email se account pehle se maujood hai",
        )

    # Admin banane ke liye secret code zaroori hai
    if data.role == UserRole.admin and data.admin_code != settings.ADMIN_SIGNUP_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin code galat hai",
        )

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        hashed_password=hash_password(data.password),
        role=data.role,
        badge_number=data.badge_number,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _log(db, user.id, "SIGNUP", request, f"role={user.role.value}")
    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user or not verify_password(data.password, user.hashed_password):
        _log(db, user.id if user else None, "LOGIN_FAILED", request, data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ya password galat hai",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ye account deactivate hai",
        )

    # Admin login page se investigator (ya ulta) login nahi kar sakta
    if data.role is not None and user.role != data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Ye account {data.role.value} portal ke liye nahi hai",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    _log(db, user.id, "LOGIN", request)

    return Token(access_token=token, user=user)


@router.post("/token", response_model=SwaggerToken, include_in_schema=True)
def token_for_swagger(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Sirf Swagger ke 'Authorize' button ke liye. Username me email likhna hai."""
    user = db.query(User).filter(User.email == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ya password galat hai",
        )
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return SwaggerToken(access_token=token)


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user