# Como Rodar o Projeto

## Pré-requisitos

- **Python** 3.10 ou superior
- **Node.js** 18 ou superior (com npm)
- Uma conta no **Supabase** (banco de dados PostgreSQL gratuito)

---

## 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd hackathon-biopark
```

---

## 2. Configurar o Supabase

1. Acesse [supabase.com](https://supabase.com) e crie um projeto.
2. Vá em **Settings → Database** e copie a **Connection String** (URI).
3. Vá em **Settings → API** e copie a **Project URL** e a **anon key**.

Você vai precisar dessas informações nos passos seguintes.

---

## 3. Backend (FastAPI)

### 3.1 Instalar dependências

```bash
cd backend
pip install -r requirements.txt
```

### 3.2 Configurar variáveis de ambiente

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

Abra o arquivo `.env` e preencha os campos:

```env
# Cole a connection string do Supabase (Settings → Database → URI)
DATABASE_URL=postgresql://postgres:[SENHA]@db.[PROJECT_REF].supabase.co:5432/postgres

# Qualquer string aleatória longa e segura
SECRET_KEY=troque-por-uma-chave-secreta-forte-aqui

ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Credenciais de acesso ao dashboard
DASHBOARD_EMAIL=admin@biopark.com.br
DASHBOARD_PASSWORD=biopark2025

# Dados do Supabase (Settings → API)
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_ANON_KEY=sua-anon-key-aqui
```

### 3.3 Subir o servidor

```bash
uvicorn app.main:app --reload
```

O backend estará disponível em:
- **API**: http://localhost:8000
- **Documentação interativa (Swagger)**: http://localhost:8000/docs

---

## 4. Frontend (React + Vite)

Abra um novo terminal:

### 4.1 Instalar dependências

```bash
cd frontend
npm install
```

### 4.2 Configurar variáveis de ambiente

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/macOS
cp .env.example .env
```

Abra o arquivo `.env` e aponte para o backend local:

```env
VITE_API_URL=http://localhost:8000
```

### 4.3 Subir o servidor de desenvolvimento

```bash
npm run dev
```

O frontend estará disponível em: **http://localhost:5173**

---

## 5. Acessar o sistema

Abra o navegador em http://localhost:5173 e faça login com as credenciais configuradas no `.env` do backend:

| Campo | Valor padrão |
|-------|-------------|
| E-mail | admin@biopark.com.br |
| Senha | biopark2025 |

---

## 6. Importar dados iniciais (opcional)

Para carregar os protocolos da planilha inicial:

1. Coloque o arquivo `.xlsx` na pasta `data/initial_load/`
2. No Swagger (http://localhost:8000/docs), use o endpoint `POST /import/spreadsheet`
3. Selecione o arquivo e envie

---

## Resumo dos comandos

| Terminal | Comando | O que faz |
|----------|---------|-----------|
| 1 | `cd backend && uvicorn app.main:app --reload` | Sobe a API na porta 8000 |
| 2 | `cd frontend && npm run dev` | Sobe o frontend na porta 5173 |

---

## Deploy em produção

| Serviço | Plataforma | Configuração |
|---------|-----------|-------------|
| Backend | Railway | Aponte para `/backend`; configure as vars do `.env` |
| Frontend | Vercel | Aponte para `/frontend`; defina `VITE_API_URL` com a URL do Railway |

O `Procfile` (backend) e o `vercel.json` (frontend) já estão configurados para produção.
