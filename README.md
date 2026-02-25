# Enterprise Processing Engine (EPE)

SaaS B2B multi-tenant para ingestão de e-mails IMAP, classificação híbrida (regras + LLM), extração estruturada, validação determinística, roteamento e auditoria.

## Stack
- Python 3.11+
- FastAPI
- PostgreSQL + SQLAlchemy + Alembic
- Redis + Celery
- JWT Auth + RBAC
- IMAP via `imapclient`
- Provider LLM modular (OpenAI default)
- Docker Compose

## Como rodar
1. Copie variáveis:
```bash
cp .env.example .env
```
2. Suba serviços:
```bash
docker compose up -d
```
3. Aplique migração:
```bash
docker compose exec backend bash -lc "alembic -c backend/alembic.ini upgrade head"
```

## Endpoints principais
- `GET /dashboard` (UI do dashboard SaaS)
- `POST /api/v1/tenants`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/email-accounts`
- `POST /api/v1/email-accounts/{id}/test`
- `POST /api/v1/email-accounts/{id}/sync`
- `GET /api/v1/emails`
- `GET /api/v1/documents`
- `GET /api/v1/documents/review`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/usage`
- `GET /api/v1/dashboard/html`

## Fluxo de aceite
1. Criar tenant
2. Criar usuário admin (via `register`)
3. Login e obter JWT
4. Conectar IMAP
5. Rodar sync da conta
6. Processar emails/documentos no worker
7. Ver classificação, extração e validação
8. Conferir dashboard e auditoria

## Dashboard SaaS (local)
- URL: `http://localhost:8011/dashboard`
- Login: use um usuário criado em `POST /api/v1/auth/register`.
- O menu lateral mostra `version` e `build` no rodapé.

## Primeiro tenant (exemplo)
```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme","slug":"acme"}'
```

## Conectar e-mail IMAP (exemplo)
```bash
curl -X POST http://localhost:8000/api/v1/email-accounts \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Financeiro",
    "imap_host":"imap.example.com",
    "imap_port":993,
    "imap_username":"finance@example.com",
    "imap_password":"secret",
    "use_ssl":true
  }'
```

## Segurança
- Senha com bcrypt
- Credenciais IMAP com AES-GCM (`APP_ENC_KEY`)
- JWT com `user_id`, `tenant_id`, `role`
- Filtro por `tenant_id` nas consultas
- Sem logging de credenciais

## Observações
- Este MVP usa parse simplificado de corpo de e-mail para extração.
- O provider OpenAI entra em fallback se `OPENAI_API_KEY` não estiver definido.
