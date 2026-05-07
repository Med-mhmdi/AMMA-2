from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryOut(BaseModel):
    id: int
    user_id: int
    name: str

    class Config:
        from_attributes = True