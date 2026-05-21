# Como Rodar o Projeto

## Pré-requisitos

- **Python** 3.10 ou superior
- **Node.js** 18 ou superior (com npm)

---

## 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd hackathon-biopark
```

---

## 2. Backend (FastAPI)

### 2.1 Instalar dependências

```bash
cd backend
pip install -r requirements.txt
```

### 2.2 Configurar variáveis de ambiente

Peça o arquivo `.env` com as credenciais do projeto para um membro da equipe e coloque-o em `backend/.env`.

### 2.3 Subir o servidor

```bash
uvicorn app.main:app --reload
```

O backend estará disponível em:
- **API**: http://localhost:8000
- **Documentação interativa (Swagger)**: http://localhost:8000/docs

---

## 3. Frontend (React + Vite)

Abra um novo terminal:

### 3.1 Instalar dependências

```bash
cd frontend
npm install
```

### 3.2 Configurar variáveis de ambiente

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

### 3.3 Subir o servidor de desenvolvimento

```bash
npm run dev
```

O frontend estará disponível em: **http://localhost:5173**

---

## 4. Acessar o sistema

Abra o navegador em http://localhost:5173 e faça login com as credenciais configuradas no `.env` do backend:

| Campo | Valor padrão |
|-------|-------------|
| E-mail | admin@biopark.com.br |
| Senha | biopark2025 |

---

## 5. Importar dados iniciais (opcional)

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
