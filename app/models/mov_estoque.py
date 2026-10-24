from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid


class MovEstoque(Base):
    __tablename__ = "movimentacoes_estoque"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    tipo = Column(String(7), nullable=False)
    qnt = Column(Integer, nullable=False)
    # server_default=func.now() pega a data atual do banco de dados
    data = Column(Date, server_default=func.now())
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produtos.id"), nullable=False)

    def __repr__(self):
        return f"<MovEstoque(id={self.id}, tipo='{self.tipo}', qnt={self.qnt}, data={self.data}, produto_id={self.produto_id})>"