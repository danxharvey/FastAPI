# Import libraries
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from app.auth.models import Base, User
from app.config import config


# Configure database
SQLALCHEMY_DATABASE_URL = config["db_url"]
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Initialize database
def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create default user if DB empty
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        if user_count == 0:
            # Directly read from YAML
            username = config["default_admin"]["username"]
            password = config["default_admin"]["password"]
            role = config["default_admin"]["role"]
            
            hashed_pw = pwd_context.hash(password)
            admin_user = User(username=username, password=hashed_pw, role=role)
            db.add(admin_user)
            db.commit()
            print(f"Default user created: username={username}, role={role}")
    finally:
        db.close()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
