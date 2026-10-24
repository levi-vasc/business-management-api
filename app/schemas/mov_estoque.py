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
