"""
Autenticação do Admin - Sistema Interno Smith 2.0
Suporta:
  - Admin principal via env vars (Pedro)
  - Usuários adicionais via tabela sm_usuarios (role: admin | marketing)
"""

import hmac
import bcrypt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.config import settings
from app.middleware.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_admin,
)
from app.database import get_supabase

router = APIRouter(prefix="/api/admin", tags=["Admin Auth"])


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(12)).decode()


# ── Modelos ────────────────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    email: str
    senha: str


class AdminLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    admin: dict


class AdminRefreshRequest(BaseModel):
    refresh_token: str


class CreateUserRequest(BaseModel):
    nome: str
    email: str
    senha: str
    role: str = "marketing"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_env_admin(email: str, senha: str) -> bool:
    """Verifica se as credenciais batem com o admin das env vars."""
    email_ok = hmac.compare_digest(email.strip().lower(), settings.admin_email.strip().lower())
    senha_ok = hmac.compare_digest(senha, settings.admin_password)
    return email_ok and senha_ok


def _buscar_usuario_db(email: str) -> Optional[dict]:
    """Busca usuário ativo em sm_usuarios pelo email."""
    try:
        supabase = get_supabase()
        res = supabase.table("sm_usuarios").select("*").eq("email", email.strip().lower()).eq("ativo", True).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        logger.error(f"Erro ao buscar usuário no DB: {e}")
    return None


def _build_tokens(sub: str, role: str, nome: str):
    extra = {"role": role, "nome": nome}
    access = create_access_token(sub, extra=extra)
    refresh = create_refresh_token(sub, extra=extra)
    return access, refresh


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest):
    """Login — verifica env admin primeiro, depois DB."""

    # 1. Admin via env
    if _is_env_admin(data.email, data.senha):
        access, refresh = _build_tokens("admin", "admin", settings.admin_nome)
        return AdminLoginResponse(
            access_token=access,
            refresh_token=refresh,
            admin={"id": "admin", "email": settings.admin_email, "nome": settings.admin_nome, "role": "admin"},
        )

    # 2. Usuário no banco
    usuario = _buscar_usuario_db(data.email)
    if usuario and _verify_password(data.senha, usuario["senha_hash"]):
        access, refresh = _build_tokens(usuario["id"], usuario["role"], usuario["nome"])
        return AdminLoginResponse(
            access_token=access,
            refresh_token=refresh,
            admin={
                "id": usuario["id"],
                "email": usuario["email"],
                "nome": usuario["nome"],
                "role": usuario["role"],
            },
        )

    raise HTTPException(status_code=401, detail="Email ou senha inválidos")


@router.post("/auth/refresh", response_model=AdminLoginResponse)
async def admin_refresh(data: AdminRefreshRequest):
    """Renova token preservando role e nome do payload anterior."""
    try:
        payload = verify_token(data.refresh_token, "refresh")

        sub = payload.get("sub")
        role = payload.get("role", "admin")
        nome = payload.get("nome", "")

        if not sub:
            raise HTTPException(status_code=401, detail="Token inválido")

        # Reconstruir info do admin
        if sub == "admin":
            email = settings.admin_email
            nome = settings.admin_nome
            role = "admin"
        else:
            # Buscar no DB para garantir que ainda está ativo
            try:
                supabase = get_supabase()
                res = supabase.table("sm_usuarios").select("id,email,nome,role,ativo").eq("id", sub).execute()
                if not res.data or not res.data[0]["ativo"]:
                    raise HTTPException(status_code=401, detail="Usuário inativo ou não encontrado")
                u = res.data[0]
                email = u["email"]
                nome = u["nome"]
                role = u["role"]
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erro ao validar refresh: {e}")
                raise HTTPException(status_code=401, detail="Token inválido")

        access, refresh = _build_tokens(sub, role, nome)
        return AdminLoginResponse(
            access_token=access,
            refresh_token=refresh,
            admin={"id": sub, "email": email, "nome": nome, "role": role},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no refresh do admin: {e}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.get("/auth/me")
async def admin_me(current=Depends(get_current_admin)):
    """Dados do usuário logado."""
    return {"id": current["id"], "role": current["role"]}


@router.post("/users")
async def criar_usuario(data: CreateUserRequest, _=Depends(get_current_admin)):
    """Cria novo usuário no sistema (admin only)."""
    if data.role not in ("admin", "marketing"):
        raise HTTPException(status_code=400, detail="Role inválido. Use 'admin' ou 'marketing'.")

    senha_hash = _hash_password(data.senha)

    try:
        supabase = get_supabase()
        res = supabase.table("sm_usuarios").insert({
            "nome": data.nome,
            "email": data.email.strip().lower(),
            "senha_hash": senha_hash,
            "role": data.role,
            "ativo": True,
        }).execute()

        usuario = res.data[0]
        logger.info(f"Usuário criado: {usuario['email']} role={usuario['role']}")
        return {"id": usuario["id"], "email": usuario["email"], "nome": usuario["nome"], "role": usuario["role"]}
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=409, detail="Email já cadastrado.")
        raise HTTPException(status_code=500, detail="Erro ao criar usuário.")
