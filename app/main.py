from fastapi import FastAPI
from app.core.database import Base, engine
import app.models  # noqa: F401

# Cria as tabelas no banco de dados automaticamente se necessário
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Business Management API",
    description="API para gerenciamento de negócios",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "API de Gestão de Negócios online!"}
