# Portal da Transparência SaaS

Sistema de monitoramento automatizado de contratos governamentais via [Portal da Transparência](https://portaldatransparencia.gov.br/) do Governo Federal. Busca empenhos por CNPJ, enriquece com itens, histórico e documentos relacionados, e exporta para XLSX/ODS/CSV.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Web | Python 3.13 · Flask 3 · Gunicorn (2 workers) |
| Worker | Celery 5 · Python 3.12 |
| Banco | PostgreSQL 16 |
| Cache / Fila | Redis 7 |
| Auth | Flask-Login · JWT (HS256) · bcrypt (12 rounds) |
| Export | openpyxl · odfpy · csv |
| Deploy | Docker Compose · GitHub Actions → Docker Hub → Coolify |

---

## Arquitetura

```
Browser
  │
  ▼
Flask (Gunicorn, porta 5000)
  │  JWT auth via cookie + UserSession no PostgreSQL
  │
  ├─► POST /searches → Celery: fetch_search_results
  │     └─► Portal API (rate-limitada via Redis token bucket)
  │           └─► PostgreSQL: Search + SearchResult (raw_json, detail_json)
  │                 └─► Celery: fetch_enrichment (itens, historico, empresa)
  │                       └─► enrichment_json salvo no JSONB
  │
  └─► POST /searches/<id>/export/<fmt> → Celery: generate_*_task
        └─► flatten_search() → render_*() → base64 no Redis
              └─► GET /export/download/<task_id> → stream para browser
```

**Rate limiting:** Redis token bucket atômico (Lua script). 400 req/min (dia) · 700 req/min (00h–06h). Compartilhado entre todos os workers.

---

## Estrutura do Projeto

```
portal-transparencia/
├── src/
│   ├── app.py              # Flask app, todas as rotas
│   ├── tasks.py            # Celery tasks (fetch, enrich, export)
│   ├── portal_api.py       # Client da API do Portal (retry + backoff)
│   ├── rate_limit.py       # Token bucket Redis (Lua)
│   ├── db.py               # SQLAlchemy init
│   ├── auth/
│   │   ├── models.py       # User, UserSession, ApiKey, Search, SearchResult
│   │   ├── routes.py       # /auth/login, /register, /logout, /sessions
│   │   ├── utils.py        # bcrypt, JWT, rate limiter login, sanitização
│   │   └── decorators.py   # @require_auth, @require_role, @require_api_key
│   ├── exports/
│   │   ├── serializer.py   # flatten_search() — transforma DB em estrutura para export
│   │   ├── parse.py        # parse de moeda BR, datas, URLs do Portal
│   │   ├── xlsx_renderer.py
│   │   ├── ods_renderer.py
│   │   └── csv_renderer.py
│   ├── templates/          # Jinja2 (Tailwind CSS via CDN)
│   └── static/             # CSS design system, fontes
├── Dockerfile              # Imagem web (gunicorn)
├── Dockerfile.worker       # Imagem worker (celery)
├── docker-compose.yml      # Stack de produção
├── docker-compose.local.yml
├── requirements.txt
└── .env.example
```

---

## Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `SECRET_KEY` | **Sim** | Chave Flask/JWT — mínimo 32 chars aleatórios |
| `DATABASE_URL` | **Sim** | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | **Sim** | `redis://redis:6379/0` |
| `API_KEY_PORTAL` | **Sim** | Chave da API do Portal da Transparência |
| `POSTGRES_USER` | Sim (compose) | Usuário do banco |
| `POSTGRES_PASSWORD` | Sim (compose) | Senha do banco |
| `POSTGRES_DB` | Sim (compose) | Nome do banco |
| `APP_ENV` | Não | `production` ou `local` |
| `LIMIT_DAY` | Não | Req/min para API do Portal (padrão: 400) |
| `LIMIT_NIGHT` | Não | Req/min de 00h–06h (padrão: 700) |
| `DISABLE_RATE_LIMIT` | Não | `true` para desabilitar em testes |

---

## Rodando Localmente

```bash
cp .env.example .env.local
# Edite .env.local com suas credenciais

docker-compose -f docker-compose.local.yml up -d

# Inicializa o banco (primeira vez)
docker-compose exec web flask init-db

# Verifica saúde
curl http://localhost:5000/health
```

---

## Fluxo de Dados — Busca

1. Usuário informa CNPJ (+ filtro de pregão opcional)
2. `Search` criada com `status='pending'`
3. Celery task `fetch_search_results` busca empenhos anos 2024–atual via API do Portal
4. Cada empenho vira um `SearchResult` com `raw_json` + `detail_json`
5. `fetch_enrichment` enfileirado por resultado: busca itens, histórico e empresa
6. Frontend faz polling em `/searches/<id>/status` até `status='done'`

---

## Exportação

- Usuário seleciona quais empenhos incluir (checkbox `included`)
- Clica em "Exportar XLSX/ODS/CSV"
- Task `generate_*_task` executa `flatten_search()` e serializa o arquivo
- Frontend faz polling em `/export/<fmt>/status/<task_id>`
- Download via `/export/<fmt>/download/<task_id>`

---

## Autenticação

- Registro com validação de senha forte (8+ chars, maiúscula, minúscula, número, especial)
- Login gera JWT (24h, ou 30 dias com "lembrar-me") + registro em `user_sessions`
- Cada request autenticado valida JWT + checa `UserSession.is_active`
- Troca de senha invalida todas as outras sessões ativas

---

## CI/CD

```
git push main
  └─► GitHub Actions
        ├─► build web → vogelcodes/portal-transp-web:latest
        ├─► build worker → vogelcodes/portal-transp-worker:latest
        └─► Coolify webhook → pull + restart stack
```

---

## Imagens Docker

```
vogelcodes/portal-transp-web:latest
vogelcodes/portal-transp-worker:latest
```

---

## Rotas Principais

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Formulário de busca |
| GET/POST | `/searches` | Lista e cria buscas |
| GET | `/searches/<id>` | Resultados da busca |
| GET | `/searches/<id>/status` | Status JSON (polling) |
| POST | `/searches/<id>/export/xlsx` | Inicia export XLSX |
| GET | `/searches/<id>/export/xlsx/download/<task_id>` | Download XLSX |
| POST | `/auth/login` | Login |
| POST | `/auth/register` | Registro |
| GET | `/health` | Health check Docker |

---

## Débito Técnico Conhecido

- Rate limiter de login (`auth/utils.py`) é in-memory por processo — em 2+ workers a proteção é parcial. Migrar para Redis.
- Rotas de export ODS/XLSX/CSV são código duplicado. Consolidar em handler genérico.
- Endpoint `/info` não exige autenticação. Adicionar `@require_auth`.
- Sem proteção CSRF. Adicionar `flask-wtf`.
- Anos de busca hardcoded (`2024, 2025, current_year`). Tornar configurável.
