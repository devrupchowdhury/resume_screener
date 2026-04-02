"""
tests/test_api.py
Integration tests for the Flask REST API.
Uses an in-memory mock so MongoDB is not required to run these tests.
"""

import unittest
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock


# ── Shared mock DB ────────────────────────────────────────────
def make_mock_db():
    db = {}

    class FakeCollection:
        def __init__(self, name):
            self.name = name
            self._data = {}

        def insert_one(self, doc):
            self._data[doc["_id"]] = doc

        def find_one(self, query, projection=None):
            _id = query.get("_id")
            return self._data.get(_id)

        def find(self, query=None, projection=None):
            if query and "job_id" in query:
                return [v for v in self._data.values() if v.get("job_id") == query["job_id"]]
            return list(self._data.values())

        def create_index(self, *args, **kwargs):
            pass

    class FakeDB:
        def __init__(self):
            self._cols = {}

        def __getitem__(self, name):
            if name not in self._cols:
                self._cols[name] = FakeCollection(name)
            return self._cols[name]

    return FakeDB()


_fake_db = make_mock_db()


class TestHealthEndpoint(unittest.TestCase):

    def setUp(self):
        with patch("database.db.get_db", return_value=_fake_db):
            import app as flask_app
            flask_app.app.config["TESTING"] = True
            self.client = flask_app.app.test_client()

    def test_health_returns_200(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)

    def test_health_returns_ok(self):
        resp = self.client.get("/api/health")
        data = json.loads(resp.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("timestamp", data)


class TestJobEndpoints(unittest.TestCase):

    def setUp(self):
        with patch("database.db.get_db", return_value=_fake_db):
            import app as flask_app
            flask_app.app.config["TESTING"] = True
            self.client = flask_app.app.test_client()
            self.app = flask_app

    def _create_job(self, title="Python Developer", description="Python Flask MongoDB 3 years experience"):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.post(
                "/api/job",
                data=json.dumps({"title": title, "company": "TestCo", "description": description}),
                content_type="application/json",
            )
        return resp

    def test_create_job_201(self):
        resp = self._create_job()
        self.assertEqual(resp.status_code, 201)

    def test_create_job_returns_id(self):
        resp = self._create_job()
        data = json.loads(resp.data)
        self.assertIn("job_id", data)
        self.assertTrue(len(data["job_id"]) > 0)

    def test_create_job_returns_skills(self):
        resp = self._create_job(description="Python Flask MongoDB Docker AWS")
        data = json.loads(resp.data)
        self.assertIn("required_skills", data)
        self.assertIn("python", data["required_skills"])

    def test_create_job_missing_title(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.post(
                "/api/job",
                data=json.dumps({"description": "some job"}),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 400)

    def test_create_job_missing_description(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.post(
                "/api/job",
                data=json.dumps({"title": "Dev"}),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 400)

    def test_get_nonexistent_job_404(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.get("/api/job/nonexistent-id-xyz")
        self.assertEqual(resp.status_code, 404)

    def test_list_jobs_returns_list(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.get("/api/jobs")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)


class TestScreenEndpoint(unittest.TestCase):

    def setUp(self):
        with patch("database.db.get_db", return_value=_fake_db):
            import app as flask_app
            flask_app.app.config["TESTING"] = True
            self.client = flask_app.app.test_client()

    def test_screen_missing_job_id(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.post("/api/screen", data={})
        self.assertEqual(resp.status_code, 400)

    def test_screen_nonexistent_job(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.post("/api/screen", data={"job_id": "fake-job-id"})
        self.assertEqual(resp.status_code, 404)

    def test_get_results_empty(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.get("/api/results/no-such-job")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["total"], 0)

    def test_get_result_404(self):
        with patch("database.db.get_db", return_value=_fake_db):
            resp = self.client.get("/api/result/no-such-result")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
