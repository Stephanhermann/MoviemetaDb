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

    def test_api_key_auth(self):
        self.client.close()
        os.environ["MOVIEMETADB_API_KEY"] = "secret-key"
        web.store = None
        self.client = TestClient(web.app)

        r = self.client.get("/movies")
        self.assertEqual(r.status_code, 401)

        r = self.client.get("/movies", headers={"Authorization": "Bearer secret-key"})
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
