from sqlalchemy import Column, Integer, String
from sqlalchemy.sql import func
from app.core.database import Base


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(14), index=True, unique=True, nullable=False)
    telefone = Column(String(11), nullable=False)
    email = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Fornecedor(id={self.id}, nome='{self.nome}', cnpj='{self.cnpj}', email='{self.email}')>"