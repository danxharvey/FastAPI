# Import libraries
from pydantic import BaseModel, Field
from app.auth.enums import UserRole

# Create user schema
class UserCreate(BaseModel):
    username: str = Field(..., example="johndoe")
    password: str = Field(..., example="strongpassword")
    role: UserRole = Field(..., example="user")

# Retrieving user information schema
class UserOut(BaseModel):
    id: int = Field(..., example=1)
    username: str = Field(..., example="johndoe")
    role: UserRole = Field(..., example="user")

    class Config:
        orm_mode = True