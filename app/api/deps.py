import uuid
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decodificar_token
from app.models.usuario import Usuario

# Utiliza HTTPBearer para captura limpa do header 'Authorization: Bearer <token>'
security = HTTPBearer(auto_error=False)


def obter_usuario_atual(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Dependência que valida o token JWT e retorna a instância do usuário autenticado.
    Retorna 401 caso o token não seja informado, esteja expirado ou seja inválido.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso não informado. É necessário enviar o cabeçalho 'Authorization: Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decodificar_token(token)
        usuario_id_str = payload.get("sub")
        if not usuario_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: identificador de usuário não encontrado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        usuario_id = uuid.UUID(usuario_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso expirado. Por favor, realize um novo login.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso inválido ou malformado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário associado a este token não foi encontrado no sistema.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuário está inativo no sistema. Contate o administrador.",
        )

    return usuario


def permitir_apenas(*roles_permitidas: str):
    """
    Fábrica de dependências para RBAC (Role-Based Access Control).
    Permite o acesso apenas se a função (role) do usuário estiver na lista de papéis autorizados.
    Caso contrário, retorna 403 Forbidden.
    """
    def verificador_permissao(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
        if usuario.role not in roles_permitidas:
            roles_formatadas = ", ".join(roles_permitidas)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado: a função '{usuario.role}' não possui permissão para executar esta ação. Papel requerido: {roles_formatadas}.",
            )
        return usuario

    return verificador_permissao
