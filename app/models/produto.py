from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    codigo = Column(Integer, nullable=False, index=True, unique=True)
    preco_custo = Column(Float, nullable=False)
    preco_venda = Column(Float, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"), nullable=False)
    estoque = Column(Integer, nullable=False, default=0)
    # server_default = func.now() Pega a data pelo próprio banco de dados
    data_cadastro = Column(Date, nullable=False, server_default=func.now())
    estoque_min = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}', codigo={self.codigo})>"