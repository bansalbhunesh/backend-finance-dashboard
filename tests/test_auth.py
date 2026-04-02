"""Auth endpoint tests."""

from tests.conftest import _auth, _create_user, _get_token

from app.models import Role


class TestLogin:
    def test_login_success(self, client, admin_user):
        r = client.post("/auth/login", json={"email": "admin@test.com", "password": "Admin12345!"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, admin_user):
        r = client.post("/auth/login", json={"email": "admin@test.com", "password": "Wrong12345!"})
        assert r.status_code == 401
        assert "Incorrect" in r.json()["detail"]

    def test_login_nonexistent_user(self, client):
        r = client.post("/auth/login", json={"email": "nobody@test.com", "password": "Pass12345!"})
        assert r.status_code == 401

    def test_login_inactive_user(self, client, db):
        _create_user(db, "inactive@test.com", "Pass12345!", Role.admin, active=False)
        r = client.post("/auth/login", json={"email": "inactive@test.com", "password": "Pass12345!"})
        assert r.status_code == 403
        assert "inactive" in r.json()["detail"].lower()

    def test_login_missing_fields(self, client):
        r = client.post("/auth/login", json={"email": "admin@test.com"})
        assert r.status_code == 422


class TestProtectedAccess:
    def test_no_token(self, client):
        r = client.get("/users/me")
        assert r.status_code in (401, 403)

    def test_invalid_token(self, client):
        r = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401

    def test_me_with_valid_token(self, client, admin_token):
        r = client.get("/users/me", headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json()["email"] == "admin@test.com"
