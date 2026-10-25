import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import obter_usuario_atual, permitir_apenas
from app.models.mov_estoque import MovEstoque
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.schemas.mov_estoque import (
    MovEstoqueCreate,
    MovEstoqueResponse,
    MovEstoqueDetalhadaResponse,
    ResumoMovimentacoesResponse,
)

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações de Estoque"])


@router.post("/", response_model=MovEstoqueResponse, status_code=status.HTTP_201_CREATED)
def registrar_movimentacao(
    dados: MovEstoqueCreate,
    db: Session = Depends(get_db),
):
    """
    Registra uma movimentação e atualiza o estoque do produto na mesma transação.
    Se a saída for superior ao estoque atual, a operação é rejeitada para evitar estoque negativo.
    """
    tipo_normalizado = dados.tipo.upper().strip()
    if tipo_normalizado not in ["ENTRADA", "SAIDA"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de movimentação inválido. Deve ser 'ENTRADA' ou 'SAIDA'."
        )

    if dados.qnt <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A quantidade movimentada deve ser maior que zero."
        )

    # Bloqueio pessimista para evitar condições de corrida
    produto = (
        db.query(Produto)
        .filter(Produto.id == dados.produto_id)
        .with_for_update()
        .first()
    )
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto informado não foi encontrado."
        )

    if tipo_normalizado == "ENTRADA":
        produto.estoque += dados.qnt
    elif tipo_normalizado == "SAIDA":
        if produto.estoque < dados.qnt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estoque insuficiente para realizar esta saída. Estoque disponível: {produto.estoque}."
            )
        produto.estoque -= dados.qnt

    nova_movimentacao = MovEstoque(
        produto_id=dados.produto_id,
        tipo=tipo_normalizado,
        qnt=dados.qnt
    )

    db.add(nova_movimentacao)
    db.commit()
    db.refresh(nova_movimentacao)
    return nova_movimentacao


@router.get("/", response_model=list[MovEstoqueDetalhadaResponse])
def listar_movimentacoes(
    data_inicio: Optional[date] = Query(None, description="Data inicial do período (inclusive)"),
    data_fim: Optional[date] = Query(None, description="Data final do período (inclusive)"),
    fornecedor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por fornecedor do produto"),
    produto_id: Optional[uuid.UUID] = Query(None, description="Filtrar por produto"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: ENTRADA ou SAIDA"),
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=500, description="Limite máximo de registros"),
    db: Session = Depends(get_db),
):
    """
    Lista histórico de movimentações com informações completas do produto e fornecedor,
    permitindo filtros por período, fornecedor, produto e tipo.
    """
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data inicial não pode ser maior que a data final."
        )

    query = db.query(
        MovEstoque,
        Produto.nome.label("produto_nome"),
        Produto.fornecedor_id.label("fornecedor_id")
    ).join(Produto, MovEstoque.produto_id == Produto.id)

    if fornecedor_id:
        query = query.filter(Produto.fornecedor_id == fornecedor_id)

    if produto_id:
        query = query.filter(MovEstoque.produto_id == produto_id)

    if tipo:
        tipo_normalizado = tipo.upper().strip()
        if tipo_normalizado not in ["ENTRADA", "SAIDA"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de movimentação inválido. Deve ser 'ENTRADA' ou 'SAIDA'."
            )
        query = query.filter(MovEstoque.tipo == tipo_normalizado)

    if data_inicio:
        query = query.filter(MovEstoque.data >= data_inicio)

    if data_fim:
        query = query.filter(MovEstoque.data <= data_fim)

    resultados = query.order_by(MovEstoque.data.desc(), MovEstoque.id.desc()).offset(skip).limit(limit).all()

    return [
        MovEstoqueDetalhadaResponse(
            id=mov.id,
            produto_id=mov.produto_id,
            produto_nome=prod_nome,
            fornecedor_id=forn_id,
            tipo=mov.tipo,
            qnt=mov.qnt,
            data=mov.data,
        )
        for mov, prod_nome, forn_id in resultados
    ]


@router.get("/relatorio-resumo", response_model=ResumoMovimentacoesResponse)
def resumo_movimentacoes(
    data_inicio: Optional[date] = Query(None, description="Data inicial do período"),
    data_fim: Optional[date] = Query(None, description="Data final do período"),
    fornecedor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por fornecedor"),
    produto_id: Optional[uuid.UUID] = Query(None, description="Filtrar por produto"),
    admin: Usuario = Depends(permitir_apenas("ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Gera um resumo estratégico do fluxo de estoque no período:
    total de movimentações, entradas, saídas e saldo líquido de itens movimentados.
    Acesso restrito ao perfil ADMIN.
    """
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A data inicial não pode ser maior que a data final."
        )

    query = db.query(MovEstoque)
    if fornecedor_id:
        query = query.join(Produto, MovEstoque.produto_id == Produto.id).filter(
            Produto.fornecedor_id == fornecedor_id
        )
    if produto_id:
        query = query.filter(MovEstoque.produto_id == produto_id)
    if data_inicio:
        query = query.filter(MovEstoque.data >= data_inicio)
    if data_fim:
        query = query.filter(MovEstoque.data <= data_fim)

    movimentacoes = query.all()

    total_movimentacoes = len(movimentacoes)
    total_entradas = sum(1 for m in movimentacoes if m.tipo == "ENTRADA")
    total_saidas = sum(1 for m in movimentacoes if m.tipo == "SAIDA")
    qnt_entrada = sum(m.qnt for m in movimentacoes if m.tipo == "ENTRADA")
    qnt_saida = sum(m.qnt for m in movimentacoes if m.tipo == "SAIDA")

    return ResumoMovimentacoesResponse(
        total_movimentacoes=total_movimentacoes,
        total_entradas=total_entradas,
        total_saidas=total_saidas,
        quantidade_itens_entrada=qnt_entrada,
        quantidade_itens_saida=qnt_saida,
        saldo_itens=qnt_entrada - qnt_saida,
    )


@router.get("/{movimentacao_id}", response_model=MovEstoqueResponse)
def obter_movimentacao(
    movimentacao_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    movimentacao = db.query(MovEstoque).filter(MovEstoque.id == movimentacao_id).first()
    if not movimentacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimentação de estoque não encontrada."
        )
    return movimentacao