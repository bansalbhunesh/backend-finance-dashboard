"""Financial records CRUD, filtering, search, pagination, and role tests."""

from datetime import datetime, timezone

from tests.conftest import _auth


SAMPLE_RECORD = {
    "amount": "150.00",
    "type": "income",
    "category": "salary",
    "occurred_at": "2025-06-15T10:00:00Z",
    "notes": "Monthly salary payment",
}


def _create_record(client, token, **overrides):
    payload = {**SAMPLE_RECORD, **overrides}
    r = client.post("/records", json=payload, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


class TestRecordCRUD:
    def test_create_record(self, client, admin_token):
        data = _create_record(client, admin_token)
        assert data["amount"] == "150.00"
        assert data["type"] == "income"
        assert data["category"] == "salary"

    def test_get_record(self, client, admin_token, analyst_token):
        rec = _create_record(client, admin_token)
        r = client.get(f"/records/{rec['id']}", headers=_auth(analyst_token))
        assert r.status_code == 200
        assert r.json()["id"] == rec["id"]

    def test_update_record(self, client, admin_token):
        rec = _create_record(client, admin_token)
        r = client.patch(f"/records/{rec['id']}", json={"amount": "200.00"}, headers=_auth(admin_token))
        assert r.status_code == 200
        assert r.json()["amount"] == "200.00"

    def test_soft_delete_record(self, client, admin_token, analyst_token):
        rec = _create_record(client, admin_token)
        r = client.delete(f"/records/{rec['id']}", headers=_auth(admin_token))
        assert r.status_code == 204

        # Should not be found anymore
        r = client.get(f"/records/{rec['id']}", headers=_auth(analyst_token))
        assert r.status_code == 404


class TestRecordFiltering:
    def test_filter_by_type(self, client, admin_token, analyst_token):
        _create_record(client, admin_token, type="income")
        _create_record(client, admin_token, type="expense", category="food", amount="30.00")
        r = client.get("/records?type=expense", headers=_auth(analyst_token))
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(i["type"] == "expense" for i in items)

    def test_filter_by_category(self, client, admin_token, analyst_token):
        _create_record(client, admin_token, category="salary")
        _create_record(client, admin_token, category="food", type="expense", amount="20.00")
        r = client.get("/records?category=salary", headers=_auth(analyst_token))
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(i["category"] == "salary" for i in items)

    def test_search(self, client, admin_token, analyst_token):
        _create_record(client, admin_token, notes="Rent payment")
        _create_record(client, admin_token, notes="Coffee", category="food", type="expense", amount="5.00")
        r = client.get("/records?search=rent", headers=_auth(analyst_token))
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert "Rent" in items[0]["notes"]


class TestPagination:
    def test_pagination_metadata(self, client, admin_token, analyst_token):
        for i in range(5):
            _create_record(client, admin_token, amount=f"{10 + i}.00")
        r = client.get("/records?page=1&limit=2", headers=_auth(analyst_token))
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 5
        assert body["page"] == 1
        assert body["pages"] == 3
        assert body["limit"] == 2
        assert len(body["items"]) == 2

    def test_last_page(self, client, admin_token, analyst_token):
        for i in range(5):
            _create_record(client, admin_token, amount=f"{10 + i}.00")
        r = client.get("/records?page=3&limit=2", headers=_auth(analyst_token))
        body = r.json()
        assert len(body["items"]) == 1


class TestRecordRoleRestrictions:
    def test_viewer_cannot_list(self, client, viewer_token):
        r = client.get("/records", headers=_auth(viewer_token))
        assert r.status_code == 403

    def test_viewer_cannot_create(self, client, viewer_token):
        r = client.post("/records", json=SAMPLE_RECORD, headers=_auth(viewer_token))
        assert r.status_code == 403

    def test_analyst_cannot_create(self, client, analyst_token):
        r = client.post("/records", json=SAMPLE_RECORD, headers=_auth(analyst_token))
        assert r.status_code == 403

    def test_analyst_cannot_delete(self, client, admin_token, analyst_token):
        rec = _create_record(client, admin_token)
        r = client.delete(f"/records/{rec['id']}", headers=_auth(analyst_token))
        assert r.status_code == 403


class TestRecordValidation:
    def test_negative_amount(self, client, admin_token):
        r = client.post("/records", json={**SAMPLE_RECORD, "amount": "-10"}, headers=_auth(admin_token))
        assert r.status_code == 422

    def test_missing_category(self, client, admin_token):
        bad = {k: v for k, v in SAMPLE_RECORD.items() if k != "category"}
        r = client.post("/records", json=bad, headers=_auth(admin_token))
        assert r.status_code == 422
