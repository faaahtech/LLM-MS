from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    service_name: str = os.getenv("SERVICE_NAME", "LLM-MS")
    service_version: str = os.getenv("SERVICE_VERSION", "1.1.0")
    database_ms_url: str = os.getenv("DATABASE_MS_URL", "http://localhost:8001").rstrip("/")
    whisper_ms_url: str = os.getenv("WHISPER_MS_URL", "http://localhost:8002").rstrip("/")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    cors_allow_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
        if origin.strip()
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
