# Backlog Ágil + Arquitetura do MVP (com `docker-compose`)

---

# 1 — Visão do MVP (recap curto)

**Objetivo do MVP:** permitir, a partir de um domínio raiz, descobrir subdomínios e ativos, enriquecer com fontes externas (via integração), rodar varredura básica (Nuclei), correlacionar com contexto clínico (tags PACS/HIS/EHR), gerar score de risco simples e apresentar dashboards/relatórios exportáveis. Implementação minimal e containerizada.

Funcionalidades mínimas do MVP:

* API REST (FastAPI) com endpoints para iniciar scan, listar ativos, vulnerabilidades e gerar relatório.
* Worker para execução de scans assíncronos (Celery + Redis).
* Scanner de descoberta (wrapper para Amass/Subfinder) — modo chamado via comando (execução em container).
* Enriquecimento básico com Shodan/Censys/VirusTotal — interfaces que podem ser mocked se não houver chave.
* Scanner Nuclei (invocado localmente no container).
* DB PostgreSQL para persistência.
* Frontend simples (Streamlit) com telas: enviar domínio, listar ativos, ver vulnerabilidades, exportar CSV.
* Export CSV/JSON e webhook/email básico (SMTP configurável).
* Docker Compose com serviços: api, worker, frontend, db, redis, (opcional) nginx.

---

# 2 — Backlog Ágil (épicos → histórias → tarefas)

## Epics (MVP)

1. **EPIC-CORE** — Core API, DB, modelos de dados e persistência.
2. **EPIC-DISCOVERY** — Integração de enumeração (Amass/Subfinder), fingerprinting.
3. **EPIC-ENRICH** — Integração com Shodan/Censys/VirusTotal (mocks incluídos).
4. **EPIC-SCAN** — Integração e execução de Nuclei/OpenVAS (Nuclei no MVP).
5. **EPIC-SCORES** — Motor de scoring (CVSS + exposição + contexto clínico).
6. **EPIC-FRONTEND** — Dashboard Streamlit para operação manual e relatórios.
7. **EPIC-WORKFLOW** — Queue + worker (Celery) e alertas (webhook/email).
8. **EPIC-AD** — Importação básica de artefatos AD (arquivo BloodHound export).
9. **EPIC-SECURITY** — Policies: keys, secrets storage, rate limits.

---

## Histórias e critérios de aceitação (exemplos prontos)

### EPIC-CORE → HIST-001

**Título:** Como analista, quero registrar um domínio para varredura via API para iniciar a descoberta.
**Critérios de aceitação:**

* POST `/api/v1/scan` aceita JSON `{ "domain": "hospitalabc.com.br", "owner":"Security Team" }` e retorna `scan_id` e status `queued`.
* Scan é persistido na tabela `scans` com timestamp.

### EPIC-DISCOVERY → HIST-002

**Título:** Como sistema, devo enumerar subdomínios usando Amass/Subfinder (ou mock) e persistir ativos.
**Critérios de aceitação:**

* Worker pega `scan_id`, executa módulo `discovery`, cria registros na tabela `assets` com campos: `hostname`, `ip`, `asn`, `country`, `fingerprint`, `service_type`.
* Em ambiente sem Amass, o módulo usa um `mock_discovery` que gera 5 assets de teste.

### EPIC-ENRICH → HIST-003

**Título:** Enriquecer ativos com Shodan/Censys/VirusTotal.
**Critérios de aceitação:**

* Para cada asset, campos `shodan_tags`, `censys_score`, `virustotal_malicious` são preenchidos (pode ser `null` se sem keys).
* Se chaves não existirem, rota `GET /api/v1/enrich/status` mostra “integration: shodan - mocked”.

### EPIC-SCAN → HIST-004

**Título:** Rodar Nuclei para identificar templates e vulnerabilidades.
**Critérios de aceitação:**

* Worker executa `nuclei -u http(s)://<asset> -t /templates` (ou mock) e grava `vulns` com `id, template, severity, evidence`.
* API `GET /api/v1/assets/{id}/vulns` retorna lista.

### EPIC-SCORES → HIST-005

**Título:** Gerar score de risco agregado por ativo.
**Critérios de aceitação:**

* Para cada asset, calcular: `score = base_cvss_weighted + exposure_weight + clinical_impact`.
* Expor via API: `GET /api/v1/assets/{id}/score` com explicação dos fatores.

### EPIC-FRONTEND → HIST-006

**Título:** Permitir interação via UI simples (Streamlit): cadastrar domínio, ver ativos, exportar CSV.
**Critérios de aceitação:**

* Usuário carrega domínio, vê progresso de scan, tabela de ativos, botão `Export CSV`, link para detalhes.

### EPIC-WORKFLOW → HIST-007

**Título:** Enviar alerta via webhook quando asset com score > threshold for encontrado.
**Critérios de aceitação:**

* Sistema dispara POST para `WEBHOOK_URL` configurada com payload do ativo quando `score >= 80`.

---

## Sprint 0 (setup infra, 1 semana)

* T0.1 Repositório e README, LICENSE
* T0.2 `docker-compose.yml`, `.env.example`
* T0.3 Esqueleto FastAPI (endpoints básicos)
* T0.4 Esqueleto Streamlit
* T0.5 Config Celery + Redis, Postgres

## Sprint 1 (descoberta e persistência, 2 semanas)

* Implementar discovery wrapper (Amass/subfinder + mocks)
* Persistir assets e scans
* Endpoint iniciar scan e consultar status

## Sprint 2 (enriquecimento + scan Nuclei, 2 semanas)

* Implementar integrações externas (mocks)
* Implementar execução Nuclei (ou mock)
* Persistir vulnerabilidades

## Sprint 3 (scoring + alerts + frontend, 2 semanas)

* Scoring básico
* Alerts via webhook/email
* Streamlit UI final do MVP
* Documentação final e scripts

---

# 3 — Arquitetura do MVP (texto + diagrama ASCII)

## Componentes

* **API (FastAPI)** — Orquestra scans, recebe requests, serve dados.
* **Worker (Celery)** — Executa discovery/enrich/scan de forma assíncrona.
* **DB (Postgres)** — Persistência.
* **Broker/Cache (Redis)** — Broker para Celery + cache de resultados.
* **Frontend (Streamlit)** — Interface simples para operações.
* **Tools (Amass, Subfinder, Nuclei)** — executáveis containerizados (ou em binários no container).
* **Integrations** — adaptadores para Shodan/Censys/VT (podem ser mocks).

## Diagrama (simplificado)

```
+-----------+         +-----------+        +-----------+
|  Streamlit| <-----> |  FastAPI  | <----> | Postgres  |
|  Frontend |         |   API     |        |  Database |
+-----------+         +-----------+        +-----------+
                           |
                           v
                        Redis (Broker)
                           |
                     +-----------+
                     |  Celery   |
                     |  Worker   |
                     +-----------+
                        /   |   \
                       /    |    \
                  Amass  Nuclei  Enrich(adapters)
                      (container/binary)   (Shodan/Censys/VT)
```

---

# 4 — Estrutura de diretórios proposta (pronta para GitHub)

```
asm-healthcare/
├── .github/
│   ├── ISSUE_TEMPLATE.md
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── scans.py
│   │   │   │   └── assets.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── scoring.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   └── crud.py
│   │   ├── workers/
│   │   │   └── tasks.py
│   │   └── services/
│   │       ├── discovery.py
│   │       ├── nuclei_runner.py
│   │       └── enrichers.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py  # Streamlit
│   ├── Dockerfile
│   └── requirements.txt
├── tools/
│   └── nuclei-templates/  # submodule / git-lfs or reference
├── docker-compose.yml
├── .env.example
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

---

# 5 — Arquivos essenciais (códigos de exemplo prontos)

## `docker-compose.yml`

```yaml
version: "3.8"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-asm}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-asm_pass}
      POSTGRES_DB: ${POSTGRES_DB:-asm_db}
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - asmnet

  redis:
    image: redis:7
    ports: ["6379:6379"]
    networks:
      - asmnet

  api:
    build: ./backend
    depends_on:
      - db
      - redis
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app
      - ./tools:/tools
    networks:
      - asmnet

  worker:
    build: ./backend
    command: ["celery", "-A", "app.workers.tasks.celery_app", "worker", "--loglevel=info"]
    depends_on:
      - redis
      - db
    env_file:
      - .env
    volumes:
      - ./backend/app:/app
      - ./tools:/tools
    networks:
      - asmnet

  frontend:
    build: ./frontend
    depends_on:
      - api
    env_file:
      - .env
    ports:
      - "8501:8501"
    volumes:
      - ./frontend:/frontend
    networks:
      - asmnet

volumes:
  db_data:

networks:
  asmnet:
    driver: bridge
```

---

## `.env.example`

```
POSTGRES_USER=asm
POSTGRES_PASSWORD=asm_pass
POSTGRES_DB=asm_db
DATABASE_URL=postgresql://asm:asm_pass@db:5432/asm_db

REDIS_URL=redis://redis:6379/0

SHODAN_API_KEY=
CENSYS_API_ID=
CENSYS_API_SECRET=
VIRUSTOTAL_API_KEY=

WEBHOOK_URL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SECRET_KEY=change-me
NUCLEI_TEMPLATES_PATH=/tools/nuclei-templates
```

---

## `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY ./app /app
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### `backend/app/requirements.txt` (essencial)

```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
alembic
pydantic
celery[redis]
httpx
python-dotenv
databases
requests
python-multipart
```

---

## `backend/app/main.py` (FastAPI minimal)

```python
from fastapi import FastAPI
from app.api.v1 import scans, assets

app = FastAPI(title="ASM Healthcare API - MVP")

app.include_router(scans.router, prefix="/api/v1/scans", tags=["scans"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])

@app.get("/")
def read_root():
    return {"service": "ASM Healthcare API", "version": "mvp"}
```

---

## `backend/app/api/v1/scans.py` (exemplo)

```python
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.workers.tasks import enqueue_scan

router = APIRouter()

class ScanRequest(BaseModel):
    domain: str
    owner: str | None = None

@router.post("/", status_code=202)
def create_scan(req: ScanRequest):
    scan_id = enqueue_scan(req.domain, req.owner)
    return {"scan_id": scan_id, "status": "queued"}
```

---

## `backend/app/workers/tasks.py` (exemplo Celery tasks)

```python
import os
from celery import Celery
from uuid import uuid4
from app.services.discovery import run_discovery
from app.services.nuclei_runner import run_nuclei

celery_app = Celery("workers", broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))

def enqueue_scan(domain, owner=None):
    scan_id = str(uuid4())
    celery_app.send_task("app.workers.tasks.worker_scan", args=[scan_id, domain, owner])
    return scan_id

@celery_app.task(name="app.workers.tasks.worker_scan")
def worker_scan(scan_id, domain, owner):
    # Persist scan start (omitted here)
    assets = run_discovery(domain)
    for a in assets:
        # Persist asset (omitted)
        run_nuclei(a["url"])
    # finalize scan
    return {"scan_id": scan_id, "domain": domain}
```

---

## `backend/app/services/discovery.py` (wrapper mock)

```python
def run_discovery(domain: str):
    # TODO: call Amass / Subfinder binaries (via subprocess) in real deployment
    # For MVP: return mock assets
    return [
        {"hostname": f"www.{domain}", "ip":"10.0.0.1", "asn":"AS12345", "country":"BR", "url": f"http://www.{domain}"},
        {"hostname": f"api.{domain}", "ip":"10.0.0.2", "asn":"AS12345", "country":"BR", "url": f"https://api.{domain}"}
    ]
```

---

## `frontend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /frontend
COPY ./requirements.txt /frontend/requirements.txt
RUN pip install --no-cache-dir -r /frontend/requirements.txt
COPY . /frontend
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### `frontend/requirements.txt`

```
streamlit
requests
pandas
```

### `frontend/app.py` (Streamlit minimal)

```python
import streamlit as st
import requests
import pandas as pd
API_URL = st.secrets.get("API_URL", "http://api:8000")

st.title("ASM Healthcare - MVP")

with st.form("scan_form"):
    domain = st.text_input("Domain (ex: hospitalabc.com.br)")
    owner = st.text_input("Owner / Team")
    submitted = st.form_submit_button("Start scan")
    if submitted and domain:
        resp = requests.post(f"{API_URL}/api/v1/scans/", json={"domain": domain, "owner": owner})
        st.write(resp.json())

st.header("Assets")
try:
    resp = requests.get(f"{API_URL}/api/v1/assets")
    assets = resp.json()
    st.dataframe(pd.DataFrame(assets))
except Exception as e:
    st.write("API not available yet.")
```

---

# 6 — Scripts úteis (para incluir)

* `scripts/init_db.sh` — roda migrations (alembic) e cria tabelas.
* `scripts/run_nuclei.sh` — helper para executar nuclei templates fornecidos.
* `scripts/mock_data.py` — popula DB com dados de exemplo para demo.

---

# 7 — Documentação para GitHub (prontos para colar)

## `README.md` (resumo pronto)

```markdown
# ASM Healthcare — Open Source ASM for Healthcare (MVP)

**Visão:** Plataforma ASM focada no setor de saúde com descoberta, enriquecimento, varredura e correlação com contexto clínico (PACS/HIS/EHR). MVP containerizado em Docker Compose.

## Funcionalidades do MVP
- Descoberta de ativos (mock/Amass)
- Enriquecimento básico (Shodan/Censys/VT adapters — suportam mock)
- Varredura com Nuclei
- Scoring básico por ativo
- Dashboard minimal (Streamlit)
- Export CSV / JSON
- API REST (FastAPI)
- Workers assíncronos (Celery + Redis)

## Pré-requisitos
- Docker & Docker Compose
- (Opcional) chaves Shodan/Censys/VirusTotal em `.env`

## Quickstart
1. Copie `.env.example` para `.env` e ajuste variáveis.
2. `docker compose up --build`
3. Acesse:
   - API: `http://localhost:8000`
   - Frontend Streamlit: `http://localhost:8501`

## Estrutura
Veja `/backend`, `/frontend`, `/tools`.

## Contribuição
Veja `CONTRIBUTING.md`.

## Segurança
Report de vulnerabilidades em `SECURITY.md`.

## License
MIT — veja `LICENSE`.
```

---

## `CONTRIBUTING.md` (pronto)

```markdown
# Contribuindo

Obrigado por contribuir! Regras rápidas:
- Abra uma issue antes de grandes mudanças.
- Fork → branch `feature/<descr>` → PR targeting `main`.
- Testes automatizados para mudanças em backend.
- Siga o Code of Conduct.
```

---

## `SECURITY.md` (pronto)

```markdown
# Security Policy

Report vulnerabilities to security@your-org.example (ou crie issue com label `security`). Não exponha PII/PHI em issues públicas. Forneça steps to reproduce e logs sensíveis via e-mail PGP (chave pública em /SECURITY.md).
```

---

## `LICENSE` (MIT)

```text
MIT License
[... padrão MIT ...]
```

---

## `ISSUE_TEMPLATE.md` (pronto)

```markdown
## Tipo de Issue
- [ ] Bug
- [ ] Feature
- [ ] Documentation

## Descrição
<!-- descreva o que aconteceu -->

## Passos para reproduzir
1.
2.
3.

## Ambiente
- Docker
- Docker Compose
```

---

# 8 — API design (endpoints principais)

```
POST /api/v1/scans/                # iniciar scan
GET  /api/v1/scans/{scan_id}       # status + progress
GET  /api/v1/assets/               # list assets (paginado)
GET  /api/v1/assets/{id}           # detalhes asset + score + vulns
GET  /api/v1/assets/{id}/vulns     # lista de vulnerabilidades
POST /api/v1/ad/import            # upload BloodHound JSON (import AD artefacts)
GET  /api/v1/reports/{scan_id}    # gerar/baixar relatório (CSV/JSON)
```

---

# 9 — Scoring (modelo MVP — explicação)

Score (0-100) = clamp(

* `cvss_component` = max CVSS / 10 \* 50 (peso 50%)
* `exposure_component` = 25 \* exposure\_factor (ip public, open ports, shodan hits)
* `clinical_component` = 25 \* clinical\_impact\_factor (PACS/HIS/EHR exposure -> 1.0)
  )

Exemplo:

* CVSS 9.8 → cvss\_component = 9.8/10 \* 50 ≈ 49
* exposure\_factor = 1 → exposure\_component = 25
* clinical\_impact\_factor = 1 (PACS exposed) → clinical\_component = 25
  Score = 99 → capped 100.

A resposta da API inclui breakdown detalhado para permitir auditoria.

---

# 10 — Segurança, LGPD & HIPAA — recomendações iniciais

* Nunca armazenar PHI em logs públicos. Mask/Redact.
* Secrets no `.env` e orientar uso de Vault (HashiCorp) para produção.
* Role-based access: exigir autenticação (JWT/OAuth2) para endpoints sensíveis (próxima iteração).
* Registrar consent e auditoria de acesso a PII.
* Para integração com AD/ BloodHound: exigir arquivos exportados com permissão.

---

# 11 — Checklist para publicar no GitHub (arquivos a adicionar)

* `README.md`, `LICENSE`, `.env.example`, `docker-compose.yml`, `backend/` (com código), `frontend/`, `.github/ISSUE_TEMPLATE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` (opcional), `templates/` (nuclei templates pointer ou submodule).

---

# 12 — Exemplo de workflow CI simples (GitHub Actions) — `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install deps
        run: |
          pip install -r backend/app/requirements.txt
      - name: Run flake8
        run: |
          pip install flake8
          flake8 backend/app || true
```

---

# 13 — Como publicar no GitHub (passo-a-passo)

1. Crie repositório `asm-healthcare` no GitHub.
2. Clone localmente e cole a estrutura acima.
3. `git add . && git commit -m "Initial MVP scaffold" && git push origin main`
4. (Opcional) adicionar submodule `nuclei-templates` ou instrução para `git clone` em `tools/`.
5. Habilitar Actions, configurar secrets (SHODAN\_KEY, CENSYS\_ID, etc).

---

# 14 — Próximos passos / Roadmap (após MVP)

* Autenticação & RBAC (OAuth, SSO).
* Integração com SIEM (Splunk/Elastic).
* Scanners adicionais: OpenVAS, Masscan.
* Visualização avançada: Grafana + Loki para logs.
* Integração AD real: parsers para BloodHound, PingCastle, AD\_Miner.
* Testes E2E e cobertura automatizada.
* Harden production: TLS, ingress, rate limiting, audits.

---

# 15 — Arquivos finais: copy-ready (você pode copiar cada bloco)

Todos os blocos de código acima (docker-compose, Dockerfile, FastAPI minimal, Streamlit) são **copy-paste ready**. Recomendo criar o repositório com essa árvore e, na primeira execução, usar dados mock (sem chaves das APIs externas) para validar fluxo.
