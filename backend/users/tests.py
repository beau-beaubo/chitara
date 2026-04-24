from django.contrib.auth import get_user_model
from django.test import TestCase


class UsersApiTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create(
			username="user1",
			email="user1@example.com",
			first_name="User",
			last_name="One",
		)

	def test_me_unauthenticated(self):
		resp = self.client.get("/api/me/")
		self.assertEqual(resp.status_code, 200)
		body = resp.json()
		self.assertFalse(body["authenticated"])
		self.assertIsNone(body["user"])

	def test_me_authenticated_and_logout(self):
		self.client.force_login(self.user)

		resp = self.client.get("/api/me/")
		self.assertEqual(resp.status_code, 200)
		body = resp.json()
		self.assertTrue(body["authenticated"])
		self.assertEqual(body["user"]["id"], self.user.id)

		logout_resp = self.client.post("/api/logout/")
		self.assertEqual(logout_resp.status_code, 200)
		self.assertTrue(logout_resp.json()["logged_out"])

		resp2 = self.client.get("/api/me/")
		self.assertFalse(resp2.json()["authenticated"])
