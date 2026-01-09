# Import libraries
from enum import Enum

# Define user roles
class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    