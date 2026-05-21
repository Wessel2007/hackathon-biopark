# Biopark — Desafio 4: Consulta de Protocolos

## Stack
- **Backend**: Python + FastAPI → Railway
- **Banco de dados**: Supabase (PostgreSQL)
- **Frontend**: React + Vite + Tailwind → Vercel

## Estrutura
```
hackathon-biopark/
├── backend/
│   ├── app/
│   │   ├── main.py             # Entry point FastAPI
│   │   ├── config.py           # Variáveis de ambiente
│   │   ├── database.py         # Conexão Supabase/PostgreSQL
│   │   ├── models/             # Tabelas (Protocol, QueryHistory)
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── routers/            # Endpoints da API
│   │   └── services/           # Lógica: importer, scraper, report
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/              # Login, Dashboard, Protocols, Reports
│   │   ├── services/api.js     # Todas as chamadas à API
│   │   └── App.jsx
│   ├── vercel.json
│   └── .env.example
└── data/
    ├── mock_responses/         # HTMLs salvos para simular consultas
    └── initial_load/           # Coloque as planilhas aqui
```

## Rodar local (front + back)

Na raiz do repositório:

```bash
npm run dev
```

Instala dependências (Node + Python em `backend/.venv`) e sobe API e frontend juntos.

## Setup — Backend

```bash
cd backend
cp .env.example .env
# Preencha DATABASE_URL com a connection string do Supabase
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API sobe em http://localhost:8000
Documentação automática: http://localhost:8000/docs

## Setup — Frontend

```bash
cd frontend
cp .env.example .env
# Preencha VITE_API_URL com a URL do backend (Railway ou localhost)
npm install
npm run dev
```

## Deploy

### Backend → Railway
1. Crie um projeto no Railway e aponte para a pasta `/backend`
2. Configure as variáveis de ambiente do `.env.example`
3. O `Procfile` já está configurado

### Frontend → Vercel
1. Aponte o Vercel para a pasta `/frontend`
2. Configure `VITE_API_URL` com a URL do Railway
3. O `vercel.json` já trata o roteamento SPA

## Endpoints principais
| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /auth/login | Login com e-mail e senha |
| GET | /protocols/ | Listar protocolos (filtros: projeto, ativo, status) |
| POST | /protocols/ | Criar protocolo |
| PATCH | /protocols/{id} | Editar protocolo |
| DELETE | /protocols/{id} | Inativar ou excluir protocolo |
| POST | /import/spreadsheet | Importar planilha .xlsx |
| POST | /scraping/run-all | Consultar todos os protocolos ativos |
| POST | /scraping/run/{id} | Consultar um protocolo específico |
| GET | /reports/dashboard-data | Dados do dashboard |
| GET | /reports/pdf | Baixar relatório em PDF |

## Credenciais padrão do dashboard
Configure no `.env`:
```
DASHBOARD_EMAIL=admin@biopark.com.br
DASHBOARD_PASSWORD=biopark2025
```
