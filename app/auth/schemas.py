# Import libraries
from pydantic import BaseModel, ConfigDict, Field

from app.auth.enums import UserRole


# Create user schema
class UserCreate(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "johndoe"})
    password: str = Field(..., json_schema_extra={"example": "strongpassword"})
    role: UserRole = Field(..., json_schema_extra={"example": "user"})


# Retrieving user information schema
class UserOut(BaseModel):
    id: int = Field(..., json_schema_extra={"example": 1})
    username: str = Field(..., json_schema_extra={"example": "johndoe"})
    role: UserRole = Field(..., json_schema_extra={"example": "user"})

    class Config:
        model_config = ConfigDict(from_attributes=True)


# Login schema
class LoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "enter username"})
    password: str = Field(..., json_schema_extra={"example": "enter password"})
