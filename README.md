# Biopark — Desafio 4: Consulta de Protocolos

Plataforma web para **cadastro, acompanhamento e consulta automatizada** de protocolos em órgãos públicos, com dashboard, histórico de movimentações, evidências (screenshot), relatórios em PDF e assistente com IA.

Desenvolvida no contexto do **Hackathon Biopark** (Desafio 4).

---

## Funcionalidades

- **Gestão de protocolos**: CRUD, filtros por projeto/status, importação de planilha `.xlsx`
- **Consultas automatizadas**: execução individual ou em lote nos sites dos órgãos
- **Histórico**: cada consulta grava status, observação, `fonte_consulta`, mudanças detectadas e screenshot quando disponível
- **Dashboard**: visão consolidada, notificações e comparação real vs. simulado
- **Relatórios**: PDF analítico e área restrita a administradores
- **Assistente IA**: chat para consultas em linguagem natural (requer `OPENAI_API_KEY`)
- **Alertas por e-mail** (opcional, via SMTP)

---

## Stack

| Camada | Tecnologia | Deploy sugerido |
|--------|------------|-----------------|
| API | Python 3.10+, FastAPI | [Railway](https://railway.app) (`backend/`) |
| Banco | Supabase (PostgreSQL) | [Supabase](https://supabase.com) |
| Front | React, Vite, Tailwind | [Vercel](https://vercel.com) (`frontend/`) |

---

## Consultas aos órgãos

A plataforma distingue consulta **real** (Playwright nos portais públicos) e **simulada** (respostas em código, prefixo `SIMULADO:` em `fonte_consulta`).

| Órgão / cenário | Modo | Implementação |
|-----------------|------|----------------|
| Cartório de Imóveis (PR) — `cartoriospr.com.br` | **Real** | `backend/app/services/scraper.py` |
| COPEL Distribuição — acompanhamento de solicitações | **Real** | `scrapers/copel_distribuicao.py` |
| SANEPAR — ePROTOCOLO PR | **Real** | `scrapers/sanepar.py` |
| Corpo de Bombeiros (CBPR) — ePROTOCOLO PR | **Real** | `scrapers/eprotocolo_pr.py` |
| CARMEL / Equiplano — Município de Toledo | **Real** | `scrapers/equiplano_toledo.py` |
| COPEL (portal genérico) | Simulado | `scrapers/copel.py` |
| SEMA / IAT, Caixa, Prefeitura, Bombeiros (URL legada) | Simulado | scrapers dedicados ou `default.py` |

**Demonstração sugerida para a banca:** consultar um protocolo de cartório ou SANEPAR (real) e um de COPEL genérico ou SEMA (simulado) e comparar o campo `fonte_consulta` no histórico.

---

## Estrutura do repositório

```
hackathon-biopark/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI
│   │   ├── config.py            # Variáveis de ambiente
│   │   ├── supabase_client.py   # Cliente Supabase
│   │   ├── routers/             # auth, protocols, scraping, reports, agent
│   │   ├── schemas/             # Pydantic
│   │   └── services/            # scraper, importer, report, scrapers/
│   ├── supabase_schema.sql      # Schema inicial
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/pages/               # Login, Dashboard, Protocols, Reports
│   └── .env.example
├── Planilhas/                   # Modelos e script de transformação da carga inicial
├── scripts/                     # setup.js, run-backend.js
├── COMO_RODAR.md                # Guia rápido de execução local
└── package.json                 # npm run dev (sobe API + front)
```

---

## Execução local

Guia passo a passo: **[COMO_RODAR.md](COMO_RODAR.md)**

Resumo na raiz do projeto:

```bash
npm run dev
```

Isso instala dependências (Node + Python), cria `.env` a partir dos exemplos se necessário, instala o Chromium do Playwright e sobe:

- API: http://localhost:8000 (docs: http://localhost:8000/docs)
- Frontend: http://localhost:5173

### Variáveis de ambiente

| Arquivo | Variáveis |
|---------|-----------|
| `backend/.env` | Copie de `backend/.env.example` — Supabase, JWT, login, OpenAI e SMTP (opcionais) |
| `frontend/.env` | `VITE_API_URL=http://localhost:8000` |

**Importante:** arquivos `.env` não são versionados. Configure credenciais apenas no ambiente local ou no painel do Railway/Vercel.

### Banco de dados

1. Crie um projeto no Supabase.
2. Execute `backend/supabase_schema.sql` no SQL Editor.
3. Aplique migrações adicionais em `backend/migration_*.sql`, se necessário.
4. Cadastre usuários na tabela `usuarios` ou use as credenciais de `DASHBOARD_*` no `.env`.

### Carga inicial

Planilhas modelo em `Planilhas/`. Use **Importar planilha** no sistema ou o script `Planilhas/transformar_protocolos.py` para gerar a carga a partir da base do desafio.

---

## Deploy

### Backend (Railway)

1. Novo projeto apontando para `backend/`
2. Variáveis do `.env.example`
3. `nixpacks.toml` já instala dependências e `playwright install chromium`

### Frontend (Vercel)

1. Projeto na pasta `frontend/`
2. `VITE_API_URL` = URL pública do backend
3. `vercel.json` configura roteamento SPA

---

## API — endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/login` | Login |
| GET | `/protocols/` | Listar protocolos |
| POST | `/protocols/` | Criar protocolo |
| PATCH | `/protocols/{id}` | Editar |
| DELETE | `/protocols/{id}` | Inativar / excluir |
| POST | `/import/spreadsheet` | Importar `.xlsx` |
| POST | `/scraping/run-all` | Consultar todos os ativos |
| POST | `/scraping/run/{id}` | Consultar um protocolo |
| GET | `/reports/dashboard-data` | Dados do dashboard |
| GET | `/reports/pdf` | Relatório PDF |
| POST | `/agent/chat` | Assistente IA |

---

## Acesso (demonstração)

Usuários ficam na tabela `usuarios` do Supabase. Para ambiente de demonstração, o `.env.example` sugere:

| Campo | Exemplo |
|-------|---------|
| E-mail | `admin@biopark.com.br` |
| Senha | conforme `DASHBOARD_PASSWORD` no `.env` |

A área **Relatórios** (`/reports`) exige cargo `admin` e segundo login em `/reports-login`.

---

## Segurança

- Não commite `.env`, chaves de API nem senhas de e-mail.
- Em produção, restrinja CORS em `backend/app/main.py` ao domínio do frontend.
- Revogue e regenere chaves expostas acidentalmente no histórico do Git antes de tornar o repositório público.

---

## Licença e entrega

Projeto acadêmico / hackathon. Após enviar o link do repositório à banca, trate o commit entregue como versão final de referência.
