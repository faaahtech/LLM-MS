from __future__ import annotations

from utils.text import normalize_text


class IntentService:
    """Detector determinístico de intenção para o MVP.

    Esta classe não contém dados acadêmicos mockados. Ela apenas classifica a
    mensagem do aluno para escolher qual endpoint da DATABASE-MS será consumido.
    """

    def detect(self, message: str, context: dict | None = None) -> str:
        text = normalize_text(message)
        active_flow = (context or {}).get("flow")

        if active_flow == "transferir_horario" and self._looks_like_option_choice(text):
            return "confirmar_transferencia_horario"

        if any(term in text for term in ["transferir", "trocar", "mudar"]) and any(
            term in text for term in ["horario", "periodo", "turno", "matricula"]
        ):
            return "transferir_horario"

        if any(term in text for term in ["trancar", "trancamento", "pausar matricula"]):
            return "trancar_matricula"

        if any(term in text for term in ["ativar", "reativar", "voltar matricula", "destrancar"]):
            return "ativar_matricula"

        if any(term in text for term in ["resumo", "grade", "semestre", "minhas aulas", "materias do semestre"]):
            return "resumo_semestre"

        if any(term in text for term in ["calendario em pdf", "baixar calendario", "pdf do calendario", "calendario pdf"]):
            return "calendario_pdf"

        if "estagio" in text or "estágio" in message.lower():
            return "orientacao_estagio"

        if any(term in text for term in ["nota", "notas", "media", "avaliacao"]):
            return "consultar_notas"

        if any(term in text for term in ["presenca", "presenças", "faltas", "falta", "frequencia"]):
            return "consultar_presencas"

        if any(term in text for term in ["status da matricula", "minha matricula", "meu ra", "ra"]):
            return "consultar_matricula"

        if any(term in text for term in ["prazo", "prazos", "rematricula", "trancamento", "prova", "feriado"]):
            return "consultar_calendario_tipo"

        if any(term in text for term in ["disciplinas do curso", "materias do curso", "matriz", "matriz curricular"]):
            return "consultar_disciplinas_curso"

        if any(term in text for term in ["calendario", "datas", "cronograma"]):
            return "consultar_calendario_tipo"

        return "fallback"

    def infer_calendar_type(self, message: str) -> str:
        text = normalize_text(message)
        if "prova" in text or "avaliacao" in text:
            return "prova"
        if "rematricula" in text or "rematrícula" in message.lower():
            return "rematricula"
        if "trancamento" in text or "trancar" in text:
            return "trancamento"
        if "feriado" in text:
            return "feriado"
        if "evento" in text:
            return "evento"
        return "prazo"

    def _looks_like_option_choice(self, text: str) -> bool:
        return text.startswith("opcao ") or text.startswith("opção ") or text.isdigit() or text in {
            "primeira", "primeiro", "segunda", "segundo", "terceira", "terceiro"
        }
