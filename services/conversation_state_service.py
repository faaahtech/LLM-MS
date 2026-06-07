from __future__ import annotations

from copy import deepcopy
from typing import Any


class ConversationStateService:
    """Estado em memória para protótipo.

    Em produção, substitua por Redis ou banco leve, porque múltiplas réplicas do
    Container Apps não compartilham memória.
    """

    def __init__(self) -> None:
        self._state: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str, request_context: dict[str, Any] | None = None) -> dict[str, Any]:
        if request_context:
            return deepcopy(request_context)
        return deepcopy(self._state.get(session_id, {}))

    def set(self, session_id: str, context: dict[str, Any]) -> None:
        self._state[session_id] = deepcopy(context)

    def clear(self, session_id: str) -> None:
        self._state.pop(session_id, None)
