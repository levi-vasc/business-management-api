import uuid
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail de acesso do usuário")
    role: Literal["ADMIN", "FUNCIONARIO"] = Field(
        default="FUNCIONARIO",
        description="Papel do usuário no sistema: 'ADMIN' ou 'FUNCIONARIO'"
    )


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, max_length=100, description="Senha em texto puro (mínimo 6 caracteres)")


class UsuarioResponse(UsuarioBase):
    id: uuid.UUID
    ativo: bool
    data_cadastro: date

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail cadastrado")
    senha: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
