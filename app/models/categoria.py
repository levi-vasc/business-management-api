from sqlalchemy import Column, String
from app.core.database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    nome = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Categoria(id={self.id}, nome='{self.nome}')>"
