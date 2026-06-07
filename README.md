# FaaahTech LLM-MS

Microserviço conversacional da Assistente Acadêmica. Ele **não acessa o banco diretamente**: toda operação acadêmica passa pela `DATABASE-MS` via HTTP usando `httpx.AsyncClient`.

## Decisão desta versão

Esta versão removeu totalmente os dados mockados. A LLM-MS agora depende apenas dos endpoints reais da DATABASE-MS. Se a DATABASE-MS estiver offline ou retornar erro, a LLM-MS repassa o erro em vez de inventar dados.

## Fluxos cobertos

1. Transferência de horário de matrícula
   - `GET /alunos/{id_aluno}/opcoes-transferencia-horario`
   - `POST /matriculas/{id_matricula_curso}/transferir-horario`
2. Trancar matrícula
   - `GET /matriculas-curso/aluno/{id_aluno}`
   - `POST /matriculas/{id_matricula_curso}/trancar`
3. Ativar matrícula
   - `GET /matriculas-curso/aluno/{id_aluno}`
   - `POST /matriculas/{id_matricula_curso}/ativar`
4. Resumo do semestre/grade
   - `GET /consultas/aluno/{id_aluno}/resumo-semestre-atual`
5. Calendário acadêmico em PDF para o frontend
   - `GET /calendario-academico/aluno/{id_aluno}/pdf`
6. Orientação sobre estágio
   - `GET /base-conhecimento/categoria/estagio`

## Fluxos adicionais já implementados com rotas existentes

7. Consultar notas do aluno
   - `GET /consultas/aluno/{id_aluno}/notas`
8. Consultar presenças/faltas do aluno
   - `GET /consultas/aluno/{id_aluno}/presencas`
9. Consultar status/RA da matrícula
   - `GET /matriculas-curso/aluno/{id_aluno}`
10. Consultar prazos/eventos do calendário por tipo
   - `GET /calendario-academico/tipo/{tipo}`
11. Consultar disciplinas do curso/unidade atual
   - `GET /consultas/curso-unidade/{id_curso_unidade}/disciplinas`

## Rotas da LLM-MS

| Método | Rota | Objetivo |
|---|---|---|
| GET | `/healthcheck` | Status da LLM-MS |
| GET | `/healthcheck/database-ms` | Testa comunicação com a DATABASE-MS |
| POST | `/chat/message` | Entrada principal da conversa |
| GET | `/calendario-academico/pdf?aluno_id=1` | Repassa o PDF recebido da DATABASE-MS para o frontend |

## Executar local

```bash
cp .env.example .env
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8002
```

Configure a URL real da DATABASE-MS:

```env
DATABASE_MS_URL=http://localhost:8000
```

## Exemplo de requisição

```bash
curl -X POST http://localhost:8002/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-1","aluno_id":1,"message":"Quero transferir o meu horário"}'
```

Depois:

```bash
curl -X POST http://localhost:8002/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id":"demo-1","aluno_id":1,"message":"Opção 1"}'
```

## Observação

A intenção ainda é classificada por uma regra determinística simples para MVP. O conteúdo acadêmico e os dados de resposta vêm da DATABASE-MS.
