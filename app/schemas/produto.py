import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProdutoBase(BaseModel):
    nome: str
    codigo: int
    preco_custo: float
    preco_venda: float
    categoria_id: int
    fornecedor_id: int
    estoque: int = 0
    estoque_min: int = 1


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    codigo: Optional[int] = None
    preco_custo: Optional[float] = None
    preco_venda: Optional[float] = None
    categoria_id: Optional[int] = None
    fornecedor_id: Optional[int] = None
    estoque: Optional[int] = None
    estoque_min: Optional[int] = None


class ProdutoResponse(ProdutoBase):
    id: uuid.UUID
    data_cadastro: date

    model_config = ConfigDict(from_attributes=True)
