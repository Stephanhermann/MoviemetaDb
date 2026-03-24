"""Web API tests for MoviemetaDb."""

import os
import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from moviemetadb import web
except Exception:  # pragma: no cover
    TestClient = None
    web = None


@unittest.skipIf(TestClient is None or web is None, "fastapi test dependencies not available")
class WebApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "web-test.db"
        os.environ["MOVIEMETADB_DATABASE_URL"] = str(self.db_path)
        os.environ.pop("MOVIEMETADB_API_KEY", None)
        web.store = None
        self.client = TestClient(web.app)

    def tearDown(self) -> None:
        self.client.close()
        self.tmpdir.cleanup()
        os.environ.pop("MOVIEMETADB_DATABASE_URL", None)
        os.environ.pop("MOVIEMETADB_API_KEY", None)
        web.store = None

    def test_movie_crud_and_search(self):
        payload = {
            "title": "Arrival",
            "year": 2016,
            "rating": 8.0,
            "plot": "Language and first contact.",
            "language": "en",
        }

        r = self.client.post("/movie", json=payload)
        self.assertEqual(r.status_code, 201)

        r = self.client.get("/movies")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Arrival")

        r = self.client.get("/movies/search", params={"q": "arr"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

        r = self.client.delete("/movie", params={"title": "Arrival", "year": 2016})
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/movies")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 0)

    def test_movie_filters_sort_and_limit(self):
        self.client.post("/movies", json={"title": "C", "year": 2001, "rating": 6.0})
        self.client.post("/movies", json={"title": "A", "year": 2005, "rating": 8.0})
        self.client.post("/movies", json={"title": "B", "year": 2010, "rating": 9.0})

        r = self.client.get("/movies", params={"min_year": 2003, "min_rating": 7.0, "sort": "year"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual([m["title"] for m in data], ["A", "B"])

        # invalid sort should not crash, and should fallback to default order
        r = self.client.get("/movies", params={"sort": "not-a-field", "limit": 2})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)

    def test_movie_validation_error(self):
        # missing required field "year"
        r = self.client.post("/movies", json={"title": "Invalid"})
        self.assertEqual(r.status_code, 422)

    def test_photo_crud_and_search(self):
        payload = {
            "file_path": "/pics/trip/sunset.jpg",
            "album": "Trip",
            "description": "Sunset",
            "tags": "sunset,sea",
        }

        r = self.client.post("/photos", json=payload)
        self.assertEqual(r.status_code, 201)

        r = self.client.get("/photos")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["file_path"], "/pics/trip/sunset.jpg")

        r = self.client.get("/photos/search", params={"q": "sunset"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

        r = self.client.delete("/photos", params={"file_path": "/pics/trip/sunset.jpg"})
        self.assertEqual(r.status_code, 200)

        r = self.client.get("/photos")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 0)

    def test_photo_filters_sort_and_limit(self):
        self.client.post("/photos", json={"file_path": "/pics/a.jpg", "album": "Trip", "taken_at": "2024-01-01"})
        self.client.post("/photos", json={"file_path": "/pics/b.jpg", "album": "Family", "taken_at": "2024-03-01"})
        self.client.post("/photos", json={"file_path": "/pics/c.jpg", "album": "Trip", "taken_at": "2024-02-01"})

        r = self.client.get("/photos", params={"album": "Trip", "sort": "taken_at"})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual([p["file_path"] for p in data], ["/pics/a.jpg", "/pics/c.jpg"])

        r = self.client.get("/photos", params={"sort": "not-a-field", "limit": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_api_key_auth(self):
        self.client.close()
        os.environ["MOVIEMETADB_API_KEY"] = "secret-key"
        web.store = None
        self.client = TestClient(web.app)

        r = self.client.get("/movies")
        self.assertEqual(r.status_code, 401)

        r = self.client.get("/movies", headers={"Authorization": "Bearer wrong-key"})
        self.assertEqual(r.status_code, 401)

        r = self.client.get("/movies", headers={"Authorization": "Bearer secret-key"})
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
