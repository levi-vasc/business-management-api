import http
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("business_management_api")


class AppException(Exception):
    """Exceção base customizada para regras de negócio e erros controlados da aplicação."""
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "Ocorreu um erro ao processar sua requisição.",
        detalhes: Optional[Any] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.detalhes = detalhes
        super().__init__(message)


def _get_http_phrase(status_code: int) -> str:
    """Retorna o nome oficial do status HTTP ou fallback para 'Error'."""
    try:
        return http.HTTPStatus(status_code).phrase
    except ValueError:
        return "Error"


def _build_error_payload(
    status_code: int,
    message: str,
    path: str,
    detalhes: Optional[Any] = None,
) -> dict:
    """Gera o payload JSON padronizado para respostas de erro."""
    return {
        "status_code": status_code,
        "error": _get_http_phrase(status_code),
        "message": message,
        "path": path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detalhes": detalhes,
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Registra os manipuladores globais de exceção na aplicação FastAPI."""

    @app.middleware("http")
    async def global_catch_all_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(
                "Exceção não tratada capturada pelo middleware na rota %s [%s]: %s",
                request.url.path,
                request.method,
                exc,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=_build_error_payload(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Ocorreu um erro interno inesperado no servidor. Nossa equipe foi notificada.",
                    path=request.url.path,
                ),
            )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(
                status_code=exc.status_code,
                message=exc.message,
                path=request.url.path,
                detalhes=exc.detalhes,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(
                status_code=exc.status_code,
                message=message,
                path=request.url.path,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_payload(
                status_code=exc.status_code,
                message=message,
                path=request.url.path,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        detalhes = []
        for error in exc.errors():
            loc = [str(x) for x in error.get("loc", []) if x not in ("body", "query", "path")]
            campo = ".".join(loc) if loc else "payload"
            detalhes.append({
                "campo": campo,
                "mensagem": error.get("msg", "Valor inválido."),
            })

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_build_error_payload(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Dados fornecidos na requisição são inválidos ou incompletos.",
                path=request.url.path,
                detalhes=detalhes,
            ),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning("Violação de integridade no banco de dados na rota %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_build_error_payload(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Violação de integridade nos dados. Verifique se os registros relacionados existem ou se campos únicos já estão cadastrados.",
                path=request.url.path,
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        logger.error("Erro no banco de dados na rota %s: %s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_payload(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Ocorreu um erro inesperado ao se comunicar com a base de dados.",
                path=request.url.path,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # O stack trace completo é gravado nos logs internos do servidor para investigação
        logger.error(
            "Exceção não tratada capturada na rota %s [%s]: %s",
            request.url.path,
            request.method,
            exc,
            exc_info=True,
        )
        # O cliente (web/mobile) NUNCA recebe stack trace ou detalhes sensíveis internos
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_build_error_payload(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Ocorreu um erro interno inesperado no servidor. Nossa equipe foi notificada.",
                path=request.url.path,
            ),
        )
