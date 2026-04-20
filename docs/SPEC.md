# Portal Transparência Utils - Sistema de Autenticação

## 1. Conceito & Visão

Sistema de busca de empenhos do Portal da Transparência com autenticação segura.
Protegido por múltiplas camadas de segurança: salt único por usuário, bcrypt com 12 rounds, e pepper criptográfico.
Interface moderna e intuitiva, com proteção de rotas e gerenciamento de sessões.

## 2. Arquitetura de Segurança

### 2.1 Hash Salt + Pepper Flow

```
SENHA → SALT (único) → BCRYPT 12 rounds → HASH FINAL
```

### 2.2 Modelo de Dados

**users**: id, username, email, password_hash, salt, created_at, last_login, is_active, role

**user_sessions**: id, user_id, token, refresh_token, expires_at, created_at, ip_address, user_agent, is_active

**api_keys**: id, user_id, api_key_hash, description, rate_limit_override, created_at, last_used, is_active

## 3. Endpoints

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/auth/login` | Página de login | ✗ |
| POST | `/auth/login` | Login | ✗ |
| GET | `/auth/register` | Página de cadastro | ✗ |
| POST | `/auth/register` | Cadastro | ✗ |
| POST | `/auth/logout` | Logout | ✓ |
| GET | `/auth/me` | Dados do usuário | ✓ |
| GET | `/` | Página inicial | ✓ |
| POST | `/search` | Buscar empenhos | ✓ |
| POST | `/generate` | Gerar relatório | ✓ |

## 4. Segurança Implementada

- **Salt**: 32 hex chars único por usuário
- **Bcrypt**: 12 rounds
- **Rate Limiting**: 5 tent, 5 min block
- **Validação**: Força de senha, sanitização

## 5. Stack

Flask 3.0 + SQLAlchemy + Flask-Login + PostgreSQL + Redis