from __future__ import annotations

from fastapi import HTTPException

from clients.database_client import DatabaseMSClient
from dtos.chat_dto import ChatRequestDTO, ChatResponseDTO
from services.conversation_state_service import ConversationStateService
from services.intent_service import IntentService
from services.response_builder_service import ResponseBuilderService
from utils.text import extract_first_int, normalize_text


class ChatService:
    def __init__(
        self,
        database_client: DatabaseMSClient | None = None,
        state_service: ConversationStateService | None = None,
        intent_service: IntentService | None = None,
        response_builder: ResponseBuilderService | None = None,
    ) -> None:
        self.database_client = database_client or DatabaseMSClient()
        self.state_service = state_service or ConversationStateService()
        self.intent_service = intent_service or IntentService()
        self.response_builder = response_builder or ResponseBuilderService()

    async def process_message(self, request: ChatRequestDTO) -> ChatResponseDTO:
        context = self.state_service.get(request.session_id, request.context)
        intent = self.intent_service.detect(request.message, context)

        if request.aluno_id is None:
            return ChatResponseDTO(
                response="Preciso identificar o aluno autenticado para continuar. Envie o aluno_id no payload.",
                intent="missing_aluno_id",
                requires_follow_up=True,
                context=context,
            )

        if intent == "transferir_horario":
            return await self._start_transfer_flow(request)
        if intent == "confirmar_transferencia_horario":
            return await self._confirm_transfer_flow(request, context)
        if intent == "trancar_matricula":
            return await self._update_matricula_status(request, action="trancar")
        if intent == "ativar_matricula":
            return await self._update_matricula_status(request, action="ativar")
        if intent == "resumo_semestre":
            return await self._resumo_semestre(request)
        if intent == "calendario_pdf":
            return ChatResponseDTO(
                response=self.response_builder.calendario_pdf(),
                intent="calendario_pdf",
                requires_follow_up=False,
                context={"download_url": f"/calendario-academico/pdf?aluno_id={request.aluno_id}"},
                data={"download_url": f"/calendario-academico/pdf?aluno_id={request.aluno_id}"},
                sources=["DATABASE-MS:GET /calendario-academico/aluno/{id_aluno}/pdf"],
            )
        if intent == "orientacao_estagio":
            return await self._orientacao_estagio(request)
        if intent == "consultar_notas":
            return await self._consultar_notas(request)
        if intent == "consultar_presencas":
            return await self._consultar_presencas(request)
        if intent == "consultar_matricula":
            return await self._consultar_matricula(request)
        if intent == "consultar_calendario_tipo":
            return await self._consultar_calendario_tipo(request)
        if intent == "consultar_disciplinas_curso":
            return await self._consultar_disciplinas_curso(request)

        return ChatResponseDTO(response=self.response_builder.fallback(), intent="fallback")

    async def _start_transfer_flow(self, request: ChatRequestDTO) -> ChatResponseDTO:
        result = await self.database_client.get_transfer_options(request.aluno_id or 1, auth_token=request.auth_token)
        aluno = result.get("aluno", {})
        matricula_atual = result.get("matricula_atual", {})
        options = result.get("options", [])

        aluno_nome = aluno.get("nome", "aluno")
        sigla_curso = options[0].get("sigla", "curso") if options else "curso"
        response = self.response_builder.transfer_options(aluno_nome, sigla_curso, options)

        context = {
            "flow": "transferir_horario",
            "aluno_id": request.aluno_id,
            "matricula_id": matricula_atual.get("id"),
            "options": options,
        }
        self.state_service.set(request.session_id, context)
        return ChatResponseDTO(
            response=response,
            intent="transferir_horario",
            requires_follow_up=bool(options),
            context=context,
            data=result,
            sources=["DATABASE-MS:GET /alunos/{id_aluno}/opcoes-transferencia-horario"],
        )

    async def _confirm_transfer_flow(self, request: ChatRequestDTO, context: dict) -> ChatResponseDTO:
        options = context.get("options", [])
        matricula_id = context.get("matricula_id")
        chosen = self._find_chosen_option(request.message, options)
        if chosen is None:
            return ChatResponseDTO(
                response="Não consegui identificar a opção escolhida. Responda com o número da opção, por exemplo: Opção 1.",
                intent="confirmar_transferencia_horario",
                requires_follow_up=True,
                context=context,
                data=options,
            )
        if not matricula_id:
            raise HTTPException(status_code=400, detail="Contexto sem matrícula para transferência.")

        updated = await self.database_client.transfer_horario(
            matricula_id=int(matricula_id),
            id_curso_unidade_destino=int(chosen["id_curso_unidade"]),
            periodo_destino=chosen.get("periodo"),
            auth_token=request.auth_token,
        )
        aluno = await self.database_client.get_aluno(request.aluno_id or 1, auth_token=request.auth_token)
        self.state_service.clear(request.session_id)
        return ChatResponseDTO(
            response=self.response_builder.transfer_success(aluno.get("nome", "aluno"), chosen, updated),
            intent="confirmar_transferencia_horario",
            requires_follow_up=False,
            context={},
            data=updated,
            sources=["DATABASE-MS:POST /matriculas/{id_matricula_curso}/transferir-horario"],
        )

    async def _update_matricula_status(self, request: ChatRequestDTO, action: str) -> ChatResponseDTO:
        matriculas = await self.database_client.get_matriculas_by_aluno(request.aluno_id or 1, auth_token=request.auth_token)
        matricula = self._pick_relevant_matricula(matriculas)
        if action == "trancar":
            updated = await self.database_client.trancar_matricula(int(matricula["id"]), auth_token=request.auth_token)
            intent = "trancar_matricula"
        else:
            updated = await self.database_client.ativar_matricula(int(matricula["id"]), auth_token=request.auth_token)
            intent = "ativar_matricula"
        return ChatResponseDTO(
            response=self.response_builder.matricula_status(action, updated),
            intent=intent,
            requires_follow_up=False,
            data=updated,
            sources=[f"DATABASE-MS:POST /matriculas/{{id_matricula_curso}}/{action}"],
        )

    async def _resumo_semestre(self, request: ChatRequestDTO) -> ChatResponseDTO:
        resumo = await self.database_client.get_resumo_semestre(request.aluno_id or 1, auth_token=request.auth_token)
        return ChatResponseDTO(
            response=self.response_builder.resumo_semestre(resumo),
            intent="resumo_semestre",
            data=resumo,
            sources=["DATABASE-MS:GET /consultas/aluno/{id_aluno}/resumo-semestre-atual"],
        )

    async def _orientacao_estagio(self, request: ChatRequestDTO) -> ChatResponseDTO:
        items = await self.database_client.search_base_conhecimento("estagio", auth_token=request.auth_token)
        return ChatResponseDTO(
            response=self.response_builder.estagio(items),
            intent="orientacao_estagio",
            data=items,
            sources=["DATABASE-MS:GET /base-conhecimento/categoria/estagio"],
        )

    async def _consultar_notas(self, request: ChatRequestDTO) -> ChatResponseDTO:
        notas = await self.database_client.get_notas(request.aluno_id or 1, auth_token=request.auth_token)
        return ChatResponseDTO(
            response=self.response_builder.notas(notas),
            intent="consultar_notas",
            data=notas,
            sources=["DATABASE-MS:GET /consultas/aluno/{id_aluno}/notas"],
        )

    async def _consultar_presencas(self, request: ChatRequestDTO) -> ChatResponseDTO:
        presencas = await self.database_client.get_presencas(request.aluno_id or 1, auth_token=request.auth_token)
        return ChatResponseDTO(
            response=self.response_builder.presencas(presencas),
            intent="consultar_presencas",
            data=presencas,
            sources=["DATABASE-MS:GET /consultas/aluno/{id_aluno}/presencas"],
        )

    async def _consultar_matricula(self, request: ChatRequestDTO) -> ChatResponseDTO:
        matriculas = await self.database_client.get_matriculas_by_aluno(request.aluno_id or 1, auth_token=request.auth_token)
        return ChatResponseDTO(
            response=self.response_builder.matricula(matriculas),
            intent="consultar_matricula",
            data=matriculas,
            sources=["DATABASE-MS:GET /matriculas-curso/aluno/{id_aluno}"],
        )

    async def _consultar_calendario_tipo(self, request: ChatRequestDTO) -> ChatResponseDTO:
        tipo = self.intent_service.infer_calendar_type(request.message)
        eventos = await self.database_client.get_calendarios_by_tipo(tipo, auth_token=request.auth_token)
        return ChatResponseDTO(
            response=self.response_builder.calendario_tipo(tipo, eventos),
            intent="consultar_calendario_tipo",
            data={"tipo": tipo, "eventos": eventos},
            sources=["DATABASE-MS:GET /calendario-academico/tipo/{tipo}"],
        )

    async def _consultar_disciplinas_curso(self, request: ChatRequestDTO) -> ChatResponseDTO:
        matriculas = await self.database_client.get_matriculas_by_aluno(request.aluno_id or 1, auth_token=request.auth_token)
        matricula = self._pick_relevant_matricula(matriculas)
        id_curso_unidade = int(matricula["id_curso_unidade"])
        disciplinas = await self.database_client.get_disciplinas_curso_unidade(
            id_curso_unidade,
            auth_token=request.auth_token,
        )
        return ChatResponseDTO(
            response=self.response_builder.disciplinas_curso(disciplinas, matricula),
            intent="consultar_disciplinas_curso",
            data={"matricula": matricula, "disciplinas": disciplinas},
            sources=["DATABASE-MS:GET /consultas/curso-unidade/{id_curso_unidade}/disciplinas"],
        )

    def _find_chosen_option(self, message: str, options: list[dict]) -> dict | None:
        number = extract_first_int(message)
        if number is not None:
            for option in options:
                if int(option.get("option_id", -1)) == number:
                    return option

        text = normalize_text(message)
        for option in options:
            label = normalize_text(option.get("label", ""))
            if label and label in text:
                return option
            period = normalize_text(option.get("periodo", ""))
            if period and period in text:
                return option
        return None

    def _pick_relevant_matricula(self, matriculas: list[dict]) -> dict:
        if not matriculas:
            raise HTTPException(status_code=404, detail="Nenhuma matrícula encontrada para o aluno.")
        for matricula in matriculas:
            if matricula.get("status") in {"cursando", "trancado"}:
                return matricula
        return matriculas[0]
