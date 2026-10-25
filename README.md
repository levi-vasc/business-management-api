# Business Management API

API REST para **gestão de negócios** — cadastro de produtos, categorias e fornecedores, controle de estoque com histórico de movimentações e autenticação com perfis de acesso.

Construída com **FastAPI**, **SQLAlchemy 2** e **PostgreSQL**, com migrações via **Alembic** e autenticação por **JWT**.

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e execução](#instalação-e-execução)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Banco de dados e migrações](#banco-de-dados-e-migrações)
- [Autenticação e autorização](#autenticação-e-autorização)
- [Referência da API](#referência-da-api)
- [Regras de negócio](#regras-de-negócio)
- [Modelo de dados](#modelo-de-dados)
- [Tratamento de erros](#tratamento-de-erros)
- [Testes](#testes)
  
---

## Funcionalidades

- **Autenticação JWT** com login, perfil do usuário logado e registro de novos usuários.
- **Controle de acesso por papel** (`ADMIN` e `FUNCIONARIO`).
- **CRUD** de categorias, fornecedores e produtos.
- **Busca e filtros de produtos** por nome, código, categoria, fornecedor e estoque baixo.
- **Movimentações de estoque** (`ENTRADA` / `SAIDA`) que atualizam o saldo do produto na mesma transação, com bloqueio pessimista contra condições de corrida e proteção contra estoque negativo.
- **Listagem de movimentações** com filtros por período, produto, fornecedor e tipo, com paginação.
- **Relatório-resumo** de movimentações (somente `ADMIN`).
- **Respostas de erro padronizadas** em JSON, sem expor detalhes internos ao cliente.
- **Documentação interativa** Swagger.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Framework web | FastAPI |
| Servidor ASGI | Uvicorn |
| ORM | SQLAlchemy 2.x |
| Banco de dados | PostgreSQL |
| Migrações | Alembic |
| Validação | Pydantic v2 |
| Autenticação | PyJWT (HS256) + bcrypt |
| Configuração | python-dotenv |
| Testes | pytest |

Python **3.13** (versão usada no desenvolvimento).

## Estrutura do projeto

```
business-management-api/
├── app/
│   ├── main.py                # Criação do app, routers e handlers de exceção
│   ├── api/                   # Camada de rotas (controllers)
│   │   ├── auth.py            # /auth: registrar, login, me
│   │   ├── categorias.py      # /categorias
│   │   ├── fornecedores.py    # /fornecedores
│   │   ├── produtos.py        # /produtos
│   │   ├── mov_estoque.py     # /movimentacoes
│   │   └── deps.py            # Dependências: usuário atual e checagem de papel
│   ├── core/
│   │   ├── database.py        # Engine, SessionLocal, Base e get_db
│   │   ├── security.py        # Hash de senha (bcrypt) e JWT
│   │   └── exceptions.py      # Handlers globais e formato padrão de erro
│   ├── models/                # Modelos SQLAlchemy (tabelas)
│   └── schemas/               # Schemas Pydantic (entrada/saída)
├── alembic/                   # Migrações
│   ├── env.py
│   └── versions/
├── tests/                     # Testes automatizados (pytest)
├── alembic.ini
├── requirements.txt
├── .env.example
└── README.md
```

A organização segue camadas simples: **rotas** (`api`) → **schemas** de validação (`schemas`) → **modelos** de persistência (`models`), com infraestrutura compartilhada em `core`.

## Pré-requisitos

- Python 3.13 (ou compatível com as versões do `requirements.txt`)
- PostgreSQL em execução
- `pip` e `venv`

## Instalação e execução

### 1. Clonar e criar o ambiente virtual

```bash
git clone https://github.com/Levineith/business-management-api
cd business-management-api

python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
.\venv\Scripts\Activate.ps1
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Criar o banco de dados

```sql
CREATE DATABASE business_management;
```

### 4. Configurar o ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais (veja [Variáveis de ambiente](#variáveis-de-ambiente)).

### 5. Aplicar as migrações

```bash
alembic upgrade head
```

### 6. Iniciar a API

```bash
uvicorn app.main:app --reload
```

Acesse:

| Recurso | URL |
|---|---|
| Health check | http://localhost:8000/ |
| Swagger UI | http://localhost:8000/docs |

## Variáveis de ambiente

Exemplo de `.env`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/business_management
SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Gere uma chave segura com:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Banco de dados e migrações

O Alembic está configurado em `alembic/` e lê a `DATABASE_URL` de `app/core/database.py` (que por sua vez carrega o `.env`).

```bash
alembic upgrade head                              # aplica todas as migrações
alembic revision --autogenerate -m "descricao"    # gera nova migração a partir dos models
alembic downgrade -1                              # reverte a última migração
alembic current                                   # revisão atual
```

## Autenticação e autorização

A API usa **Bearer Token (JWT)**. O token carrega `sub` (ID do usuário), `email` e `role`, e expira conforme `ACCESS_TOKEN_EXPIRE_MINUTES`.

### Papéis

| Papel | Descrição |
|---|---|
| `ADMIN` | Acesso total, incluindo cadastro de usuários e relatório-resumo. |
| `FUNCIONARIO` | Operação do dia a dia. |

### Fluxo

1. **Primeiro usuário:** enquanto não existir nenhum usuário no banco, `POST /auth/registrar` é público. Cadastre o primeiro com `"role": "ADMIN"`.
2. **Demais usuários:** depois disso, apenas um `ADMIN` autenticado pode cadastrar novos usuários.
3. **Login:** `POST /auth/login` retorna o token.
4. **Uso:** Clique no botão `Authorize` e cole o token no campo.

Usuários com `ativo = false` são impedidos de autenticar (`403`).

## Referência da API

Legenda de acesso: 🌐 público · 🔒 requer login · 👑 somente `ADMIN`.

### Status

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| GET | `/` | 🌐 | Verifica se a API está online. |

### Autenticação — `/auth`

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/auth/registrar` | 🌐 no 1º usuário / 👑 depois | Cadastra um usuário. |
| POST | `/auth/login` | 🌐 | Autentica e retorna `access_token` + dados do usuário. |
| GET | `/auth/me` | 🔒 | Retorna o usuário autenticado. |

### Categorias — `/categorias`

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/categorias/` | 🔒 | Cria categoria (nome único). |
| GET | `/categorias/` | 🌐 | Lista categorias. |
| GET | `/categorias/{categoria_id}` | 🌐 | Busca por ID. |
| PUT | `/categorias/{categoria_id}` | 🔒 | Atualiza o nome. |
| DELETE | `/categorias/{categoria_id}` | 🔒 | Exclui (bloqueado se houver produtos vinculados). |

### Fornecedores — `/fornecedores`

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/fornecedores/` | 🔒 | Cria fornecedor (CNPJ e e-mail únicos). |
| GET | `/fornecedores/` | 🌐 | Lista fornecedores. |
| GET | `/fornecedores/{fornecedor_id}` | 🌐 | Busca por ID. |
| PUT | `/fornecedores/{fornecedor_id}` | 🔒 | Atualização parcial. |
| DELETE | `/fornecedores/{fornecedor_id}` | 🔒 | Exclui (bloqueado se houver produtos vinculados). |

### Produtos — `/produtos`

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/produtos/` | 🔒 | Cria produto (código único; categoria e fornecedor devem existir). |
| GET | `/produtos/` | 🌐 | Lista com filtros opcionais. |
| GET | `/produtos/{produto_id}` | 🌐 | Busca por ID. |
| PUT | `/produtos/{produto_id}` | 🔒 | Atualização parcial. |
| DELETE | `/produtos/{produto_id}` | 🔒 | Exclui (bloqueado se houver histórico de movimentações). |

**Filtros de `GET /produtos/`**

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `nome` | string | Busca parcial, sem diferenciar maiúsculas/minúsculas. |
| `codigo` | int | Código exato. |
| `categoria_id` | UUID | Filtra por categoria. |
| `fornecedor_id` | UUID | Filtra por fornecedor. |
| `apenas_estoque_baixo` | bool | Apenas produtos com `estoque <= estoque_min`. |

### Movimentações de estoque — `/movimentacoes`

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| POST | `/movimentacoes/` | 🔒 | Registra `ENTRADA` ou `SAIDA` e atualiza o estoque. |
| GET | `/movimentacoes/` | 🔒 | Lista movimentações (detalhadas) com filtros e paginação. |
| GET | `/movimentacoes/relatorio-resumo` | 👑 | Totais agregados do período. |
| GET | `/movimentacoes/{movimentacao_id}` | 🔒 | Busca por ID. |

**Filtros de `GET /movimentacoes/`**

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `data_inicio` | date | — | Início do período (inclusive). |
| `data_fim` | date | — | Fim do período (inclusive). |
| `fornecedor_id` | UUID | — | Fornecedor do produto. |
| `produto_id` | UUID | — | Produto. |
| `tipo` | string | — | `ENTRADA` ou `SAIDA`. |
| `skip` | int ≥ 0 | `0` | Registros a pular. |
| `limit` | int 1–500 | `100` | Máximo de registros. |

`GET /movimentacoes/relatorio-resumo` aceita `data_inicio`, `data_fim`, `fornecedor_id` e `produto_id`, e retorna:

```json
{
  "total_movimentacoes": 2,
  "total_entradas": 1,
  "total_saidas": 1,
  "quantidade_itens_entrada": 20,
  "quantidade_itens_saida": 8,
  "saldo_itens": 12
}
```

### Exemplos de payload

**Criar produto** — `POST /produtos/`

```json
{
  "nome": "Caneta Azul",
  "codigo": 1001,
  "preco_custo": 1.0,
  "preco_venda": 2.5,
  "categoria_id": "<uuid-da-categoria>",
  "fornecedor_id": "<uuid-do-fornecedor>",
  "estoque": 10,
  "estoque_min": 5
}
```

**Registrar movimentação** — `POST /movimentacoes/`

```json
{
  "produto_id": "<uuid-do-produto>",
  "tipo": "SAIDA",
  "qnt": 3
}
```

## Regras de negócio

- **Estoque nunca fica negativo:** uma `SAIDA` maior que o saldo é rejeitada com `400` informando o estoque disponível.
- **Atomicidade e concorrência:** a movimentação e a atualização do saldo ocorrem na mesma transação, com o produto bloqueado.
- **Tipo normalizado:** `tipo` é aceito em qualquer caixa e com espaços nas pontas (`" entrada "` → `ENTRADA`); só `ENTRADA` e `SAIDA` são válidos.
- **Quantidade positiva:** `qnt` deve ser maior que zero.
- **Data da movimentação** é definida pelo banco de dados (`now()`); não é informada pelo cliente.
- **Estoque baixo:** produto está em alerta quando `estoque <= estoque_min`.
- **Integridade referencial:** não é possível excluir categoria/fornecedor com produtos vinculados, nem produto com histórico de movimentações.
- **Unicidade:** nome de categoria; CNPJ e e-mail de fornecedor; código de produto; e-mail de usuário.
- **Primeiro usuário livre, demais restritos a `ADMIN`**.

## Modelo de dados

```
categorias (1) ───< produtos >─── (1) fornecedores
                       │
                       └───< movimentacoes_estoque

usuarios  (independente)
```

| Tabela | Campos principais |
|---|---|
| `usuarios` | `id` (UUID), `nome`, `email` (único), `senha_hash`, `role`, `ativo`, `data_cadastro` |
| `categorias` | `id` (UUID), `nome` (único, ≤100) |
| `fornecedores` | `id` (UUID), `nome`, `cnpj` (único, 14), `telefone` (11), `email` (único) |
| `produtos` | `id` (UUID), `nome`, `codigo` (int, único), `preco_custo`, `preco_venda`, `categoria_id` (FK), `fornecedor_id` (FK), `estoque`, `estoque_min`, `data_cadastro` |
| `movimentacoes_estoque` | `id` (UUID), `tipo` (`ENTRADA`/`SAIDA`), `qnt`, `data`, `produto_id` (FK) |

Todos os identificadores são **UUID v4**. CNPJ deve ter até 14 caracteres e telefone até 11 (sem máscara).

## Tratamento de erros

Todos os erros seguem o mesmo formato JSON:

```json
{
  "status_code": 400,
  "error": "Bad Request",
  "message": "Dados fornecidos na requisição são inválidos ou incompletos.",
  "path": "/produtos/",
  "timestamp": "2026-10-25T13:14:00+00:00",
  "detalhes": [
    { "campo": "preco_custo", "mensagem": "Field required" }
  ]
}
```

| Situação | Status |
|---|---|
| Erro de validação do payload (Pydantic) | `400` (com `detalhes` por campo) |
| Violação de integridade no banco (`IntegrityError`) | `400` |
| Regra de negócio violada | `400` |
| Token ausente, inválido ou expirado | `401` |
| Sem permissão / usuário inativo | `403` |
| Recurso não encontrado | `404` |
| Erro de banco ou exceção não tratada | `500` (mensagem genérica; o stack trace vai apenas para o log do servidor) |

> [!NOTE]
> Erros de validação retornam `400` (e não o `422` padrão do FastAPI).

## Testes

```bash
pytest
```

Os testes ficam em `tests/` e cobrem produtos, movimentações de estoque, consultas avançadas e tratamento de exceções.

> [!IMPORTANT]
>  **Os testes usam o banco apontado por `DATABASE_URL`** e executam `Base.metadata.create_all` / `drop_all` ao redor de cada teste. Isso **apaga as tabelas mapeadas** do banco configurado. **Nunca** execute `pytest` apontando para um banco com dados reais — use um banco exclusivo de testes, por exemplo:
>
> ```bash
> DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/business_management_test pytest
> ```
>
> Alguns testes que chamam rotas protegidas precisam enviar um token válido; se algum falhar com `401`, verifique os cabeçalhos nas fixtures.
