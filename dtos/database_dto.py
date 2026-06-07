from __future__ import annotations

from pydantic import BaseModel


class MatriculaCursoDTO(BaseModel):
    id: int
    id_aluno: int
    id_curso_unidade: int
    ra: str
    semestre_curso: int
    periodo: str
    status: str
    ano_ingresso: int | None = None
    semestre_ingresso: int | None = None


class CursoUnidadeDTO(BaseModel):
    id: int
    id_curso: int | None = None
    id_unidade: int | None = None
    curso_nome: str | None = None
    curso_sigla: str | None = None
    unidade_nome: str | None = None
    periodo: str | None = None
