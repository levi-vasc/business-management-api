from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class MovEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tipo = Column(String(7), nullable=False)
    qnt = Column(Integer, nullable=False)
    # server_default=func.now() pega a data atual do banco de dados
    data = Column(Date, server_default=func.now())
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)

    def __repr__(self):
        return f"<MovEstoque(id={self.id}, tipo='{self.tipo}', qnt={self.qnt}, data={self.data}, produto_id={self.produto_id})>"