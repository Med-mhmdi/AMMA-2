from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    phone_number: str | None = None
    first_name: str
    family_name: str

    class Config:
        from_attributes = True