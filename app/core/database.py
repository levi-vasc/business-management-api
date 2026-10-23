import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Carrega as variáveis de ambiente definidas no arquivo .env
load_dotenv()

# Obtém a string de conexão do banco do arquivo .env
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/business_management"
)

# Caso a URL comece com postgresql:// simples, ajustamos para postgresql+psycopg2://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Cria a engine de conexão com o banco de dados
engine = create_engine(DATABASE_URL)

# Cria a fábrica de sessões para executar operações no banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Classe base para os modelos SQLAlchemy
Base = declarative_base()


# Função utilitária para obter a sessão do banco (Dependency Injection no FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
