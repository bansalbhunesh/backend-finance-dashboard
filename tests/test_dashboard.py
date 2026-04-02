"""Dashboard summary and full endpoint tests."""

from tests.conftest import _auth


def _seed_records(client, token):
    """Create a few records for dashboard aggregation tests."""
    records = [
        {"amount": "1000.00", "type": "income", "category": "salary", "occurred_at": "2025-06-01T10:00:00Z"},
        {"amount": "500.00", "type": "income", "category": "freelance", "occurred_at": "2025-06-15T10:00:00Z"},
        {"amount": "200.00", "type": "expense", "category": "food", "occurred_at": "2025-06-10T10:00:00Z"},
        {"amount": "300.00", "type": "expense", "category": "utilities", "occurred_at": "2025-07-01T10:00:00Z"},
    ]
    ids = []
    for rec in records:
        r = client.post("/records", json=rec, headers=_auth(token))
        assert r.status_code == 201
        ids.append(r.json()["id"])
    return ids


class TestDashboardSummary:
    def test_summary_totals(self, client, admin_token, viewer_token):
        _seed_records(client, admin_token)
        r = client.get("/dashboard/summary", headers=_auth(viewer_token))
        assert r.status_code == 200
        data = r.json()
        assert float(data["total_income"]) == 1500.00
        assert float(data["total_expenses"]) == 500.00
        assert float(data["net_balance"]) == 1000.00
        assert data["record_count"] == 4

    def test_empty_summary(self, client, viewer_token):
        r = client.get("/dashboard/summary", headers=_auth(viewer_token))
        assert r.status_code == 200
        data = r.json()
        assert float(data["total_income"]) == 0
        assert float(data["net_balance"]) == 0
        assert data["record_count"] == 0


class TestDashboardFull:
    def test_full_dashboard(self, client, admin_token, analyst_token):
        _seed_records(client, admin_token)
        r = client.get("/dashboard/full", headers=_auth(analyst_token))
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "category_totals" in data
        assert "recent_activity" in data
        assert "monthly_trends" in data
        assert len(data["category_totals"]) > 0
        assert len(data["recent_activity"]) > 0

    def test_trends_weekly(self, client, admin_token, viewer_token):
        _seed_records(client, admin_token)
        r = client.get("/dashboard/full?trend_granularity=week", headers=_auth(viewer_token))
        assert r.status_code == 200
        assert len(r.json()["monthly_trends"]) > 0


class TestDashboardSoftDelete:
    def test_deleted_records_excluded(self, client, admin_token, viewer_token):
        ids = _seed_records(client, admin_token)
        # Delete the first income record (1000.00)
        client.delete(f"/records/{ids[0]}", headers=_auth(admin_token))

        r = client.get("/dashboard/summary", headers=_auth(viewer_token))
        data = r.json()
        assert float(data["total_income"]) == 500.00
        assert data["record_count"] == 3


class TestDashboardRoles:
    def test_viewer_can_access(self, client, viewer_token):
        r = client.get("/dashboard/summary", headers=_auth(viewer_token))
        assert r.status_code == 200

    def test_unauthenticated(self, client):
        r = client.get("/dashboard/summary")
        assert r.status_code in (401, 403)
