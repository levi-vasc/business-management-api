import uuid
import pytest
from datetime import date, timedelta
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
def setup_data(db_session):
    from app.models.categoria import Categoria
    from app.models.fornecedor import Fornecedor
    from app.models.produto import Produto
    cat = Categoria(id=uuid.uuid4(), nome='Teste')
    forn = Fornecedor(
        id=uuid.uuid4(),
        nome='Fornecedor',
        cnpj='12345678000199',
        telefone='11999990000',
        email='contato@fornecedor.com'
    )
    db_session.add_all([cat, forn])
    db_session.commit()
    prod = Produto(
        id=uuid.uuid4(),
        nome='Mouse',
        codigo=200,
        preco_custo=30,
        preco_venda=60,
        categoria_id=cat.id,
        fornecedor_id=forn.id,
        estoque=5,
        estoque_min=3,
        data_cadastro=date.today()
    )
    db_session.add(prod)
    db_session.commit()
    return {'produto_id': prod.id, 'fornecedor_id': forn.id}

def test_registrar_entrada(setup_data):
    payload = {
        'produto_id': str(setup_data['produto_id']),
        'tipo': 'ENTRADA',
        'qnt': 10,
        'data': str(date.today())
    }
    response = client.post('/movimentacoes/', json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data['tipo'] == 'ENTRADA'
    assert data['qnt'] == 10

def test_registrar_saida_insuficiente(setup_data):
    payload = {
        'produto_id': str(setup_data['produto_id']),
        'tipo': 'SAIDA',
        'qnt': 100,
        'data': str(date.today())
    }
    response = client.post('/movimentacoes/', json=payload)
    assert response.status_code == 400
    assert 'Estoque insuficiente' in response.json()['detail']

def test_listar_movimentacoes_filtro_por_fornecedor(setup_data):
    client.post('/movimentacoes/', json={
        'produto_id': str(setup_data['produto_id']),
        'tipo': 'ENTRADA',
        'qnt': 5,
        'data': str(date.today())
    })
    resp = client.get('/movimentacoes/', params={'fornecedor_id': str(setup_data['fornecedor_id'])})
    assert resp.status_code == 200
    itens = resp.json()
    assert len(itens) >= 1

def test_resumo_movimentacoes(setup_data, admin_token):
    client.post('/movimentacoes/', json={
        'produto_id': str(setup_data['produto_id']),
        'tipo': 'ENTRADA',
        'qnt': 20,
        'data': str(date.today() - timedelta(days=10))
    })
    client.post('/movimentacoes/', json={
        'produto_id': str(setup_data['produto_id']),
        'tipo': 'SAIDA',
        'qnt': 8,
        'data': str(date.today() - timedelta(days=5))
    })
    headers = {'Authorization': f'Bearer {admin_token}'}
    resp = client.get('/movimentacoes/relatorio-resumo', headers=headers)
    assert resp.status_code == 200
    resumo = resp.json()
    assert resumo['total_movimentacoes'] == 2
    assert resumo['total_entradas'] == 1
    assert resumo['total_saidas'] == 1
    assert resumo['quantidade_itens_entrada'] == 20
    assert resumo['quantidade_itens_saida'] == 8
