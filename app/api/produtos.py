import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.categoria import Categoria
from app.models.fornecedor import Fornecedor
from app.models.mov_estoque import MovEstoque
from app.models.produto import Produto
from app.api.deps import obter_usuario_atual, permitir_apenas
from app.models.usuario import Usuario
from app.schemas.produto import (
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse,
)

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
):
    
    if db.query(Produto).filter(Produto.codigo == dados.codigo).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um produto cadastrado com este código."
        )

    categoria = db.query(Categoria).filter(Categoria.id == dados.categoria_id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A categoria informada não existe."
        )

    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == dados.fornecedor_id).first()
    if not fornecedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O fornecedor informado não existe."
        )

    novo_produto = Produto(**dados.model_dump())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto


@router.get("/", response_model=list[ProdutoResponse])
def listar_produtos(
    nome: Optional[str] = Query(None, description="Filtrar por nome do produto (busca parcial insensível a maiúsculas)"),
    codigo: Optional[int] = Query(None, description="Filtrar por código exato do produto"),
    categoria_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID da categoria"),
    fornecedor_id: Optional[uuid.UUID] = Query(None, description="Filtrar por ID do fornecedor"),
    apenas_estoque_baixo: bool = Query(False, description="Exibir apenas produtos que atingiram ou estão abaixo do estoque mínimo"),
    db: Session = Depends(get_db),
):
    query = db.query(Produto)

    if nome:
        query = query.filter(Produto.nome.ilike(f"%{nome.strip()}%"))
    if codigo is not None:
        query = query.filter(Produto.codigo == codigo)
    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)
    if fornecedor_id:
        query = query.filter(Produto.fornecedor_id == fornecedor_id)
    if apenas_estoque_baixo:
        query = query.filter(Produto.estoque <= Produto.estoque_min)

    return query.all()


@router.get("/{produto_id}", response_model=ProdutoResponse)
def obter_produto(
    produto_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado."
        )
    return produto


@router.put("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(
    produto_id: uuid.UUID,
    dados: ProdutoUpdate,
    admin: Usuario = Depends(permitir_apenas("ADMIN")),
    db: Session = Depends(get_db),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado."
        )

    dados_atualizacao = dados.model_dump(exclude_unset=True)

    if "codigo" in dados_atualizacao and dados_atualizacao["codigo"] != produto.codigo:
        if db.query(Produto).filter(Produto.codigo == dados_atualizacao["codigo"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro produto cadastrado com este código."
            )

    if "categoria_id" in dados_atualizacao:
        categoria = db.query(Categoria).filter(Categoria.id == dados_atualizacao["categoria_id"]).first()
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A categoria informada não existe."
            )

    if "fornecedor_id" in dados_atualizacao:
        fornecedor = db.query(Fornecedor).filter(Fornecedor.id == dados_atualizacao["fornecedor_id"]).first()
        if not fornecedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O fornecedor informado não existe."
            )

    for campo, valor in dados_atualizacao.items():
        setattr(produto, campo, valor)

    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{produto_id}", status_code=status.HTTP_200_OK)
def excluir_produto(
    produto_id: uuid.UUID,
    admin: Usuario = Depends(permitir_apenas("ADMIN")),
    db: Session = Depends(get_db),
):
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado."
        )

    movimentacoes = db.query(MovEstoque).filter(MovEstoque.produto_id == produto_id).first()
    if movimentacoes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir este produto pois ele possui histórico de movimentações de estoque."
        )

    db.delete(produto)
    db.commit()
    return {"message": "Produto excluído com sucesso."}
