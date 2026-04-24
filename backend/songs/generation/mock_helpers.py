from __future__ import annotations

import hashlib

from .base import SongGenerationRequest


def make_mock_task_id(request: SongGenerationRequest) -> str:
    stable_key = "|".join(
        [
            request.title,
            request.prompt,
            request.voice_type or "",
            str(request.duration_seconds or ""),
        ]
    )
    digest = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:12]
    return f"mock_{digest}"
