import uuid
from sqlalchemy import Boolean, Column, Date, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="FUNCIONARIO")  # "ADMIN" ou "FUNCIONARIO"
    ativo = Column(Boolean, nullable=False, default=True)
    data_cadastro = Column(Date, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', role='{self.role}')>"
