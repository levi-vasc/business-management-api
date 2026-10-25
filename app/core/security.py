import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import bcrypt
import jwt
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("SECRET_KEY", "b38f89a9c2f689e47264871d6439bf1e837f482d96e5792d83ab9c72e104e76a")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def gerar_senha_hash(senha: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")

def verificar_senha(senha_pura: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha_pura.encode("utf-8"), senha_hash.encode("utf-8"))
    except Exception:
        return False

def criar_access_token(dados: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    payload = dados.copy()
    if expires_delta:
        expira_em = datetime.now(timezone.utc) + expires_delta
    else:
        expira_em = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({"exp": expira_em})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decodificar_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido",
        )
