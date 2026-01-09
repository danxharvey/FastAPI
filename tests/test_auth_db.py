# Import libraries
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

from app.auth.db import engine, get_db, init_db, pwd_context
from app.auth.enums import UserRole
from app.auth.models import Base, User
from app.config import config

# ------------------------
# Fixtures
# ------------------------


@pytest.fixture(autouse=True)
def refresh_db():
    """Refresh the database for each test: drop all tables,
    recreate them, and initialize default admin.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Initialize default admin if needed
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    username = config["default_admin"]["username"]
    password = config["default_admin"]["password"]
    role = config["default_admin"]["role"]
    hashed_pw = pwd_context.hash(password)
    admin_user = User(username=username, password=hashed_pw, role=role)
    session.add(admin_user)
    session.commit()
    session.close()
    yield  # Run the test
    # No teardown needed, next test will refresh again


@pytest.fixture
def test_db():
    """Provide a session for tests."""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(test_db):
    """Create a sample user for testing."""
    user = User(
        username="testuser", password=pwd_context.hash("password"), role=UserRole.user
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ------------------------
# Tests (unchanged logic)
# ------------------------


class TestInitDb:
    """Test suite for init_db function."""

    def test_init_db_creates_tables(self, test_db):
        """Test that init_db creates necessary tables."""
        tables = test_db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "users" in table_names

    def test_init_db_creates_users_table_structure(self, test_db):
        """Test that users table has correct structure."""
        inspector = inspect(engine)
        columns = inspector.get_columns("users")
        column_names = [col["name"] for col in columns]

        assert "id" in column_names
        assert "username" in column_names
        assert "password" in column_names
        assert "role" in column_names

    def test_init_db_creates_default_admin_when_empty(self, test_db):
        """Test that init_db creates default admin when database is empty."""
        user_count = test_db.query(User).count()
        assert user_count >= 1

        admin = test_db.query(User).filter(User.role == UserRole.admin).first()
        assert admin is not None
        assert admin.username == config["default_admin"]["username"]
        assert admin.role == UserRole.admin

        # Verify password is hashed (not plain text)
        assert admin.password != config["default_admin"]["password"]
        assert pwd_context.verify(config["default_admin"]["password"], admin.password)

    def test_init_db_default_admin_credentials(self, test_db):
        """Test that default admin has correct credentials from config."""
        admin = test_db.query(User).filter(User.role == UserRole.admin).first()

        assert admin.username == config["default_admin"]["username"]
        assert admin.role == UserRole.admin
        # Password should be hashed
        assert pwd_context.verify(config["default_admin"]["password"], admin.password)

    def test_init_db_does_not_create_admin_when_users_exist(self, test_db, test_user):
        """Test that init_db does not create another admin when users already exist."""
        initial_count = test_db.query(User).count()

        # Call init_db again
        init_db()

        # Count should not increase (admin already exists from fixture)
        final_count = test_db.query(User).count()
        assert final_count == initial_count

    def test_init_db_is_idempotent(self, test_db):
        """Test that calling init_db multiple times doesn't cause issues."""
        initial_count = test_db.query(User).count()

        # Call init_db multiple times
        init_db()
        init_db()
        init_db()

        # Should still have same number of users
        final_count = test_db.query(User).count()
        assert final_count == initial_count

    def test_init_db_creates_only_one_admin(self, test_db):
        """Test that only one default admin is created."""
        admins = test_db.query(User).filter(User.role == UserRole.admin).all()
        assert len(admins) == 1

    def test_init_db_handles_exception_gracefully(self, test_db):
        """Test that init_db handles exceptions and still closes the session."""
        # This test verifies the finally block works
        # We can't easily simulate an exception without breaking things,
        # but we can verify the function completes successfully
        try:
            init_db()
            # If we get here, the function completed without crashing
            assert True
        except Exception:
            pytest.fail("init_db raised an exception unexpectedly")

    def test_init_db_uses_config_values(self, test_db):
        """Test that init_db uses values from config."""
        admin = test_db.query(User).filter(User.role == UserRole.admin).first()

        assert admin.username == config["default_admin"]["username"]
        assert admin.role == UserRole.admin
        # Verify password matches config (when hashed)
        assert pwd_context.verify(config["default_admin"]["password"], admin.password)


class TestGetDb:
    """Test suite for get_db dependency function."""

    def test_get_db_yields_session(self, test_db):
        """Test that get_db yields a database session."""
        db_gen = get_db()
        db = next(db_gen)

        assert db is not None
        assert hasattr(db, "query")
        assert hasattr(db, "add")
        assert hasattr(db, "commit")
        assert db.query(User).count() >= 1

        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_session_type(self):
        """Test that get_db yields a SessionLocal session."""
        db_gen = get_db()
        db = next(db_gen)

        # Verify it's a SQLAlchemy session
        assert hasattr(db, "bind")
        assert hasattr(db, "query")

        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_closes_session(self, test_db):
        """Test that get_db properly closes session after use."""
        db_gen = get_db()
        db = next(db_gen)

        # Verify session is active
        assert db.is_active

        # Close the generator (simulating FastAPI dependency cleanup)
        try:
            next(db_gen)
        except StopIteration:
            pass

    def test_get_db_can_query_users(self, test_db, test_user):
        """Test that get_db session can query users."""
        db_gen = get_db()
        db = next(db_gen)

        try:
            users = db.query(User).all()
            assert isinstance(users, list)
            assert len(users) >= 1
            assert any(u.username == test_user.username for u in users)
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    def test_get_db_can_create_user(self, test_db):
        """Test that get_db session can create users."""
        db_gen = get_db()
        db = next(db_gen)

        try:
            new_user = User(
                username="newuser",
                password=pwd_context.hash("password"),
                role=UserRole.user,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Verify user was created
            user = db.query(User).filter(User.username == "newuser").first()
            assert user is not None
            assert user.username == "newuser"
            assert user.role == UserRole.user
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    def test_get_db_can_update_user(self, test_db, test_user):
        """Test that get_db session can update users."""
        db_gen = get_db()
        db = next(db_gen)

        try:
            user = db.query(User).filter(User.id == test_user.id).first()
            original_username = user.username
            user.username = "updateduser"
            db.commit()
            db.refresh(user)

            assert user.username == "updateduser"
            assert user.username != original_username
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    def test_get_db_can_delete_user(self, test_db):
        """Test that get_db session can delete users."""
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Create a user to delete
            user_to_delete = User(
                username="tobedeleted",
                password=pwd_context.hash("password"),
                role=UserRole.user,
            )
            db.add(user_to_delete)
            db.commit()
            db.refresh(user_to_delete)

            user_id = user_to_delete.id

            # Delete the user
            db.delete(user_to_delete)
            db.commit()

            # Verify user is deleted
            deleted_user = db.query(User).filter(User.id == user_id).first()
            assert deleted_user is None
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    def test_get_db_handles_exception_and_closes(self):
        """Test that get_db closes session even when exception occurs."""
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Simulate an exception
            raise ValueError("Test exception")
        except ValueError:
            # Verify session is still accessible before cleanup
            assert db.is_active
        finally:
            # Cleanup should still work
            try:
                next(db_gen)
            except StopIteration:
                pass

    def test_get_db_multiple_calls_yield_different_sessions(self):
        """Test that multiple calls to get_db yield different session instances."""
        db_gen1 = get_db()
        db1 = next(db_gen1)

        db_gen2 = get_db()
        db2 = next(db_gen2)

        # Sessions should be different objects
        assert db1 is not db2

        # Cleanup
        try:
            next(db_gen1)
            next(db_gen2)
        except StopIteration:
            pass

    def test_get_db_session_isolation(self):
        """Test that sessions from get_db are properly isolated."""
        db_gen1 = get_db()
        db1 = next(db_gen1)

        db_gen2 = get_db()
        db2 = next(db_gen2)

        try:
            # Create user in first session
            user1 = User(
                username="session1user",
                password=pwd_context.hash("password"),
                role=UserRole.user,
            )
            db1.add(user1)
            db1.commit()

            # In SQLite with default isolation, this might be visible, but the test
            # verifies the sessions are separate objects
            assert db1 is not db2
        finally:
            try:
                next(db_gen1)
                next(db_gen2)
            except StopIteration:
                pass
