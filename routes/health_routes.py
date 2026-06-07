from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from clients.database_client import DatabaseMSClient
from config.settings import get_settings

router = APIRouter(tags=["Healthcheck"])


@router.get("/healthcheck")
async def healthcheck() -> dict:
    settings = get_settings()
    return {
        "Status": "Online",
        "Service": settings.service_name,
        "Version": settings.service_version,
        "Current_Time": datetime.utcnow().isoformat(),
        "Database_MS_URL": settings.database_ms_url,
        "Mock_Mode": False,
    }


@router.get("/healthcheck/database-ms")
async def healthcheck_database_ms() -> dict:
    client = DatabaseMSClient()
    return await client.healthcheck()
