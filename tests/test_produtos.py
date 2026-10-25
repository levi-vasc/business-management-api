import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker

client = TestClient(app)

@pytest.fixture(scope='function')
def db_session():
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def categoria_id(db_session):
    from app.models.categoria import Categoria
    cat = Categoria(id=uuid.uuid4(), nome='Teste')
    db_session.add(cat)
    db_session.commit()
    return cat.id

@pytest.fixture
def fornecedor_id(db_session):
    from app.models.fornecedor import Fornecedor
    forn = Fornecedor(
        id=uuid.uuid4(),
        nome='Fornecedor Teste',
        cnpj='12345678000199',
        telefone='11999990000',
        email='contato@fornecedor.com'
    )
    db_session.add(forn)
    db_session.commit()
    return forn.id

def test_criar_produto(categoria_id, fornecedor_id):
    payload = {
        'nome': 'Caneta',
        'codigo': 999,
        'preco_custo': 1.0,
        'preco_venda': 2.5,
        'categoria_id': str(categoria_id),
        'fornecedor_id': str(fornecedor_id),
        'estoque': 10,
        'estoque_min': 5,
        'data_cadastro': '2026-01-01'
    }
    response = client.post('/produtos/', json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data['nome'] == 'Caneta'
    assert data['codigo'] == 999

def test_listar_produtos_filtro_estoque_baixo(categoria_id, fornecedor_id):
    from app.models.produto import Produto
    db = next(get_db())
    prod1 = Produto(
        id=uuid.uuid4(),
        nome='Produto Normal',
        codigo=101,
        preco_custo=10,
        preco_venda=20,
        categoria_id=categoria_id,
        fornecedor_id=fornecedor_id,
        estoque=20,
        estoque_min=5,
        data_cadastro='2026-01-10'
    )
    prod2 = Produto(
        id=uuid.uuid4(),
        nome='Produto Baixo',
        codigo=102,
        preco_custo=5,
        preco_venda=12,
        categoria_id=categoria_id,
        fornecedor_id=fornecedor_id,
        estoque=2,
        estoque_min=5,
        data_cadastro='2026-01-11'
    )
    db.add_all([prod1, prod2])
    db.commit()
    response = client.get('/produtos/', params={'apenas_estoque_baixo': True})
    assert response.status_code == 200
    itens = response.json()
    assert any(i['nome'] == 'Produto Baixo' for i in itens)
    assert not any(i['nome'] == 'Produto Normal' for i in itens)
