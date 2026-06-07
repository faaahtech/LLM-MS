import pytest

from dtos.chat_dto import ChatRequestDTO
from services.chat_service import ChatService


class FakeDatabaseClient:
    async def get_transfer_options(self, aluno_id: int, auth_token: str | None = None):
        return {
            "aluno": {"id": aluno_id, "nome": "teste"},
            "matricula_atual": {
                "id": 1,
                "id_aluno": aluno_id,
                "id_curso_unidade": 3,
                "ra": "202600001",
                "semestre_curso": 1,
                "periodo": "noturno",
                "status": "cursando",
            },
            "options": [
                {
                    "option_id": 1,
                    "id_curso_unidade": 1,
                    "curso": "Análise e Desenvolvimento de Sistemas",
                    "sigla": "ADS",
                    "unidade": "FATEC Zona Sul",
                    "periodo": "matutino",
                    "label": "ADS Manhã - FATEC Zona Sul",
                }
            ],
        }

    async def transfer_horario(self, matricula_id: int, id_curso_unidade_destino: int, periodo_destino=None, auth_token=None):
        return {
            "id": matricula_id,
            "id_aluno": 1,
            "id_curso_unidade": id_curso_unidade_destino,
            "ra": "202600001",
            "semestre_curso": 1,
            "periodo": periodo_destino or "matutino",
            "status": "cursando",
        }

    async def get_aluno(self, aluno_id: int, auth_token: str | None = None):
        return {"id": aluno_id, "nome": "Marcos"}

    async def get_matriculas_by_aluno(self, aluno_id: int, auth_token: str | None = None):
        return [
            {
                "id": 1,
                "id_aluno": aluno_id,
                "id_curso_unidade": 3,
                "ra": "202600001",
                "semestre_curso": 1,
                "periodo": "noturno",
                "status": "cursando",
            }
        ]

    async def trancar_matricula(self, matricula_id: int, auth_token: str | None = None):
        return {"id": matricula_id, "ra": "202600001", "status": "trancado"}

    async def ativar_matricula(self, matricula_id: int, auth_token: str | None = None):
        return {"id": matricula_id, "ra": "202600001", "status": "cursando"}

    async def get_resumo_semestre(self, aluno_id: int, auth_token: str | None = None):
        return {
            "id_aluno": aluno_id,
            "aluno_nome": "Marcos",
            "semestre_curso": 1,
            "periodo_letivo": "2026/1",
            "grade": [
                {
                    "disciplina": "Sociedade e Tecnologia",
                    "professor": "Admárcio",
                    "horario": "19:00 ~ 23:00",
                    "dia_semana": "Terça-feira",
                }
            ],
        }

    async def search_base_conhecimento(self, categoria: str, auth_token: str | None = None):
        return [{"titulo": "Estágio obrigatório", "resposta": "Orientação cadastrada.", "status": "ativo"}]

    async def get_notas(self, aluno_id: int, auth_token: str | None = None):
        return [{"disciplina_nome": "Engenharia de Software", "avaliacao_nome": "P1", "valor": "8.5"}]

    async def get_presencas(self, aluno_id: int, auth_token: str | None = None):
        return [{"disciplina_nome": "Engenharia de Software", "data_aula": "2026-06-01", "presente": True}]

    async def get_calendarios_by_tipo(self, tipo: str, auth_token: str | None = None):
        return [{"titulo": "Prazo de rematrícula", "data_inicio": "2026-06-10", "tipo": tipo}]

    async def get_disciplinas_curso_unidade(self, id_curso_unidade: int, auth_token: str | None = None):
        return [{"nome": "Engenharia de Software I", "codigo": "ESW1", "semestre_recomendado": 1, "obrigatoria": True}]


def make_service() -> ChatService:
    return ChatService(database_client=FakeDatabaseClient())


@pytest.mark.asyncio
async def test_transfer_flow_consumes_database_client() -> None:
    service = make_service()
    first = await service.process_message(
        ChatRequestDTO(session_id="test-1", aluno_id=1, message="Quero transferir o meu horário")
    )

    assert first.intent == "transferir_horario"
    assert first.requires_follow_up is True
    assert "ADS Manhã" in first.response
    assert first.sources == ["DATABASE-MS:GET /alunos/{id_aluno}/opcoes-transferencia-horario"]

    second = await service.process_message(
        ChatRequestDTO(session_id="test-1", aluno_id=1, message="Opção 1")
    )

    assert second.intent == "confirmar_transferencia_horario"
    assert second.requires_follow_up is False
    assert "DATABASE-MS confirmou" in second.response


@pytest.mark.asyncio
async def test_resumo_semestre_consumes_database_client() -> None:
    service = make_service()
    response = await service.process_message(
        ChatRequestDTO(session_id="test-2", aluno_id=1, message="Quero ver o resumo do semestre")
    )

    assert response.intent == "resumo_semestre"
    assert "Sociedade e Tecnologia" in response.response


@pytest.mark.asyncio
async def test_notas_flow() -> None:
    service = make_service()
    response = await service.process_message(ChatRequestDTO(session_id="test-3", aluno_id=1, message="Ver minhas notas"))
    assert response.intent == "consultar_notas"
    assert "8.5" in response.response


@pytest.mark.asyncio
async def test_presencas_flow() -> None:
    service = make_service()
    response = await service.process_message(ChatRequestDTO(session_id="test-4", aluno_id=1, message="Ver minhas faltas"))
    assert response.intent == "consultar_presencas"
    assert "Frequência" in response.response
