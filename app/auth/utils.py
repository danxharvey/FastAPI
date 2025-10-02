from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Depends
from jose import jwt, JWTError
from app.config import config


# Create JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=config["jwt_exp_minutes"])
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, config["jwt_secret"], algorithm=config["jwt_algorithm"])
    return token


# Decode JWT token
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, config["jwt_secret"], algorithms=[config["jwt_algorithm"]])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Extract current user from cookie
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(token)
    username: str = payload.get("sub")
    role: str = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Invalid authentication payload")
    return {"username": username, "role": role}


# Role check dependency
def require_role(required_role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] != required_role:
            raise HTTPException(status_code=403, detail=f"Requires {required_role} role")
        return current_user
    return role_checker
