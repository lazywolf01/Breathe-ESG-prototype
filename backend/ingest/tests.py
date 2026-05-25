from django.test import TestCase
from rest_framework.test import APIClient

from .models import EmissionActivity, ReviewEvent


class IngestionWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_seed_creates_realistic_review_rows(self):
        response = self.client.post("/api/seed/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["stats"]["rows"], 14)
        self.assertEqual(EmissionActivity.objects.filter(status="flagged").count(), 4)
        self.assertEqual(ReviewEvent.objects.filter(action="ingested").count(), 14)

    def test_approved_rows_can_be_locked(self):
        self.client.post("/api/seed/")
        activity = EmissionActivity.objects.filter(status="pending").first()

        review = self.client.patch(
            f"/api/activities/{activity.id}/review/",
            {"status": "approved", "actor": "Unit test"},
            format="json",
        )
        lock = self.client.post("/api/lock-approved/", {"actor": "Unit test"}, format="json")
        activity.refresh_from_db()

        self.assertEqual(review.status_code, 200)
        self.assertEqual(lock.json()["locked"], 1)
        self.assertEqual(activity.status, "locked")

    def test_clear_removes_uploaded_rows(self):
        self.client.post("/api/seed/")

        response = self.client.post("/api/clear/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["stats"]["rows"], 0)
        self.assertEqual(EmissionActivity.objects.count(), 0)
