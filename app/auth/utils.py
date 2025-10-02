# Import libraries
from datetime import datetime, timedelta, timezone
from jose import jwt

# Utility functions for authentication
def create_access_token(data: dict, secret: str, expires_minutes: int, algorithm: str = "HS256"):
    to_encode = data.copy()
    expire = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret, algorithm=algorithm)


# Decode JWT token
def decode_access_token(token: str, secret: str , algorithms: list = ["HS256"]):
    return jwt.decode(token, secret, algorithms=algorithms)
