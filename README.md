# 🌱 Empório Natural — API de Produtos

API REST desenvolvida em **Flask** que serve como backend para a loja virtual do **Empório Natural** — projeto de e-commerce de produtos naturais (frutas, granel, suplementos, etc.) construído em React no mini projeto `mini_projects` do curso de React (`react_course`, pasta de documentos). Esta API é responsável pelo catálogo de produtos, autenticação de usuários e gerenciamento do carrinho de compras.

---

## 📋 Visão Geral

O projeto expõe endpoints para:

- **Catálogo de produtos** — listagem e busca por ID, com dados como nome, descrição, imagem, categorias, preço e unidade de venda (kg/un).
- **Autenticação de usuários** — cadastro e login com senha criptografada (`werkzeug.security`), utilizando **JWT** com *access token* (1h) e *refresh token* (7 dias) armazenados em **cookies httpOnly** (`SameSite=None`, `Secure`), com suporte também ao header `Authorization`.
- **Carrinho de compras** — cada usuário possui um carrinho persistido no banco (coluna JSON), com operações de adicionar, remover e limpar itens.
- **Revogação de tokens** — no logout, os tokens são adicionados a uma **blacklist no Redis**, impedindo reuso até a expiração.

### Stack

| Camada | Tecnologia |
|---|---|
| Framework | Flask 3 |
| ORM | SQLAlchemy 2.0 (Flask-SQLAlchemy) |
| Banco de dados | PostgreSQL (produção) / SQLite (padrão local) |
| Cache / Blacklist | Redis |
| Autenticação | PyJWT (HS256) + cookies httpOnly |
| Deploy | Gunicorn |

---

## ✨ Features

- ✅ CRUD de carrinho por usuário (`GET`, `POST`, `DELETE`) com proteção de rotas via decorator
- ✅ Cadastro e login com **hash de senha** e validação de nomes repetidos
- ✅ **Access token + Refresh token** com renovação na rota `/refresh` (rotação do refresh token)
- ✅ **Logout seguro**: tokens revogados via Redis com TTL igual à validade restante de cada token
- ✅ Cookies `httpOnly` + flag `is_logged` (não httpOnly) para o frontend saber o estado da sessão
- ✅ **CORS** configurado com `supports_credentials` para as origens do frontend (Vite dev `:5173`, preview `:4173` e `CLIENT_SITE`)
- ✅ Pool de conexões com `pool_pre_ping` e `pool_recycle` (evita erro de conexão SSL encerrada no PostgreSQL)
- ✅ Seed de **29 produtos** do empório (frutas, castanhas, sementes, whey, mel, chás etc.)
- ✅ Suporte a `postgres://` e `postgresql://` na `DATABASE_URL`
- ✅ Modo desenvolvimento (`DEV=true`) com debug e host `localhost`

---

## 🛠️ Requisitos

- **Python 3.10+**
- **Redis** em execução (localhost:6379 ou URL remota)
- **PostgreSQL** (opcional — sem `DATABASE_URL`, usa SQLite `users.db`)
- Dependências Python:

```bash
pip install -r requirements.txt
```

### Variáveis de ambiente

Copie o `.env.example` para `.env` e preencha:

| Variável | Descrição | Exemplo |
|---|---|---|
| `JWT_SECRET_KEY_APP` | Chave secreta para assinar os JWTs | `uma-chave-forte-e-aleatoria` |
| `DATABASE_URL` | URL de conexão do banco (opcional) | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Host ou URL do Redis | `localhost` ou `redis://...` |
| `REDIS_PORT` | Porta do Redis | `6379` |
| `PORT` | Porta da API | `5000` |
| `DEV` | Modo desenvolvimento (`true`/`false`) | `true` |
| `CLIENT_SITE` | Origem do frontend em produção | `https://meudominio.com` |

> ⚠️ **Importante:** sem `JWT_SECRET_KEY_APP` definida, a API usa uma chave padrão insegura. Defina sempre em produção.

---

## 🚀 Como executar

```bash
# 1. Crie o ambiente virtual e instale as dependências
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure o .env (ver tabela acima)

# 3. Crie as tabelas do banco
python database_creator.py

# 4. Popule o catálogo com os produtos do empório
python products.py

# 5. Rode a API
python app.py
```

A API estará disponível em `http://localhost:5000`.

### Produção

Com `DEV=false`, o servidor escuta em `0.0.0.0` e os cookies `secure` são reforçados. Para servir com Gunicorn:

```bash
gunicorn app:app
```

---

## 📡 Endpoints

### Produtos (públicos)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` ou `/products` | Lista até 50 produtos do catálogo |
| `GET` | `/products/<id>` | Detalhes de um produto (404 se não existir) |

### Usuários

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/users/createnewuser` | Cadastro — body: `{ "user", "password" }` — já autentica e seta os cookies |
| `POST` | `/users/login` | Login — body: `{ "username", "password" }` |
| `GET` | `/users/me` 🔒 | Dados do usuário logado (nome e carrinho) |
| `DELETE` | `/users/logout` 🔒 | Revoga access e refresh tokens (blacklist no Redis) |

### Carrinho 🔒

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/users/cart` | Retorna o carrinho do usuário |
| `POST` | `/users/cart` | Adiciona/atualiza item — body: `{ "product": { "id", ... } }` |
| `DELETE` | `/users/cart` | Remove item — body: `{ "id": "..." }` |
| `DELETE` | `/users/clearCart` | Limpa todo o carrinho |

### Sessão

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/refresh` | Renova os tokens a partir do refresh token (rotaciona o refresh antigo) |

🔒 = requer autenticação (cookie `acess_token` ou header `Authorization: Bearer <token>`)

### Códigos de erro de autenticação

- `401` — token expirado (`type_error: "expired"`) → o frontend deve chamar `/refresh`
- `422` — token inexistente ou inválido (revogado via logout)
- Erros de validação de cadastro retornam flags como `hasRepeated` e `manyCharacters`

---

## 📁 Estrutura do Projeto

```
├── app.py               # Aplicação Flask: models, rotas e configuração
├── authentication.py    # Decorators de autenticação e criação de JWTs
├── redis_manager.py     # Conexão e helpers de blacklist no Redis
├── products.py          # Seed com o catálogo de produtos do empório
├── database_creator.py  # Cria as tabelas do banco
├── deleter.py           # Utilitário para limpar a tabela de produtos
├── requirements.txt     # Dependências
├── .env.example         # Template de variáveis de ambiente
└── utils/
    ├── jwt_utils.py     # Decodificação de JWT e extração de tokens
    └── datetime_utils.py# Utilitários de data/expiração
```
