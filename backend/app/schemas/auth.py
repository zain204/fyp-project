from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole
from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    # Login page batata hai (admin ya investigator). Role match na hua to access nahi milega.
    role: Optional[UserRole] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SwaggerToken(BaseModel):
    access_token: str
    token_type: str = "bearer"