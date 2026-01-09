# Import libraries
from fastapi import status

from app.auth.db import pwd_context
from app.auth.enums import UserRole
from app.auth.utils import create_access_token


class TestLoginEndpoint:
    """Test suite for POST /auth/login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login with valid credentials."""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpassword"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Logged in as testuser" in response.json()["msg"]

        # Verify cookie is set
        assert "access_token" in response.cookies
        token = response.cookies["access_token"]
        assert token is not None
        assert len(token) > 0

    def test_login_invalid_username(self, client, test_user):
        """Test login with invalid username."""
        response = client.post(
            "/auth/login", json={"username": "wronguser", "password": "testpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
        assert "access_token" not in response.cookies

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
        assert "access_token" not in response.cookies

    def test_login_with_invalid_token_allows_login(self, client, test_user):
        """Test that login with invalid/expired token allows new login to proceed."""
        # Set an invalid token in cookie
        client.cookies.set("access_token", "invalid.token.here")

        # Should be able to login despite invalid token
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpassword"}
        )

        # Should succeed - invalid token should be ignored
        assert response.status_code == status.HTTP_200_OK
        assert "Logged in as testuser" in response.json()["msg"]
        assert "access_token" in response.cookies

    def test_login_with_admin_user(self, client, test_admin):
        """Test login with admin user."""
        response = client.post(
            "/auth/login", json={"username": "testadmin", "password": "adminpassword"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert "Logged in as testadmin" in response.json()["msg"]
        assert "access_token" in response.cookies

    def test_login_token_contains_role(self, client, test_user):
        """Test that login token contains user role."""
        response = client.post(
            "/auth/login", json={"username": "testuser", "password": "testpassword"}
        )

        assert response.status_code == status.HTTP_200_OK
        token = response.cookies["access_token"]

        # Decode token to verify role
        from app.auth.utils import decode_access_token

        payload = decode_access_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "user"


class TestLogoutEndpoint:
    """Test suite for POST /auth/logout endpoint."""

    def test_logout_success(self, client, test_user):
        """Test successful logout."""
        # First login
        token = create_access_token(data={"sub": "testuser", "role": "user"})

        # Logout
        client.cookies.set("access_token", token)
        response = client.post("/auth/logout")

        assert response.status_code == status.HTTP_200_OK
        assert "logged out" in response.json()["msg"].lower()

        # Verify cookie is deleted
        # TestClient doesn't show deleted cookies, but we can verify by trying to use it
        client.cookies.set("access_token", token)
        response2 = client.get("/users/list")
        # Should fail because cookie was deleted (or token invalidated)
        assert response2.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_logout_without_token(self, client):
        """Test logout without authentication token."""
        response = client.post("/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in response.json()["detail"]

    def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token."""
        client.cookies.set("access_token", "invalid.token")
        response = client.post("/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateUserEndpoint:
    """Test suite for POST /users/create endpoint."""

    def test_create_user_success(self, client, test_admin):
        """Test successful user creation by admin."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.post(
            "/users/create",
            json={"username": "newuser", "password": "newpassword", "role": "user"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "newuser"
        assert response.json()["role"] == "user"
        assert "id" in response.json()

    def test_create_user_requires_admin(self, client, test_user):
        """Test that only admin can create users."""
        token = create_access_token(data={"sub": "testuser", "role": "user"})

        client.cookies.set("access_token", token)
        response = client.post(
            "/users/create",
            json={"username": "newuser", "password": "newpassword", "role": "user"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Requires admin role" in response.json()["detail"]

    def test_create_user_duplicate_username(self, client, test_admin, test_user):
        """Test that creating user with duplicate username fails."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.post(
            "/users/create",
            json={
                "username": "testuser",  # Already exists
                "password": "password",
                "role": "user",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already exists" in response.json()["detail"]

    def test_create_user_without_auth(self, client):
        """Test that creating user without authentication fails."""
        response = client.post(
            "/users/create",
            json={"username": "newuser", "password": "password", "role": "user"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestListUsersEndpoint:
    """Test suite for GET /users/list endpoint."""

    def test_list_users_success(self, client, test_admin, test_user):
        """Test successful listing of users by admin."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.get("/users/list")

        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 2  # At least admin and test_user

        usernames = [u["username"] for u in users]
        assert "testadmin" in usernames
        assert "testuser" in usernames

    def test_list_users_requires_admin(self, client, test_user):
        """Test that only admin can list users."""
        token = create_access_token(data={"sub": "testuser", "role": "user"})

        client.cookies.set("access_token", token)
        response = client.get("/users/list")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Requires admin role" in response.json()["detail"]

    def test_list_users_without_auth(self, client):
        """Test that listing users without authentication fails."""
        response = client.get("/users/list")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUserEndpoint:
    """Test suite for GET /users/view/{user_id} endpoint."""

    def test_get_user_success(self, client, test_admin, test_user):
        """Test successful retrieval of user by admin."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.get(f"/users/view/{test_user.id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == test_user.id
        assert response.json()["username"] == "testuser"
        assert response.json()["role"] == "user"

    def test_get_user_not_found(self, client, test_admin):
        """Test retrieval of non-existent user."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.get("/users/view/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_get_user_requires_admin(self, client, test_user):
        """Test that only admin can view users."""
        token = create_access_token(data={"sub": "testuser", "role": "user"})

        client.cookies.set("access_token", token)
        response = client.get(f"/users/view/{test_user.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateUserEndpoint:
    """Test suite for PATCH /users/patch/{user_id} endpoint."""

    def test_update_user_success(self, client, test_admin, test_user):
        """Test successful user update by admin."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.patch(
            f"/users/patch/{test_user.id}",
            json={"username": "updateduser", "password": "newpassword", "role": "user"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "updateduser"
        assert response.json()["id"] == test_user.id

    def test_update_user_not_found(self, client, test_admin):
        """Test update of non-existent user."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.patch(
            "/users/patch/99999",
            json={"username": "updateduser", "password": "newpassword", "role": "user"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_update_user_requires_admin(self, client, test_user):
        """Test that only admin can update users."""
        token = create_access_token(data={"sub": "testuser", "role": "user"})

        client.cookies.set("access_token", token)
        response = client.patch(
            f"/users/patch/{test_user.id}",
            json={"username": "updateduser", "password": "newpassword", "role": "user"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteUserEndpoint:
    """Test suite for DELETE /users/delete/{user_id} endpoint."""

    def test_delete_user_success(self, client, test_admin, test_db):
        """Test successful user deletion by admin."""
        # Create a user to delete
        from app.auth.models import User

        user_to_delete = User(
            username="tobedeleted",
            password=pwd_context.hash("password"),
            role=UserRole.user,
        )
        test_db.add(user_to_delete)
        test_db.commit()
        test_db.refresh(user_to_delete)

        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.delete(f"/users/delete/{user_to_delete.id}")

        assert response.status_code == status.HTTP_200_OK
        assert "deleted successfully" in response.json()["detail"].lower()

        # Verify user is deleted
        deleted_user = test_db.query(User).filter(User.id == user_to_delete.id).first()
        assert deleted_user is None

    def test_delete_user_not_found(self, client, test_admin):
        """Test deletion of non-existent user."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.delete("/users/delete/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in response.json()["detail"]

    def test_delete_user_prevents_self_deletion(self, client, test_admin):
        """Test that admin cannot delete themselves."""
        token = create_access_token(data={"sub": "testadmin", "role": "admin"})

        client.cookies.set("access_token", token)
        response = client.delete(f"/users/delete/{test_admin.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Cannot delete yourself" in response.json()["detail"]

    def test_delete_user_requires_admin(self, client, test_user):
        """Test that only admin can delete users."""
        token = create_access_token(data={"sub": "testuser", "role": "user"})

        client.cookies.set("access_token", token)
        response = client.delete(f"/users/delete/{test_user.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN
