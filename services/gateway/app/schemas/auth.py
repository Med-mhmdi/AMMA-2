from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    phone_number: str | None = None
    password: str = Field(min_length=6)
    first_name: str = Field(min_length=1, max_length=100)
    family_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)