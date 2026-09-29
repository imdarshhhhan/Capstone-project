from pydantic import BaseModel, EmailStr
from app.db.models import UserRole

class UserSignupSchema(BaseModel):
    email: EmailStr
    password: str
    fullName: str
    role: UserRole

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
