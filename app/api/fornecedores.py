import uuid
from app.api.deps import obter_usuario_atual
from app.models.usuario import Usuario
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.fornecedor import Fornecedor
from app.models.produto import Produto
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate, FornecedorResponse

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])


@router.post("/", response_model=FornecedorResponse, status_code=status.HTTP_201_CREATED)
def criar_fornecedor(dados: FornecedorCreate, usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    
    if db.query(Fornecedor).filter(Fornecedor.cnpj == dados.cnpj).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um fornecedor cadastrado com este CNPJ."
        )

    if db.query(Fornecedor).filter(Fornecedor.email == dados.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um fornecedor cadastrado com este e-mail."
        )

    novo_fornecedor = Fornecedor(**dados.model_dump())
    db.add(novo_fornecedor)
    db.commit()
    db.refresh(novo_fornecedor)
    return novo_fornecedor


@router.get("/", response_model=list[FornecedorResponse])
def listar_fornecedores(db: Session = Depends(get_db)):
    return db.query(Fornecedor).all()

@router.get("/{fornecedor_id}", response_model=FornecedorResponse)
def obter_fornecedor(fornecedor_id: uuid.UUID, db: Session = Depends(get_db)):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )
    return fornecedor


@router.put("/{fornecedor_id}", response_model=FornecedorResponse)
def atualizar_fornecedor(fornecedor_id: uuid.UUID, dados: FornecedorUpdate, usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )

    dados_atualizacao = dados.model_dump(exclude_unset=True)

    if "cnpj" in dados_atualizacao and dados_atualizacao["cnpj"] != fornecedor.cnpj:
        if db.query(Fornecedor).filter(Fornecedor.cnpj == dados_atualizacao["cnpj"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro fornecedor cadastrado com este CNPJ."
            )

    if "email" in dados_atualizacao and dados_atualizacao["email"] != fornecedor.email:
        if db.query(Fornecedor).filter(Fornecedor.email == dados_atualizacao["email"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outro fornecedor cadastrado com este e-mail."
            )

    for campo, valor in dados_atualizacao.items():
        setattr(fornecedor, campo, valor)

    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.delete("/{fornecedor_id}", status_code=status.HTTP_200_OK)
def excluir_fornecedor(fornecedor_id: uuid.UUID, usuario: Usuario = Depends(obter_usuario_atual), db: Session = Depends(get_db)):
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor não encontrado."
        )

    produtos_vinculados = db.query(Produto).filter(Produto.fornecedor_id == fornecedor_id).first()
    if produtos_vinculados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir este fornecedor pois existem produtos vinculados a ele."
        )

    db.delete(fornecedor)
    db.commit()
    return {"message": "Fornecedor excluído com sucesso."}
