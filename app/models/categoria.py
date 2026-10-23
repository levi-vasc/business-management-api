from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<Categoria(id={self.id}, nome='{self.nome}')>"
