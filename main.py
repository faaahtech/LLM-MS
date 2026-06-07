from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import get_settings
from routes.chat_routes import router as chat_router
from routes.health_routes import router as health_router

settings = get_settings()

app = FastAPI(
    title="FaaahTech LLM-MS",
    version=settings.service_version,
    description="Microserviço conversacional da Assistente Acadêmica FaaahTech.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
