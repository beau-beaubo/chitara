from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from songs.generation.base import SongGenerationRequest
from songs.generation.suno import SunoConfig, SunoSongGeneratorStrategy
from songs.models import Song, SongStatus


class _DummyResponse:
	def __init__(self, payload):
		self._payload = payload

	def raise_for_status(self):
		return None

	def json(self):
		return self._payload


class SongGenerationMockApiTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create(
			username="tester",
			email="tester@example.com",
			first_name="Test",
			last_name="User",
		)
		self.song = Song.objects.create(
			title="Test Song",
			creator=self.user,
			prompt_text="lofi chill beat",
			voice_type="female",
			status=SongStatus.PENDING,
		)

	@override_settings(GENERATOR_STRATEGY="mock")
	def test_generate_mock_updates_song(self):
		resp = self.client.post(f"/api/songs/{self.song.id}/generate/")
		self.assertEqual(resp.status_code, 200)

		body = resp.json()
		self.assertEqual(body["generation"]["status"], "SUCCESS")
		self.assertTrue(body["song"]["generation_task_id"].startswith("mock_"))
		self.assertTrue(body["song"]["file_path"].startswith("mock://audio/mock_"))
		self.assertEqual(body["song"]["status"], SongStatus.COMPLETED)

		self.song.refresh_from_db()
		self.assertEqual(self.song.status, SongStatus.COMPLETED)
		self.assertIsNotNone(self.song.file_path)
		self.assertIsNotNone(self.song.generation_task_id)

	@override_settings(GENERATOR_STRATEGY="mock")
	def test_poll_without_task_id_returns_400(self):
		song = Song.objects.create(
			title="New Song",
			creator=self.user,
			prompt_text="ambient pad",
			voice_type="male",
		)
		resp = self.client.get(f"/api/songs/{song.id}/generate/")
		self.assertEqual(resp.status_code, 400)

	@override_settings(GENERATOR_STRATEGY="suno", SUNO_API_KEY="")
	def test_suno_missing_api_key_returns_500(self):
		resp = self.client.post(f"/api/songs/{self.song.id}/generate/")
		self.assertEqual(resp.status_code, 500)
		self.assertIn("Missing Suno API key", resp.json().get("error", ""))


class SunoStrategyUnitTests(TestCase):
	@patch("songs.generation.suno.requests.get")
	@patch("songs.generation.suno.requests.post")
	def test_suno_generate_and_get_details(self, post_mock, get_mock):
		post_mock.return_value = _DummyResponse(
			{"code": 200, "msg": "success", "data": {"taskId": "task_123"}}
		)
		get_mock.return_value = _DummyResponse(
			{
				"code": 200,
				"msg": "success",
				"data": {
					"taskId": "task_123",
					"status": "SUCCESS",
					"response": {
						"data": [
							{
								"audio_url": "https://example.com/audio.mp3",
								"title": "Generated Song",
								"duration": 180.5,
							}
						]
					},
				},
			}
		)

		strategy = SunoSongGeneratorStrategy(
			SunoConfig(api_key="test-key", base_url="https://api.sunoapi.org/api/v1")
		)

		start = strategy.generate(
			SongGenerationRequest(title="T", prompt="A calm piano track")
		)
		self.assertEqual(start.task_id, "task_123")
		self.assertEqual(start.status, "PENDING")

		details = strategy.get_details("task_123")
		self.assertEqual(details.task_id, "task_123")
		self.assertEqual(details.status, "SUCCESS")
		self.assertEqual(details.audio_url, "https://example.com/audio.mp3")
		self.assertEqual(details.title, "Generated Song")
		self.assertEqual(details.duration_seconds, 180.5)

		post_args, post_kwargs = post_mock.call_args
		self.assertEqual(post_args[0], "https://api.sunoapi.org/api/v1/generate")
		self.assertIn("Authorization", post_kwargs["headers"])
		self.assertEqual(post_kwargs["json"]["prompt"], "A calm piano track")

		get_args, get_kwargs = get_mock.call_args
		self.assertEqual(get_args[0], "https://api.sunoapi.org/api/v1/generate/record-info")
		self.assertEqual(get_kwargs["params"], {"taskId": "task_123"})
