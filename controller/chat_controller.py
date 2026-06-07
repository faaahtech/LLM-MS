from __future__ import annotations

from fastapi import Response

from clients.database_client import DatabaseMSClient
from dtos.chat_dto import ChatRequestDTO, ChatResponseDTO
from services.chat_service import ChatService


class ChatController:
    def __init__(self) -> None:
        self.chat_service = ChatService()
        self.database_client = DatabaseMSClient()

    async def process_message(self, request: ChatRequestDTO) -> ChatResponseDTO:
        return await self.chat_service.process_message(request)

    async def get_calendario_pdf(self, aluno_id: int, auth_token: str | None = None) -> Response:
        content, filename, content_type = await self.database_client.get_calendario_pdf(
            aluno_id=aluno_id,
            auth_token=auth_token,
        )
        headers = {"Content-Disposition": f'inline; filename="{filename}"'}
        return Response(content=content, media_type=content_type, headers=headers)
