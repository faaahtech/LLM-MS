from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from config.settings import Settings, get_settings


class DatabaseMSClient:
    """Cliente HTTP da DATABASE-MS.

    Regra deste microserviço: não existe fallback mockado. Toda resposta vem da
    DATABASE-MS; quando uma rota falha, a falha é repassada de forma clara para
    o frontend/LLM.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.timeout = self.settings.request_timeout_seconds

    async def healthcheck(self) -> dict[str, Any]:
        return await self._get_json("/healthcheck")

    async def get_aluno(self, aluno_id: int, auth_token: str | None = None) -> dict[str, Any]:
        return await self._get_json(f"/alunos/{aluno_id}", auth_token=auth_token)

    async def get_matriculas_by_aluno(self, aluno_id: int, auth_token: str | None = None) -> list[dict[str, Any]]:
        return await self._get_json(f"/matriculas-curso/aluno/{aluno_id}", auth_token=auth_token)

    async def get_transfer_options(self, aluno_id: int, auth_token: str | None = None) -> dict[str, Any]:
        return await self._get_json(f"/alunos/{aluno_id}/opcoes-transferencia-horario", auth_token=auth_token)

    async def transfer_horario(
        self,
        matricula_id: int,
        id_curso_unidade_destino: int,
        periodo_destino: str | None = None,
        auth_token: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"id_curso_unidade_destino": id_curso_unidade_destino}
        if periodo_destino:
            payload["periodo_destino"] = periodo_destino
        return await self._post_json(f"/matriculas/{matricula_id}/transferir-horario", payload, auth_token=auth_token)

    async def trancar_matricula(self, matricula_id: int, auth_token: str | None = None) -> dict[str, Any]:
        return await self._post_json(f"/matriculas/{matricula_id}/trancar", {}, auth_token=auth_token)

    async def ativar_matricula(self, matricula_id: int, auth_token: str | None = None) -> dict[str, Any]:
        return await self._post_json(f"/matriculas/{matricula_id}/ativar", {}, auth_token=auth_token)

    async def get_resumo_semestre(self, aluno_id: int, auth_token: str | None = None) -> dict[str, Any]:
        return await self._get_json(f"/consultas/aluno/{aluno_id}/resumo-semestre-atual", auth_token=auth_token)

    async def get_resumo_aluno(self, aluno_id: int, auth_token: str | None = None) -> dict[str, Any]:
        return await self._get_json(f"/consultas/aluno/{aluno_id}/resumo", auth_token=auth_token)

    async def get_notas(self, aluno_id: int, auth_token: str | None = None) -> list[dict[str, Any]]:
        return await self._get_json(f"/consultas/aluno/{aluno_id}/notas", auth_token=auth_token)

    async def get_presencas(self, aluno_id: int, auth_token: str | None = None) -> list[dict[str, Any]]:
        return await self._get_json(f"/consultas/aluno/{aluno_id}/presencas", auth_token=auth_token)

    async def get_periodo_letivo_ativo(self, auth_token: str | None = None) -> dict[str, Any]:
        return await self._get_json("/consultas/periodo-letivo/ativo", auth_token=auth_token)

    async def get_disciplinas_curso_unidade(
        self,
        id_curso_unidade: int,
        auth_token: str | None = None,
    ) -> list[dict[str, Any]]:
        return await self._get_json(f"/consultas/curso-unidade/{id_curso_unidade}/disciplinas", auth_token=auth_token)

    async def get_calendarios_by_tipo(self, tipo: str, auth_token: str | None = None) -> list[dict[str, Any]]:
        return await self._get_json(f"/calendario-academico/tipo/{tipo}", auth_token=auth_token)

    async def get_calendario_pdf(self, aluno_id: int, auth_token: str | None = None) -> tuple[bytes, str, str]:
        return await self._get_bytes(f"/calendario-academico/aluno/{aluno_id}/pdf", auth_token=auth_token)

    async def search_base_conhecimento(self, categoria: str, auth_token: str | None = None) -> list[dict[str, Any]]:
        return await self._get_json(f"/base-conhecimento/categoria/{categoria}", auth_token=auth_token)

    async def _get_json(self, path: str, auth_token: str | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.settings.database_ms_url, timeout=self.timeout) as client:
            response = await client.get(path, headers=self._headers(auth_token))
        return self._handle_json_response(response)

    async def _post_json(self, path: str, payload: dict[str, Any], auth_token: str | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.settings.database_ms_url, timeout=self.timeout) as client:
            response = await client.post(path, json=payload, headers=self._headers(auth_token))
        return self._handle_json_response(response)

    async def _get_bytes(self, path: str, auth_token: str | None = None) -> tuple[bytes, str, str]:
        async with httpx.AsyncClient(base_url=self.settings.database_ms_url, timeout=self.timeout) as client:
            response = await client.get(path, headers=self._headers(auth_token))
        if response.status_code >= 400:
            self._raise_http_exception(response)
        content_type = response.headers.get("content-type", "application/pdf")
        filename = self._extract_filename(response.headers.get("content-disposition")) or "calendario-academico.pdf"
        return response.content, filename, content_type

    def _headers(self, auth_token: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _handle_json_response(self, response: httpx.Response) -> Any:
        if response.status_code >= 400:
            self._raise_http_exception(response)
        if not response.content:
            return {}
        return response.json()

    def _raise_http_exception(self, response: httpx.Response) -> None:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    def _extract_filename(self, content_disposition: str | None) -> str | None:
        if not content_disposition:
            return None
        marker = "filename="
        if marker not in content_disposition:
            return None
        filename = content_disposition.split(marker, 1)[1].strip()
        return filename.strip('"') or None
