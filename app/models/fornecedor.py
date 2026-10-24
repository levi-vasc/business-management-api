from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(14), index=True, unique=True, nullable=False)
    telefone = Column(String(11), nullable=False)
    email = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Fornecedor(id={self.id}, nome='{self.nome}', cnpj='{self.cnpj}', email='{self.email}')>"