"""
Autenticação do Admin - Sistema Interno Smith 2.0
Login único com credenciais do administrador via env
"""

import hmac

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.config import settings
from app.middleware.auth import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/api/admin", tags=["Admin Auth"])


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


@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLoginRequest):
    """Login do administrador"""
    email_match = hmac.compare_digest(data.email.strip().lower(), settings.admin_email.strip().lower())
    password_match = hmac.compare_digest(data.senha, settings.admin_password)

    if not email_match or not password_match:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    access_token = create_access_token("admin")
    refresh_token = create_refresh_token("admin")

    return AdminLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        admin={
            "id": "admin",
            "email": settings.admin_email,
            "nome": "Pedro Machado",
            "role": "admin",
        },
    )


@router.post("/auth/refresh", response_model=AdminLoginResponse)
async def admin_refresh(data: AdminRefreshRequest):
    """Renovar token do admin"""
    try:
        payload = verify_token(data.refresh_token, "refresh")

        if payload.get("sub") != "admin":
            raise HTTPException(status_code=401, detail="Token inválido")

        access_token = create_access_token("admin")
        refresh_token = create_refresh_token("admin")

        return AdminLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            admin={
                "id": "admin",
                "email": settings.admin_email,
                "nome": "Pedro Machado",
                "role": "admin",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no refresh do admin: {e}")
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.get("/auth/me")
async def admin_me():
    """Dados do admin logado"""
    return {
        "id": "admin",
        "email": settings.admin_email,
        "nome": "Pedro Machado",
        "role": "admin",
    }
