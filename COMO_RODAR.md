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
| E-mail | `admin@prati.com.br` |
| Senha  | `123456` |
| Cargo  | `admin` (para acessar Relatórios) |

Se o login falhar, insira o usuário no Supabase (SQL Editor):

```sql
INSERT INTO usuarios (email, senha_hash, cargo)
VALUES ('admin@prati.com.br', '123456', 'admin');
```

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

## Variáveis obrigatórias para a plataforma rodar 100%

O arquivo `backend/.env` **não está no repositório** (por segurança). Você precisa criá-lo manualmente a partir do `backend/.env.example` e preencher os seguintes campos:

| Variável | O que é | Onde obter |
|----------|---------|------------|
| `SUPABASE_URL` | URL do projeto Supabase | Supabase → Project Settings → API |
| `SUPABASE_ANON_KEY` | Chave pública do Supabase | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Chave de serviço do Supabase | Supabase → Project Settings → API |
| `SECRET_KEY` | Chave para assinar os tokens JWT | Qualquer string longa e aleatória |
| `OPENAI_API_KEY` | Chave da OpenAI para o assistente IA | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

> **Sem essas variáveis o backend não inicia.** As variáveis de SMTP (`SMTP_HOST`, `SMTP_USER`, etc.) são opcionais — apenas necessárias para notificações por e-mail.

Exemplo de `backend/.env` mínimo:

```env
SECRET_KEY=qualquer-chave-secreta-forte
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

DASHBOARD_EMAIL=seu@email.com
DASHBOARD_PASSWORD=sua-senha

SUPABASE_URL=https://SEU_PROJECT.supabase.co
SUPABASE_ANON_KEY=sua-anon-key
SUPABASE_SERVICE_KEY=sua-service-role-key

OPENAI_API_KEY=sk-proj-...
```

---

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| Consulta real falha com erro de Playwright | Rode `python -m playwright install chromium` dentro de `backend/` (ou `npm run setup` na raiz) |
| Front não conecta na API | Confira `VITE_API_URL` em `frontend/.env` |
| Login recusado | Verifique Supabase, schema (`supabase_schema.sql`) e usuário/senha no `.env` |
| Assistente IA retorna erro | Verifique se `OPENAI_API_KEY` está preenchida e válida no `backend/.env` |
