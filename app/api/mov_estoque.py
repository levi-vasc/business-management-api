from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.mov_estoque import MovEstoque
from app.models.produto import Produto
from app.schemas.mov_estoque import MovEstoqueCreate, MovEstoqueResponse

router = APIRouter(prefix="/movimentacoes", tags=["Movimentações de Estoque"])


@router.post("/", response_model=MovEstoqueResponse, status_code=status.HTTP_201_CREATED)
def registrar_movimentacao(dados: MovEstoqueCreate, db: Session = Depends(get_db)):
    
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

    produto = db.query(Produto).filter(Produto.id == dados.produto_id).first()
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


@router.get("/", response_model=list[MovEstoqueResponse])
def listar_movimentacoes(db: Session = Depends(get_db)):
    return db.query(MovEstoque).all()


@router.get("/{movimentacao_id}", response_model=MovEstoqueResponse)
def obter_movimentacao(movimentacao_id: int, db: Session = Depends(get_db)):
    movimentacao = db.query(MovEstoque).filter(MovEstoque.id == movimentacao_id).first()
    if not movimentacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movimentação de estoque não encontrada."
        )
    return movimentacao