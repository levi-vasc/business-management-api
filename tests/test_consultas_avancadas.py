import unittest
import uuid
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.produto import Produto
from app.models.mov_estoque import MovEstoque
from app.api.produtos import listar_produtos
from app.api.mov_estoque import (
    listar_movimentacoes,
    resumo_movimentacoes,
)


class TestConsultasAvancadas(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

        # Popular dados base: Categoria e Fornecedores
        self.cat1 = Categoria(id=uuid.uuid4(), nome="Informática")
        self.cat2 = Categoria(id=uuid.uuid4(), nome="Escritório")
        self.db.add_all([self.cat1, self.cat2])

        self.forn_dell = Fornecedor(
            id=uuid.uuid4(),
            nome="Dell Computadores",
            cnpj="12345678000101",
            telefone="11999990001",
            email="contato@dell.com"
        )
        self.forn_logitech = Fornecedor(
            id=uuid.uuid4(),
            nome="Logitech Brasil",
            cnpj="98765432000199",
            telefone="11999990002",
            email="vendas@logitech.com"
        )
        self.db.add_all([self.forn_dell, self.forn_logitech])
        self.db.commit()

        # Produtos
        # 1. Teclado Mecânico: estoque 2, estoque_min 5 -> ESTOQUE BAIXO (deficit 3), Fornecedor: Logitech
        self.prod_teclado = Produto(
            id=uuid.uuid4(),
            nome="Teclado Mecânico RGB",
            codigo=101,
            preco_custo=150.0,
            preco_venda=250.0,
            categoria_id=self.cat1.id,
            fornecedor_id=self.forn_logitech.id,
            estoque=2,
            estoque_min=5,
            data_cadastro=date(2026, 1, 10),
        )
        # 2. Mouse Gamer: estoque 0, estoque_min 10 -> RUPTURA TOTAL (deficit 10), Fornecedor: Logitech
        self.prod_mouse = Produto(
            id=uuid.uuid4(),
            nome="Mouse Gamer Pro",
            codigo=102,
            preco_custo=80.0,
            preco_venda=160.0,
            categoria_id=self.cat1.id,
            fornecedor_id=self.forn_logitech.id,
            estoque=0,
            estoque_min=10,
            data_cadastro=date(2026, 1, 15),
        )
        # 3. Monitor UltraWide: estoque 15, estoque_min 3 -> NORMAL, Fornecedor: Dell
        self.prod_monitor = Produto(
            id=uuid.uuid4(),
            nome="Monitor UltraWide 29",
            codigo=201,
            preco_custo=900.0,
            preco_venda=1400.0,
            categoria_id=self.cat1.id,
            fornecedor_id=self.forn_dell.id,
            estoque=15,
            estoque_min=3,
            data_cadastro=date(2026, 2, 1),
        )
        self.db.add_all([self.prod_teclado, self.prod_mouse, self.prod_monitor])
        self.db.commit()

        # Movimentações de Estoque
        hoje = date(2026, 10, 24)
        ontem = hoje - timedelta(days=1)
        semana_passada = hoje - timedelta(days=7)
        mes_passado = hoje - timedelta(days=30)

        # Monitor (Dell)
        self.mov1 = MovEstoque(
            id=uuid.uuid4(),
            produto_id=self.prod_monitor.id,
            tipo="ENTRADA",
            qnt=20,
            data=mes_passado,
        )
        self.mov2 = MovEstoque(
            id=uuid.uuid4(),
            produto_id=self.prod_monitor.id,
            tipo="SAIDA",
            qnt=5,
            data=semana_passada,
        )
        # Teclado (Logitech)
        self.mov3 = MovEstoque(
            id=uuid.uuid4(),
            produto_id=self.prod_teclado.id,
            tipo="ENTRADA",
            qnt=10,
            data=ontem,
        )
        self.mov4 = MovEstoque(
            id=uuid.uuid4(),
            produto_id=self.prod_teclado.id,
            tipo="SAIDA",
            qnt=8,
            data=hoje,
        )
        self.db.add_all([self.mov1, self.mov2, self.mov3, self.mov4])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_consulta_produtos_apenas_estoque_baixo(self):
        """Testa o filtro apenas_estoque_baixo na listagem de produtos"""
        prods_baixo = listar_produtos(
            nome=None,
            codigo=None,
            categoria_id=None,
            fornecedor_id=None,
            apenas_estoque_baixo=True,
            db=self.db,
        )
        # Teclado (2 <= 5) e Mouse (0 <= 10) devem vir, Monitor (15 > 3) NÃO deve vir
        self.assertEqual(len(prods_baixo), 2)
        nomes = [p.nome for p in prods_baixo]
        self.assertIn("Mouse Gamer Pro", nomes)
        self.assertIn("Teclado Mecânico RGB", nomes)

    def test_consulta_produtos_estoque_baixo_por_fornecedor(self):
        """Testa filtrar estoque baixo combinando com fornecedor específico"""
        prods_dell = listar_produtos(
            nome=None,
            codigo=None,
            categoria_id=None,
            fornecedor_id=self.forn_dell.id,
            apenas_estoque_baixo=True,
            db=self.db,
        )
        self.assertEqual(len(prods_dell), 0)

        prods_logitech = listar_produtos(
            nome=None,
            codigo=None,
            categoria_id=None,
            fornecedor_id=self.forn_logitech.id,
            apenas_estoque_baixo=True,
            db=self.db,
        )
        self.assertEqual(len(prods_logitech), 2)

    def test_filtros_gerais_produtos(self):
        """Testa busca textual por nome, categoria e flag de estoque baixo na listagem geral"""
        # Busca por nome case-insensitive
        prods = listar_produtos(
            nome="tEcLaDo",
            codigo=None,
            categoria_id=None,
            fornecedor_id=None,
            apenas_estoque_baixo=False,
            db=self.db,
        )
        self.assertEqual(len(prods), 1)
        self.assertEqual(prods[0].nome, "Teclado Mecânico RGB")

        # Filtro por fornecedor
        prods_dell = listar_produtos(
            nome=None,
            codigo=None,
            categoria_id=None,
            fornecedor_id=self.forn_dell.id,
            apenas_estoque_baixo=False,
            db=self.db,
        )
        self.assertEqual(len(prods_dell), 1)
        self.assertEqual(prods_dell[0].nome, "Monitor UltraWide 29")

    def test_movimentacoes_filtro_por_fornecedor(self):
        """Testa filtragem de movimentações pelo fornecedor através do JOIN com Produto"""
        # Movimentações dos produtos da Dell
        movs_dell = listar_movimentacoes(
            data_inicio=None,
            data_fim=None,
            fornecedor_id=self.forn_dell.id,
            produto_id=None,
            tipo=None,
            db=self.db,
        )
        self.assertEqual(len(movs_dell), 2)
        for m in movs_dell:
            self.assertEqual(m.produto_id, self.prod_monitor.id)
            self.assertEqual(m.produto_nome, "Monitor UltraWide 29")
            self.assertEqual(m.fornecedor_id, self.forn_dell.id)

        # Movimentações dos produtos da Logitech
        movs_logitech = listar_movimentacoes(
            data_inicio=None,
            data_fim=None,
            fornecedor_id=self.forn_logitech.id,
            produto_id=None,
            tipo=None,
            db=self.db,
        )
        self.assertEqual(len(movs_logitech), 2)
        for m in movs_logitech:
            self.assertEqual(m.produto_id, self.prod_teclado.id)
            self.assertEqual(m.produto_nome, "Teclado Mecânico RGB")
            self.assertEqual(m.fornecedor_id, self.forn_logitech.id)

    def test_movimentacoes_filtro_por_periodo(self):
        """Testa histórico por período de datas"""
        hoje = date(2026, 10, 24)
        ontem = hoje - timedelta(days=1)

        # Apenas ontem e hoje
        movs_recentes = listar_movimentacoes(
            data_inicio=ontem,
            data_fim=hoje,
            fornecedor_id=None,
            produto_id=None,
            tipo=None,
            db=self.db,
        )
        self.assertEqual(len(movs_recentes), 2)

    def test_resumo_movimentacoes(self):
        """Testa geração de relatório resumo estratégico"""
        resumo = resumo_movimentacoes(
            data_inicio=None,
            data_fim=None,
            fornecedor_id=None,
            produto_id=None,
            db=self.db,
        )
        self.assertEqual(resumo.total_movimentacoes, 4)
        self.assertEqual(resumo.total_entradas, 2)
        self.assertEqual(resumo.total_saidas, 2)
        self.assertEqual(resumo.quantidade_itens_entrada, 30)  # 20 monitor + 10 teclado
        self.assertEqual(resumo.quantidade_itens_saida, 13)    # 5 monitor + 8 teclado
        self.assertEqual(resumo.saldo_itens, 17)               # 30 - 13


if __name__ == "__main__":
    unittest.main()
