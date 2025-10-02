# Import libraries
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from app.auth.models import Base, User
from app.auth.schemas import UserCreate, UserOut
from app.auth.models import User
from app.auth.utils import create_access_token, decode_access_token
from app.utils import pwd_context, config
from jose import JWTError


# Dependency to get DB session    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Check current user (dummy implementation, replace with real auth logic)
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_access_token(token, secret=config["jwt_secret"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///app/auth/users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Define router and endpoints
router = APIRouter(
    prefix="/auth/users",
    tags=["User Management"]
)

    
# Create user
@router.post("/", response_model=UserOut, summary="Create user", description="Add a new user to the system.")
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    hashed_pw = pwd_context.hash(user.password)
    db_user = User(username=user.username, password=hashed_pw)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")
    return db_user


# List all users
@router.get("/auth/users/", response_model=List[UserOut], summary="List users", description="List all users in database.")
def read_users(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    return db.query(User).all()


# Get single user
@router.get("/auth/users/{user_id}", response_model=UserOut, summary="Get user", description="Retrieve a single user.")
def read_user(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Update user
@router.patch("/auth/users/{user_id}", response_model=UserOut, summary="Update user", description="Update a user details.")
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.username = user_update.username
    user.password = pwd_context.hash(user_update.password)
    db.commit()
    db.refresh(user)
    return user


# Delete user
@router.delete("/auth/users/{user_id}", summary="Delete user", description="Delete a user from the system.")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Optional: prevent users from deleting themselves
    if current_user == user.username:
        raise HTTPException(status_code=403, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}


# User login
@router.post("auth/login", summary="User login", description="Authenticate user and return JWT token.")
def login(username: str, password: str, request: Request, db: Session = Depends(get_db)):
    # Check for existing JWT cookie
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = decode_access_token(token, secret=config["jwt_secret"])
            current_user = payload.get("sub")
            if current_user:
                raise HTTPException(status_code=400, detail=f"Already logged in as {current_user}")
        except JWTError:
            # Token invalid/expired → ignore, continue login
            pass

    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate JWT token
    token = create_access_token(
        data={"sub": user.username},
        secret=config["jwt_secret"],
        expires_minutes=config["jwt_exp_minutes"]
    )
    
    # Create response and set cookie
    response = JSONResponse(content={"msg": f"Logged in as {user.username}"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,   # prevents JS access
        secure=False,    # True if using HTTPS
        samesite="lax"   # prevents CSRF in simple cases
    )
    return response


# User logout
@router.post("/auth/logout", summary="Logout user", description="Clear JWT cookie to logout")
def logout(current_user: str = Depends(get_current_user)):
    response = JSONResponse(content={"msg": f"User {current_user} logged out"})
    response.delete_cookie(key="access_token")
    return response