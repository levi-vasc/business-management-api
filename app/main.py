from fastapi import FastAPI
from app.core.database import Base, engine
import app.models
from app.api import categorias, fornecedores, produtos, mov_estoque, auth

from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="Business Management API",
    description="API para gerenciamento de negócios",
    version="0.1.0",
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(fornecedores.router)
app.include_router(produtos.router)
app.include_router(mov_estoque.router)

@app.get("/", tags=["Status"])
def read_root():
    return {"message": "API de Gestão de Negócios está online e operacional!"}
