from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequestDTO(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="default", min_length=1, max_length=120)
    aluno_id: int | None = Field(default=1, description="ID do aluno autenticado no frontend/DATABASE-MS")
    auth_token: str | None = Field(default=None, description="Token JWT recebido do frontend, quando existir")
    context: dict[str, Any] | None = Field(default=None, description="Contexto enviado pelo frontend em fluxos multi-etapas")


class ChatResponseDTO(BaseModel):
    response: str
    intent: str
    requires_follow_up: bool = False
    context: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] | list[Any] | None = None
    sources: list[str] = Field(default_factory=list)


class TransferOptionDTO(BaseModel):
    option_id: int
    id_curso_unidade: int
    curso: str
    sigla: str
    unidade: str
    periodo: Literal["matutino", "vespertino", "noturno"] | str
    label: str


class CalendarPdfResponseDTO(BaseModel):
    filename: str
    content_type: str = "application/pdf"
