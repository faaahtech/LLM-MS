from __future__ import annotations

from fastapi import APIRouter, Header, Query, status
from fastapi.responses import Response

from controller.chat_controller import ChatController
from dtos.chat_dto import ChatRequestDTO, ChatResponseDTO

router = APIRouter(tags=["Chat"])
controller = ChatController()


@router.post("/chat/message", response_model=ChatResponseDTO, status_code=status.HTTP_200_OK)
async def chat_message(data: ChatRequestDTO) -> ChatResponseDTO:
    return await controller.process_message(data)


@router.get("/calendario-academico/pdf", status_code=status.HTTP_200_OK)
async def get_calendario_pdf(
    aluno_id: int = Query(default=1, ge=1),
    authorization: str | None = Header(default=None),
) -> Response:
    token = authorization.replace("Bearer ", "", 1) if authorization else None
    return await controller.get_calendario_pdf(aluno_id=aluno_id, auth_token=token)
