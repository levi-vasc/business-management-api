from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class ErroDetalhe(BaseModel):
    campo: str = Field(..., description="Nome do campo que originou o erro")
    mensagem: str = Field(..., description="Mensagem de erro amigável")


class ErrorResponse(BaseModel):
    status_code: int = Field(..., description="Código de status HTTP da resposta", example=400)
    error: str = Field(..., description="Descrição padronizada do erro HTTP", example="Bad Request")
    message: str = Field(..., description="Mensagem explicativa compreensível do problema", example="Dados inválidos.")
    path: str = Field(..., description="Caminho do endpoint da requisição", example="/produtos")
    timestamp: datetime = Field(..., description="Data e hora em UTC em que o erro ocorreu")
    detalhes: Optional[Any] = Field(None, description="Detalhes adicionais ou lista de campos com erro")
