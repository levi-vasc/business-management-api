from pydantic import BaseModel, ConfigDict
import uuid


class CategoriaBase(BaseModel):
    nome: str


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
