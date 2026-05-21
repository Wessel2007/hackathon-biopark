from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt

from app.config import settings
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.supabase_client import SupabaseClient, get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, sb: SupabaseClient = Depends(get_supabase)):
    result = sb.table("usuarios").select("email, senha_hash, cargo").eq("email", body.email).maybe_single().execute()
    if not result.data or result.data["senha_hash"] != body.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    token = create_access_token({"sub": body.email, "cargo": result.data.get("cargo", "usuario")})
    return TokenResponse(access_token=token)


@router.post("/register", status_code=201)
def register(body: RegisterRequest, sb: SupabaseClient = Depends(get_supabase)):
    existing = sb.table("usuarios").select("id").eq("email", body.email).maybe_single().execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    sb.table("usuarios").insert({"email": body.email, "senha_hash": body.password}).execute()
    return {"message": "Usuário criado com sucesso"}
