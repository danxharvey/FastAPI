from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel
from enum import Enum


# Set schemas for API
class Gender(str, Enum):
    male = 'Male'
    female = 'Female'
    other = 'Other'


class Role(str, Enum):
    admin = 'Administrator'
    user = 'User'
    power = 'Power User'


class User(BaseModel):
    id: Optional[UUID] = uuid4()
    first_name: str
    last_name: str
    gender: Gender
    roles: List[Role]


class UpdateUser(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    gender: Optional[Gender]
    roles: Optional[List[Role]]