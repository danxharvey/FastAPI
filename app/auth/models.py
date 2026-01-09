# Import libraries
from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import declarative_base
from app.auth.enums import UserRole

# Define the SQLAlchemy User model
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole), default=UserRole.user, nullable=False)