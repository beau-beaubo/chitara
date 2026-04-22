from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SongGenerationRequest:
    title: str
    prompt: str
    voice_type: str | None = None
    duration_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class SongGenerationResult:
    task_id: str
    status: str
    audio_url: str | None = None
    stream_audio_url: str | None = None
    duration_seconds: float | None = None
    title: str | None = None
    raw: Mapping[str, Any] | None = None


class SongGeneratorStrategy(ABC):
    @abstractmethod
    def generate(self, request: SongGenerationRequest) -> SongGenerationResult:
        """Start generation.

        Returns a result that may either:
        - contain final output fields (e.g., mock), or
        - contain only a task reference for later polling (e.g., Suno).
        """

    @abstractmethod
    def get_details(self, task_id: str) -> SongGenerationResult:
        """Fetch generation status/details for an existing task."""
