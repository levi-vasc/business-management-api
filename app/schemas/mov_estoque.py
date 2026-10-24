from datetime import date
from pydantic import BaseModel, ConfigDict
import uuid


class MovEstoqueCreate(BaseModel):
    produto_id: uuid.UUID
    tipo: str  # 'ENTRADA' ou 'SAIDA'
    qnt: int

class MovEstoqueResponse(BaseModel):
    id: uuid.UUID
    produto_id: uuid.UUID
    tipo: str
    qnt: int
    data: date

    model_config = ConfigDict(from_attributes=True)


class MovEstoqueDetalhadaResponse(BaseModel):
    id: uuid.UUID
    produto_id: uuid.UUID
    produto_nome: str
    fornecedor_id: uuid.UUID
    tipo: str
    qnt: int
    data: date

    model_config = ConfigDict(from_attributes=True)


class ResumoMovimentacoesResponse(BaseModel):
    total_movimentacoes: int
    total_entradas: int
    total_saidas: int
    quantidade_itens_entrada: int
    quantidade_itens_saida: int
    saldo_itens: int
