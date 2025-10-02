# Import libraries
from pydantic import BaseModel, Field

# Pydantic schemas for user creation and output
class UserCreate(BaseModel):
    username: str = Field(..., example="johndoe")
    password: str = Field(..., example="strongpassword")


class UserOut(BaseModel):
    id: int = Field(..., example=1)
    username: str = Field(..., example="johndoe")

    class Config:
        orm_mode = True