from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, InvalidOperation
from typing import Any

from utils.text import period_to_label


class ResponseBuilderService:
    def transfer_options(self, aluno_nome: str, sigla_curso: str, options: list[dict[str, Any]]) -> str:
        if not options:
            return (
                f"Certo, {aluno_nome}. A DATABASE-MS não retornou opções de transferência "
                f"para o curso {sigla_curso}."
            )

        lines = [f"Ok, {aluno_nome}. Temos as seguintes opções para o seu curso {sigla_curso}:", ""]
        for option in options:
            lines.append(f"{option.get('option_id')} - {option.get('label')}")
        lines.extend(["", "Deseja escolher qual opção?"])
        return "\n".join(lines)

    def transfer_success(self, aluno_nome: str, option: dict[str, Any], updated: dict[str, Any]) -> str:
        periodo = period_to_label(updated.get("periodo") or option.get("periodo") or "")
        label = option.get("label") or f"curso/unidade {updated.get('id_curso_unidade')} {periodo}".strip()
        return f"Transferindo a matrícula para {label}. Pronto, {aluno_nome}, a DATABASE-MS confirmou a alteração."

    def matricula_status(self, action: str, matricula: dict[str, Any]) -> str:
        ra = matricula.get("ra", "não informado")
        status = matricula.get("status", "não informado")
        if action == "trancar":
            return f"Sua matrícula foi marcada como **trancada** na DATABASE-MS. RA: {ra}. Status atual: {status}."
        return f"Sua matrícula foi marcada como **ativa/cursando** na DATABASE-MS. RA: {ra}. Status atual: {status}."

    def resumo_semestre(self, resumo: dict[str, Any]) -> str:
        aluno = resumo.get("aluno_nome") or resumo.get("nome") or "aluno"
        semestre = resumo.get("semestre_curso") or resumo.get("semestre") or "atual"
        periodo_letivo = resumo.get("periodo_letivo") or "período atual"
        grade = resumo.get("grade", [])

        lines = [
            f"Certo, {aluno}. Você está no {semestre}º semestre ({periodo_letivo}) e este é o resumo da sua grade:",
            "",
        ]
        if not grade:
            lines.append("A DATABASE-MS não retornou disciplinas vinculadas ao semestre atual.")
            return "\n".join(lines)

        for item in grade:
            lines.append(f"- Professor: {item.get('professor') or 'Não informado'}")
            lines.append(f"  Matéria: {item.get('disciplina') or 'Não informada'}")
            lines.append(f"  Horário: {item.get('horario') or 'Não informado'}")
            lines.append(f"  Dia: {item.get('dia_semana') or 'Não informado'}")
            if item.get("sala"):
                lines.append(f"  Sala: {item.get('sala')}")
            lines.append("")
        return "\n".join(lines).strip()

    def estagio(self, items: list[dict[str, Any]]) -> str:
        active_items = [item for item in items if item.get("status", "ativo") == "ativo"]
        if not active_items:
            return "A DATABASE-MS não retornou orientações ativas sobre estágio na base de conhecimento."
        lines = ["Encontrei estas orientações sobre estágio na base de conhecimento:", ""]
        for item in active_items[:3]:
            titulo = item.get("titulo", "Orientação")
            resposta = item.get("resposta", "Sem descrição cadastrada.")
            lines.append(f"**{titulo}**")
            lines.append(resposta)
            lines.append("")
        return "\n".join(lines).strip()

    def calendario_pdf(self) -> str:
        return "Encontrei o calendário acadêmico em PDF na DATABASE-MS. O frontend pode baixar/exibir pelo link retornado."

    def notas(self, notas: list[dict[str, Any]]) -> str:
        if not notas:
            return "A DATABASE-MS não retornou notas cadastradas para este aluno."
        by_disciplina: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for nota in notas:
            by_disciplina[nota.get("disciplina_nome") or "Disciplina não informada"].append(nota)

        lines = ["Estas são as notas encontradas na DATABASE-MS:", ""]
        for disciplina, itens in by_disciplina.items():
            lines.append(f"**{disciplina}**")
            for item in itens:
                avaliacao = item.get("avaliacao_nome") or f"Avaliação {item.get('id_avaliacao')}"
                valor = item.get("valor", "não informado")
                data = f" em {item.get('avaliacao_data')}" if item.get("avaliacao_data") else ""
                lines.append(f"- {avaliacao}{data}: {valor}")
            media = self._safe_average([item.get("valor") for item in itens])
            if media is not None:
                lines.append(f"  Média simples retornada: {media:.2f}")
            lines.append("")
        return "\n".join(lines).strip()

    def presencas(self, presencas: list[dict[str, Any]]) -> str:
        if not presencas:
            return "A DATABASE-MS não retornou registros de presença para este aluno."
        total = len(presencas)
        presentes = sum(1 for item in presencas if item.get("presente") is True)
        faltas = total - presentes
        percentual = (presentes / total) * 100 if total else 0
        lines = [
            "Resumo de presença encontrado na DATABASE-MS:",
            f"- Aulas registradas: {total}",
            f"- Presenças: {presentes}",
            f"- Faltas: {faltas}",
            f"- Frequência aproximada: {percentual:.1f}%",
            "",
            "Últimos registros:",
        ]
        for item in presencas[:8]:
            disciplina = item.get("disciplina_nome") or "Disciplina não informada"
            data = item.get("data_aula") or "data não informada"
            status = "presente" if item.get("presente") else "falta"
            lines.append(f"- {data} · {disciplina}: {status}")
        return "\n".join(lines)

    def matricula(self, matriculas: list[dict[str, Any]]) -> str:
        if not matriculas:
            return "A DATABASE-MS não retornou matrícula para este aluno."
        lines = ["Encontrei as seguintes matrículas na DATABASE-MS:", ""]
        for matricula in matriculas:
            periodo = period_to_label(matricula.get("periodo", ""))
            lines.append(f"- RA: {matricula.get('ra', 'não informado')}")
            lines.append(f"  Status: {matricula.get('status', 'não informado')}")
            lines.append(f"  Semestre do curso: {matricula.get('semestre_curso', 'não informado')}")
            lines.append(f"  Período: {periodo or matricula.get('periodo', 'não informado')}")
            lines.append(f"  Curso/unidade ID: {matricula.get('id_curso_unidade', 'não informado')}")
            lines.append("")
        return "\n".join(lines).strip()

    def calendario_tipo(self, tipo: str, eventos: list[dict[str, Any]]) -> str:
        if not eventos:
            return f"A DATABASE-MS não retornou eventos do tipo '{tipo}'."
        lines = [f"Eventos de calendário do tipo **{tipo}** encontrados na DATABASE-MS:", ""]
        for evento in eventos[:10]:
            inicio = evento.get("data_inicio") or "data não informada"
            fim = f" até {evento.get('data_fim')}" if evento.get("data_fim") else ""
            titulo = evento.get("titulo") or "Evento sem título"
            desc = f" — {evento.get('descricao')}" if evento.get("descricao") else ""
            lines.append(f"- {inicio}{fim}: {titulo}{desc}")
        return "\n".join(lines)

    def disciplinas_curso(self, disciplinas: list[dict[str, Any]], matricula: dict[str, Any]) -> str:
        if not disciplinas:
            return "A DATABASE-MS não retornou disciplinas para o curso/unidade da matrícula atual."
        lines = [
            f"Estas são as disciplinas vinculadas ao curso/unidade {matricula.get('id_curso_unidade')} na DATABASE-MS:",
            "",
        ]
        for disciplina in disciplinas[:20]:
            nome = disciplina.get("nome") or disciplina.get("disciplina_nome") or "Disciplina sem nome"
            codigo = disciplina.get("codigo") or disciplina.get("disciplina_codigo")
            semestre = disciplina.get("semestre_recomendado")
            obrigatoria = disciplina.get("obrigatoria")
            partes = [nome]
            if codigo:
                partes.append(f"cód. {codigo}")
            if semestre:
                partes.append(f"{semestre}º semestre")
            if obrigatoria is not None:
                partes.append("obrigatória" if obrigatoria else "optativa")
            lines.append("- " + " · ".join(partes))
        return "\n".join(lines)

    def fallback(self) -> str:
        return (
            "Posso ajudar com transferência de horário, trancamento/ativação de matrícula, "
            "resumo do semestre, calendário acadêmico em PDF, estágio, notas, presenças, "
            "status da matrícula, prazos do calendário e disciplinas do curso."
        )

    def _safe_average(self, values: list[Any]) -> float | None:
        parsed: list[Decimal] = []
        for value in values:
            try:
                parsed.append(Decimal(str(value)))
            except (InvalidOperation, TypeError, ValueError):
                continue
        if not parsed:
            return None
        return float(sum(parsed) / len(parsed))
