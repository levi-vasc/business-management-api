from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid

class FornecedorBase(BaseModel):
    nome: str
    cnpj: str
    telefone: str
    email: str


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None


class FornecedorResponse(FornecedorBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
