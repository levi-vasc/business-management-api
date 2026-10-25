from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import obter_usuario_atual, security
from app.core.database import get_db
from app.core.security import criar_access_token, gerar_senha_hash, verificar_senha
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse, UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/registrar", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    total_usuarios = db.query(Usuario).count()

    if total_usuarios > 0:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Apenas administradores podem cadastrar novos usuários. Token de acesso não informado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        solicitante = obter_usuario_atual(credentials=credentials, db=db)
        if solicitante.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: apenas usuários com o papel 'ADMIN' podem cadastrar novos usuários.",
            )

    usuario_existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com este e-mail."
        )

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_senha_hash(dados.senha),
        role=dados.role,
        ativo=True,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@router.post("/login", response_model=TokenResponse)
def login(
    dados: LoginRequest,
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Contate o administrador do sistema.",
        )

    token = criar_access_token(
        dados={
            "sub": str(usuario.id),
            "email": usuario.email,
            "role": usuario.role,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        usuario=usuario,
    )

@router.get("/me", response_model=UsuarioResponse)
def obter_perfil_atual(
    usuario: Usuario = Depends(obter_usuario_atual),
):
    return usuario
