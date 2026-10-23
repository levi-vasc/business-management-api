from fastapi import FastAPI
from app.core.database import Base, engine
import app.models

app = FastAPI(
    title="Business Management API",
    description="API para gerenciamento de negócios",
    version="0.1.0",
)

@app.get("/")
def read_root():
    return {"message": "API de Gestão de Negócios"}
