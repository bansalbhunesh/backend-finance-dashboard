"""User CRUD and role restriction tests."""

from tests.conftest import _auth, _create_user

from app.models import Role


class TestListUsers:
    def test_admin_can_list(self, client, admin_token):
        r = client.get("/users", headers=_auth(admin_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_viewer_cannot_list(self, client, viewer_token):
        r = client.get("/users", headers=_auth(viewer_token))
        assert r.status_code == 403

    def test_analyst_cannot_list(self, client, analyst_token):
        r = client.get("/users", headers=_auth(analyst_token))
        assert r.status_code == 403


class TestCreateUser:
    def test_admin_creates_user(self, client, admin_token):
        payload = {
            "email": "new@test.com",
            "password": "NewPass12345!",
            "full_name": "New User",
            "role": "analyst",
        }
        r = client.post("/users", json=payload, headers=_auth(admin_token))
        assert r.status_code == 201
        assert r.json()["email"] == "new@test.com"
        assert r.json()["role"] == "analyst"

    def test_duplicate_email(self, client, admin_token, db):
        _create_user(db, "dup@test.com", "Pass12345!", Role.viewer)
        payload = {"email": "dup@test.com", "password": "Pass12345!", "full_name": "Dup"}
        r = client.post("/users", json=payload, headers=_auth(admin_token))
        assert r.status_code == 409

    def test_viewer_cannot_create(self, client, viewer_token):
        payload = {"email": "x@test.com", "password": "Pass12345!", "full_name": "X"}
        r = client.post("/users", json=payload, headers=_auth(viewer_token))
        assert r.status_code == 403


class TestUpdateUser:
    def test_admin_updates_user(self, client, admin_token, db):
        user = _create_user(db, "upd@test.com", "Pass12345!", Role.viewer)
        r = client.patch(f"/users/{user.id}", json={"full_name": "Updated"}, headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json()["full_name"] == "Updated"

    def test_empty_update(self, client, admin_token, db):
        user = _create_user(db, "empty@test.com", "Pass12345!", Role.viewer)
        r = client.patch(f"/users/{user.id}", json={}, headers=_auth(admin_token))
        assert r.status_code == 400


class TestDeleteUser:
    def test_soft_delete(self, client, admin_token, db):
        user = _create_user(db, "del@test.com", "Pass12345!", Role.viewer)
        r = client.delete(f"/users/{user.id}", headers=_auth(admin_token))
        assert r.status_code == 204

        # Should no longer appear in list
        r = client.get("/users", headers=_auth(admin_token))
        emails = [u["email"] for u in r.json()]
        assert "del@test.com" not in emails

    def test_cannot_delete_self(self, client, admin_token, admin_user):
        r = client.delete(f"/users/{admin_user.id}", headers=_auth(admin_token))
        assert r.status_code == 400

    def test_delete_nonexistent(self, client, admin_token):
        r = client.delete("/users/99999", headers=_auth(admin_token))
        assert r.status_code == 404
