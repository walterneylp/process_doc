# 🚀 PROMPT SINGLE SHOT PARA CODEX

## Projeto: Enterprise Processing Engine (EPE)

---

Você deve gerar um projeto SaaS B2B completo chamado:

# Enterprise Processing Engine (EPE)

Um Motor de Processamento Empresarial com:

* Multi-tenant
* Multi-conta IMAP por empresa
* Processamento assíncrono
* Classificação híbrida (Regras + LLM)
* Extração estruturada de documentos
* Validação determinística
* Roteamento por setor
* Auditoria completa
* Dashboard simples
* Planos e limites SaaS

---

# 🔧 Stack Obrigatória

* Python 3.11+
* FastAPI
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis
* Celery
* JWT Auth
* IMAP (imaplib ou imapclient)
* LLM provider modular (OpenAI default)
* Docker + docker-compose

---

# 📁 Estrutura Obrigatória do Projeto

```
backend/
  app/
    main.py
    api/
      v1/
        auth.py
        tenants.py
        users.py
        email_accounts.py
        emails.py
        documents.py
        configs.py
        dashboard.py
    core/
      config.py
      security.py
      tenant_context.py
      logging.py
      limits.py
    domain/
      email/
      document/
      routing/
      audit/
      billing/
    engines/
      rules_engine/
        engine.py
      llm_classifier/
        engine.py
        prompts.py
        schemas.py
      extractor/
        engine.py
        schemas.py
      validator/
        engine.py
    adapters/
      email/
        imap_client.py
      storage/
        local.py
      notify/
        email_notify.py
        webhook_notify.py
      llm/
        provider.py
        openai_provider.py
    workers/
      celery_app.py
      tasks.py
      scheduler.py
    db/
      session.py
      models.py
      migrations/
    utils/
      crypto.py
      file_types.py
      jsonschema.py

docker-compose.yml
README.md
.env.example
requirements.txt
```

---

# 🧠 Arquitetura Obrigatória

## Monólito modular pronto para escalar

Separação clara de camadas:

* API não acessa DB diretamente
* Engines não acessam DB diretamente
* Persistência isolada
* Tudo com tenant_id obrigatório
* Tudo com trace_id para auditoria

---

# 🏢 Multi-Tenant

Todas as tabelas devem conter:

* tenant_id (UUID)
* created_at
* updated_at quando aplicável

JWT deve carregar:

* user_id
* tenant_id
* role

---

# 🗄️ Banco de Dados (Gerar migrations)

Criar todas as tabelas:

tenants
plans
tenant_usage
users
roles
user_roles
email_accounts
emails
email_attachments
documents
classifications
extractions
processing_runs
dead_letters
audit_logs
tenant_categories
tenant_rules
tenant_prompts
extraction_schemas

Campos completos conforme especificação abaixo.

---

# 📩 Email (IMAP)

Implementar:

* Cadastro de conta IMAP
* Teste de conexão
* Sync automático via scheduler
* Evitar duplicação por message_id
* Armazenar anexos no filesystem
* Hash SHA256 do anexo

Credenciais devem ser criptografadas com AES-GCM.

Chave deve vir de:

APP_ENC_KEY no .env

---

# 🔁 Pipeline Assíncrono

Celery + Redis

Estados do pipeline:

RECEIVED
QUEUED
PROCESSING
CLASSIFIED
EXTRACTED
VALIDATED
ROUTED
DONE
FAILED

Jobs obrigatórios:

sync_email_account(account_id)
process_email(email_id)
process_document(document_id)

---

# 🤖 Classificação Híbrida

Implementar:

## 1. RulesEngine

* palavras-chave
* domínio remetente
* tipo de anexo
* retorna categoria + confidence

Se confidence >= 0.85 → não chamar LLM.

## 2. LLMClassifier

* Deve retornar JSON estrito
* Campos:

  * category
  * department
  * confidence
  * priority
  * reason
* Usar OpenAI provider modular

Salvar no banco:

classifications

---

# 📄 Extração Estruturada

ExtractionEngine:

* Selecionar schema por tenant + doc_type
* Prompt deve exigir JSON válido
* Validar contra JSON Schema
* Reprocessar 1 vez se inválido
* Se falhar → dead_letters

Salvar em:

extractions (jsonb)

---

# 🧪 Validação Determinística

ValidatorEngine deve:

* Validar datas
* Validar valores monetários
* Validar formato CNPJ
* Validar campos obrigatórios

Se inválido:

* marcar needs_review
* registrar em dead_letters

---

# 🔀 Roteamento

RoutingEngine deve:

* Usar tenant_rules
* Usar categoria
* Usar prioridade
* Enviar email para lista configurada por departamento

Implementar EmailNotifyAdapter.

---

# 🛡️ Auditoria Obrigatória

Registrar audit_logs para:

* ingestão
* classificação
* extração
* validação
* roteamento
* reprocessamento
* ações manuais

Campos:

tenant_id
trace_id
event_type
entity_type
entity_id
payload (jsonb)

---

# 📊 Dashboard MVP

Endpoints:

GET /dashboard/summary
GET /dashboard/usage
GET /emails
GET /documents
GET /review

Interface HTML simples suficiente.

---

# 💰 Planos SaaS

Criar seed automático:

Starter
Pro
Business

Implementar verificação de limites antes de:

* processar email
* chamar LLM

Bloquear processamento se limite estourado.

---

# 🔐 Segurança

* Hash bcrypt para senha
* AES-GCM para IMAP
* JWT
* RBAC
* Filtro obrigatório por tenant_id
* Nunca logar credenciais

---

# 🐳 Docker

Gerar docker-compose com:

* postgres
* redis
* backend
* worker

---

# 📄 README

Explicar:

* como rodar
* como configurar .env
* como rodar migrations
* como criar primeiro tenant
* como conectar email

---

# 🎯 Critérios de Aceite

O sistema deve permitir:

1. Criar tenant
2. Criar usuário
3. Logar
4. Conectar IMAP
5. Rodar sync
6. Processar email
7. Classificar híbrido
8. Extrair PDF texto
9. Validar
10. Roteamento
11. Auditoria completa
12. Dashboard funcionando

---

# ⚠️ Regras de Código

* Código limpo
* Tipagem Python
* Comentários explicativos
* Modular
* Sem segredos no código
* Sem hardcoded API keys

---

# 🔚 Fim da instrução

Gerar o projeto completo com todos os arquivos, código funcional, migrations, docker-compose e README.

---

