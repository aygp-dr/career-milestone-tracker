"""Tests for CareerMilestoneTracker."""

import json


class TestIndex:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_contains_title(self, client):
        resp = client.get("/")
        assert b"Career Milestone Tracker" in resp.data

    def test_index_shows_add_form(self, client):
        resp = client.get("/")
        assert b"Add Milestone" in resp.data

    def test_index_empty_message(self, client):
        resp = client.get("/")
        assert b"No milestones yet" in resp.data

    def test_index_shows_milestones(self, client, seed_milestones):
        resp = client.get("/")
        assert b"Senior Engineer" in resp.data
        assert b"AWS Solutions Architect" in resp.data

    def test_filter_by_category(self, client, seed_milestones):
        resp = client.get("/?category=promotion")
        assert b"Senior Engineer" in resp.data
        assert b"PyCon Talk" not in resp.data

    def test_filter_invalid_category(self, client, seed_milestones):
        resp = client.get("/?category=invalid")
        assert resp.status_code == 200
        # Should show all milestones when filter is invalid
        assert b"Senior Engineer" in resp.data

    def test_progress_summary_counts(self, client, seed_milestones):
        resp = client.get("/")
        # Total count should be 5
        assert b">5<" in resp.data


class TestAddMilestone:
    def test_add_milestone(self, client):
        resp = client.post("/add", data={
            "title": "Got Promoted",
            "date": "2024-05-01",
            "category": "promotion",
            "description": "To staff engineer",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Got Promoted" in resp.data

    def test_add_milestone_redirects(self, client):
        resp = client.post("/add", data={
            "title": "New Cert",
            "date": "2024-06-01",
            "category": "certification",
            "description": "",
        })
        assert resp.status_code == 302

    def test_add_milestone_missing_title(self, client):
        resp = client.post("/add", data={
            "title": "",
            "date": "2024-05-01",
            "category": "promotion",
        }, follow_redirects=True)
        # Should redirect without adding
        assert resp.status_code == 200

    def test_add_milestone_invalid_category(self, client):
        resp = client.post("/add", data={
            "title": "Bad Category",
            "date": "2024-05-01",
            "category": "invalid",
        }, follow_redirects=True)
        assert b"Bad Category" not in resp.data


class TestEditMilestone:
    def test_edit_form_appears(self, client, seed_milestones):
        resp = client.get("/?edit=1")
        assert b"Edit Milestone" in resp.data
        assert b"Save Changes" in resp.data

    def test_edit_milestone(self, client, seed_milestones):
        resp = client.post("/edit/1", data={
            "title": "Staff Engineer",
            "date": "2024-02-01",
            "category": "promotion",
            "description": "Updated title",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Staff Engineer" in resp.data

    def test_edit_redirects(self, client, seed_milestones):
        resp = client.post("/edit/1", data={
            "title": "Staff Engineer",
            "date": "2024-02-01",
            "category": "promotion",
            "description": "",
        })
        assert resp.status_code == 302

    def test_edit_invalid_category_rejected(self, client, seed_milestones):
        resp = client.post("/edit/1", data={
            "title": "Bad",
            "date": "2024-02-01",
            "category": "invalid",
            "description": "",
        }, follow_redirects=True)
        # Original title should remain
        assert b"Senior Engineer" in resp.data


class TestDeleteMilestone:
    def test_delete_milestone(self, client, seed_milestones):
        resp = client.post("/delete/1", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Senior Engineer" not in resp.data

    def test_delete_redirects(self, client, seed_milestones):
        resp = client.post("/delete/1")
        assert resp.status_code == 302

    def test_delete_nonexistent(self, client):
        resp = client.post("/delete/999", follow_redirects=True)
        assert resp.status_code == 200


class TestAPIMilestones:
    def test_api_milestones_empty(self, client):
        resp = client.get("/api/milestones")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data == []

    def test_api_milestones_returns_all(self, client, seed_milestones):
        resp = client.get("/api/milestones")
        data = json.loads(resp.data)
        assert len(data) == 5

    def test_api_milestones_filter(self, client, seed_milestones):
        resp = client.get("/api/milestones?category=promotion")
        data = json.loads(resp.data)
        assert len(data) == 1
        assert data[0]["title"] == "Senior Engineer"

    def test_api_milestones_filter_invalid(self, client, seed_milestones):
        resp = client.get("/api/milestones?category=bogus")
        data = json.loads(resp.data)
        assert len(data) == 5

    def test_api_milestone_by_id(self, client, seed_milestones):
        resp = client.get("/api/milestones/1")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "Senior Engineer"
        assert data["category"] == "promotion"

    def test_api_milestone_not_found(self, client):
        resp = client.get("/api/milestones/999")
        assert resp.status_code == 404

    def test_api_milestones_ordered_by_date_desc(self, client, seed_milestones):
        resp = client.get("/api/milestones")
        data = json.loads(resp.data)
        dates = [m["date"] for m in data]
        assert dates == sorted(dates, reverse=True)


class TestAPISummary:
    def test_api_summary_empty(self, client):
        resp = client.get("/api/summary")
        data = json.loads(resp.data)
        assert data["total"] == 0
        assert all(v == 0 for v in data["by_category"].values())
        assert data["by_year"] == {}

    def test_api_summary_with_data(self, client, seed_milestones):
        resp = client.get("/api/summary")
        data = json.loads(resp.data)
        assert data["total"] == 5
        assert data["by_category"]["promotion"] == 1
        assert data["by_category"]["certification"] == 1
        assert data["by_category"]["project"] == 1
        assert data["by_category"]["award"] == 1
        assert data["by_category"]["talk"] == 1
        assert data["by_year"]["2024"] == 3
        assert data["by_year"]["2023"] == 2
