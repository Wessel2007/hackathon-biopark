# Como rodar o projeto

Guia rápido para avaliação local. Detalhes de arquitetura, órgãos consultados e deploy estão no [README.md](README.md).

---

## Pré-requisitos

- **Python** 3.10 ou superior  
- **Node.js** 18 ou superior  

---

## Opção recomendada (um comando)

Na **raiz** do repositório:

```bash
npm run dev
```

O script `scripts/setup.js`:

1. Instala dependências Node (raiz + `frontend/`) e Python (`backend/.venv` + `requirements.txt`)
2. Instala o Chromium do Playwright (necessário para consultas reais)
3. Cria `backend/.env` e `frontend/.env` a partir dos `.env.example`, se ainda não existirem
4. Sobe API (**http://localhost:8000**) e frontend (**http://localhost:5173**) no mesmo terminal

Documentação interativa da API: **http://localhost:8000/docs**

---

## Configuração manual (opcional)

### Backend

```bash
cd backend
cp .env.example .env
# Edite .env com URL e chaves do Supabase
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --reload
```

### Frontend (outro terminal)

```bash
cd frontend
cp .env.example .env
# VITE_API_URL=http://localhost:8000
npm install
npm run dev
```

---

## Login

Os usuários são cadastrados na tabela `usuarios` do Supabase. Credenciais para avaliação:

| Campo  | Valor |
|--------|-------|
| E-mail | `aquilaaws@gmail.com` |
| Senha  | `1` |

- **Dashboard** (`/`): acesso geral após login
- **Relatórios** (`/reports`): exige cargo `admin` + login em `/reports-login`

---

## Demo — consultas reais vs. simuladas

1. No Dashboard, execute a consulta de um protocolo de **Cartório**, **SANEPAR** ou **COPEL Distribuição** (acompanhamento).
2. Consulte um protocolo de **SEMA**, **Caixa** ou **COPEL genérico**.
3. No histórico, compare `fonte_consulta`: consultas reais não usam o prefixo `SIMULADO:`.

Tabela completa: [README.md — Consultas aos órgãos](README.md#consultas-aos-órgãos).

---

## Relatório PDF

Com o backend rodando e usuário autenticado, use **Baixar PDF** no Dashboard ou em Relatórios.

---

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| Consulta real falha com erro de Playwright | Rode `python -m playwright install chromium` dentro de `backend/` (ou `npm run setup` na raiz) |
| Front não conecta na API | Confira `VITE_API_URL` em `frontend/.env` |
| Login recusado | Verifique Supabase, schema (`supabase_schema.sql`) e usuário/senha no `.env` |
