"""
Middleware de autenticação JWT para Client Portal
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Configuração JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "30"))

security = HTTPBearer()


def create_access_token(client_id: str, expires_hours: Optional[int] = None) -> str:
    """
    Cria um access token JWT para o cliente
    """
    if expires_hours is None:
        expires_hours = JWT_EXPIRATION_HOURS

    expire = datetime.utcnow() + timedelta(hours=expires_hours)

    payload = {
        "sub": client_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(client_id: str) -> str:
    """
    Cria um refresh token JWT para o cliente
    """
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)

    payload = {
        "sub": client_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verifica e decodifica um token JWT
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}"
            )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def get_current_client(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency para obter o cliente autenticado atual
    """
    token = credentials.credentials
    payload = verify_token(token, "access")

    return {
        "id": payload.get("sub"),
        "token": token
    }


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency para rotas admin — valida token e confirma que o usuário é admin
    """
    token = credentials.credentials
    payload = verify_token(token, "access")

    if payload.get("sub") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao administrador"
        )

    return {"id": "admin", "token": token}


async def get_optional_client(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Dependency para obter o cliente autenticado (opcional)
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = verify_token(token, "access")
        return {
            "id": payload.get("sub"),
            "token": token
        }
    except HTTPException:
        return None
