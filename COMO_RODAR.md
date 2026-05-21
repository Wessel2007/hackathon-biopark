# Como Rodar o Projeto

## Pré-requisitos

- Python 3.10+
- Node.js 18+

---

## Tudo de uma vez (recomendado)

Na raiz do repositório:

```bash
npm run dev
```

Esse comando:
1. Instala dependências do Node (raiz + frontend) e do Python (`backend/.venv` + `requirements.txt`)
2. Cria `.env` a partir dos exemplos, se ainda não existirem
3. Sobe o backend (http://localhost:8000) e o frontend (http://localhost:5173) no mesmo terminal

---

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API disponível em http://localhost:8000 — documentação em http://localhost:8000/docs

---

## Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend disponível em http://localhost:5173

---

## Login

| Campo | Valor |
|-------|-------|
| E-mail | admin@biopark.com.br |
| Senha | biopark2025 |
