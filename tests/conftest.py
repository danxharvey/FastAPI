# Import libraries
import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Request
from unittest.mock import Mock

# Import app components
from app.auth.models import Base, User
from app.auth.db import get_db, pwd_context
from app.auth.enums import UserRole
from app.main import app
from app.config import config


# Create test database in memory
@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    # Use test DB URL from config
    test_db_url = config.get("test_db_url", "sqlite:///:memory:")
    
    # If using file-based DB, ensure directory exists
    if test_db_url.startswith("sqlite:///"):
        db_path = test_db_url.replace("sqlite:///", "")
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            # Remove existing test DB if it exists
            if os.path.exists(db_path):
                os.remove(db_path)
    
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        # Clean up test DB file if it exists
        if test_db_url.startswith("sqlite:///") and test_db_url != "sqlite:///:memory:":
            db_path = test_db_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                os.remove(db_path)


# Override get_db dependency for testing
@pytest.fixture(scope="function")
def override_get_db(test_db):
    """Override the get_db dependency with test database."""
    def _get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close, test_db fixture handles it
    
    app.dependency_overrides[get_db] = _get_db
    yield test_db
    app.dependency_overrides.clear()


# Test client fixture
@pytest.fixture(scope="function")
def client(override_get_db):
    """Create a test client with test database."""
    return TestClient(app)


# Create test user fixture
@pytest.fixture
def test_user(test_db):
    """Create a test user in the database."""
    user = User(
        username="testuser",
        password=pwd_context.hash("testpassword"),
        role=UserRole.user
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# Create test admin user fixture
@pytest.fixture
def test_admin(test_db):
    """Create a test admin user in the database."""
    admin = User(
        username="testadmin",
        password=pwd_context.hash("adminpassword"),
        role=UserRole.admin
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin


# Mock request fixture for testing auth functions
@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = Mock(spec=Request)
    request.cookies = {}
    return request


# Helper function to create auth token
def create_test_token(username: str, role: str = "user"):
    """Helper to create a test JWT token."""
    from app.auth.utils import create_access_token
    return create_access_token(data={"sub": username, "role": role})
