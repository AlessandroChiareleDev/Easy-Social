# Deploy VPS - Status & Próximos Passos

## ✅ O que já está pronto

### Servidor VPS (76.13.169.45)

- **OS**: Ubuntu 24.04.4 LTS
- **SSH**: Acesso via chave (`~/.ssh/id_ed25519`) — sem senha
- **Nginx**: Configurado como reverse proxy (porta 80)
- **Node.js**: v20.20.2 + PM2 6.0.14
- **Python**: 3.12.3 + venv com todas as deps
- **PostgreSQL 16**: Local para certificados A1
  - User: `easy_social_user` / Senha: `sua_senha_segura`
  - DB: `easy_social_db`
  - Tabelas: `certificados_a1`, `config_esocial`, `senha_certificado_salva`
- **Xvfb**: Display virtual :99 para pyautogui (headless)
- **Firewall (UFW)**: Portas 22, 80, 443 abertas
- **PM2 Startup**: Configurado para auto-start no boot

### Serviços Rodando

| Serviço          | PM2 Name     | Porta | Status    |
| ---------------- | ------------ | ----- | --------- |
| Backend Node.js  | easy-backend | 3333  | ✅ Online |
| Python API       | easy-python  | 8000  | ✅ Online |
| Nginx (frontend) | systemd      | 80    | ✅ Active |
| Xvfb             | systemd      | :99   | ✅ Active |
| PostgreSQL       | systemd      | 5432  | ✅ Active |

### Nginx Routing

| URL             | Destino                                                  |
| --------------- | -------------------------------------------------------- |
| `/`             | Frontend Vue (static: `/opt/easy-social/frontend/dist/`) |
| `/api/*`        | Node backend (`localhost:3333`)                          |
| `/python-api/*` | Python API (`localhost:8000`) — strip prefix             |
| `/uploads/*`    | Static files (`/opt/easy-social/backend/uploads/`)       |

### Endpoints Testados (via IP público)

- `http://76.13.169.45/` → Frontend (200 ✅)
- `http://76.13.169.45/api/health` → Backend health OK ✅
- `http://76.13.169.45/python-api/docs` → Python Swagger (200 ✅)

---

## ⏳ Falta fazer — DNS + SSL

### 1. Configurar DNS (no painel da Hostinger)

O domínio `easyesocial.com.br` atualmente aponta para `2.57.91.91` (IP padrão).
Precisa ser alterado para `76.13.169.45`.

**Passos no painel Hostinger:**

1. Acessar https://hpanel.hostinger.com
2. Ir em **Domínios** → `easyesocial.com.br` → **DNS / Nameservers**
3. Editar ou criar registros:
   - **A** → `@` → `76.13.169.45` (TTL: 300)
   - **A** → `www` → `76.13.169.45` (TTL: 300)
4. Aguardar propagação DNS (5 min a 48h, geralmente 10-30 min)

### 2. Instalar SSL (após DNS propagar)

Rodar no VPS (via SSH):

```bash
ssh root@76.13.169.45
certbot --nginx -d easyesocial.com.br -d www.easyesocial.com.br --non-interactive --agree-tos --email admin@easyesocial.com.br
certbot renew --dry-run
```

Ou rodar o script localmente:

```bash
python python-scripts/_setup_ssl.py
```

### 3. Teste final

Após SSL:

- `https://easyesocial.com.br` → Frontend
- `https://easyesocial.com.br/api/health` → Backend
- `https://easyesocial.com.br/python-api/docs` → Python

---

## Arquitetura de Produção

```
Internet
   │
   ▼
Nginx (:80/:443) ─── SSL/Let's Encrypt
   │
   ├── /              → Vue SPA (dist/ static files)
   ├── /api/*         → Node.js backend (:3333) → Supabase
   └── /python-api/*  → Python FastAPI (:8000) → Supabase + LocalPG (certs)
```

## Conexões de Banco

- **Supabase** (main): `aws-1-us-east-2.pooler.supabase.com` → Todas as tabelas de negócio
- **Local PG** (certs only): `localhost:5432/easy_social_db` → Certificados A1

## Scripts úteis

| Script                | Função                                  |
| --------------------- | --------------------------------------- |
| `_deploy_upload.py`   | Upload + extração do projeto no VPS     |
| `_deploy_build.py`    | Configurar .env, instalar deps, buildar |
| `_deploy_services.py` | Configurar Nginx + PM2                  |
| `_setup_ssl.py`       | Verificar DNS e instalar SSL            |

## Comandos úteis no VPS

```bash
ssh root@76.13.169.45        # Conectar
pm2 status                    # Ver serviços
pm2 logs easy-backend         # Logs backend
pm2 logs easy-python          # Logs Python
pm2 restart all               # Reiniciar tudo
nginx -t && systemctl reload nginx  # Recarregar Nginx
```
