# Como Rodar o Projeto

## Pré-requisitos

- Python 3.10+
- Node.js 18+

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
