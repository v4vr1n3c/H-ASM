# H-ASM
H-ASM (Healthcare Attack Surface Management)

# ASM-Healthcare — MVP (Open Source)

> **Plataforma de Attack Surface Management (ASM)** focada em instituições de **healthcare**. Este repositório contém o **MVP técnico**, arquitetura, backlog ágil e toda a documentação necessária para publicar no GitHub e iniciar desenvolvimento.

---

## Sumário

1. Visão Geral
2. Escopo do MVP
3. Arquitetura Técnica
4. docker-compose (MVP)
5. Estrutura do Repositório
6. Como rodar localmente
7. API (endpoints principais)
8. Modelo de dados (simplificado)
9. Backlog Ágil (épicos, histórias, tasks)
10. Roadmap / Sprints iniciais
11. Segurança, LGPD & HIPAA — orientações
12. Testes, CI/CD e Linting
13. Contribuição
14. Licença

---

# 1. Visão Geral

Plataforma open-source para descoberta, enriquecimento, correlação e priorização de riscos relacionados à superfície de ataque de instituições de saúde. O MVP oferece descoberta automatizada a partir de um domínio raiz, enriquecimento por APIs públicas, scanner de vulnerabilidades leve, correlação com dados de AD (importados) e visualização básica via frontend.

Objetivos imediatos do MVP:

* Descoberta de ativos (externos) via Amass/Subfinder + resolução
* Fingerprinting básico (WhatWeb / Wappalyzer + HTTP headers)
* Enriquecimento (Shodan / Censys / VirusTotal — adaptável por chave de API)
* Scanner leve (Nuclei) para identificar templates de risco
* Correlação com dados AD importados (JSON/CSV gerado por BloodHound/AD\_Miner)
* Backend FastAPI com REST API
* Frontend React com painel inicial (lista de ativos, risco, filtros)
* Empacotamento via Docker Compose

# 2. Escopo do MVP

**Inclusões:**

* Descoberta ativa/passiva de subdomínios
* Resolução DNS, fingerprinting HTTP
* Enriquecimento com pelo menos 2 fontes (configuráveis)
* Integração básica com Nuclei para templates
* DB com modelo de ativos e vulnerabilidades
* API REST para gerenciar scans, visualizar ativos e exportar CSV/JSON
* Frontend com: tabela de ativos + painel de risco agregado
* Alertas simples via webhook (POST)

**Exclusões (para roadmap pós-MVP):**

* Scanners pesados integrados (OpenVAS completo) por padrão
* Orquestração multi-tenant
* Automação avançada de mitigação
* UI de análise AD complexa (apenas importação e correlação básica)

# 3. Arquitetura Técnica

```
+-----------+      +----------------+      +-----------+
| Operator  | ---> |  Frontend React| <--> | FastAPI   |
| (browser) |      +----------------+      +-----------+
|           |                             /  |  |  \    
+-----------+                            /   |  |   \   
                                         /    |  |    \  
+----------+    +---------------+   +------+ |  |  +-------+
| Scheduler| -> | Discovery WS  | ->|Workers|--+--|Enricher|
|(Celery)  |    |(amass/subfinder)|  +------+     +-------+
+----------+    +---------------+                      |
                                                 +-----v-----+
                                                 | PostgreSQL |
                                                 +-----------+
```

Componentes principais:

* **Frontend:** React (CRA / Vite) com componentes para tabelas, filtros e visualização de timeline. Alternativa rápida: Streamlit para PoC.
* **Backend:** FastAPI, autenticação JWT (modo mínimo para MVP), rotas para agendar scans, consultar ativos, realizar exportações e receber uploads de AD.
* **Workers:** Worker para execução de ferramentas (Amass/Subfinder, Nuclei) e enriquecimento (Shodan/Censys). Pode usar Celery + Redis para filas.
* **DB:** PostgreSQL (preferível para queries relacionais e integridade).
* **Storage:** Volume para Nuclei/scan outputs e para relatórios exportados.
* **Orquestração:** Docker Compose com serviços: db, backend, frontend, worker, redis, nginx (opcional).

# 4. docker-compose (MVP)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_USER: asm
      POSTGRES_PASSWORD: asm_pass
      POSTGRES_DB: asmdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    restart: unless-stopped

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://asm:asm_pass@postgres:5432/asmdb
      REDIS_URL: redis://redis:6379/0
      SHODAN_API_KEY: "${SHODAN_API_KEY}"
      NUCLEI_TEMPLATES_DIR: /templates
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://asm:asm_pass@postgres:5432/asmdb
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
```

> **Nota:** Para rodar ferramentas nativas (amass, subfinder, nuclei) você pode usar imagens separadas ou bundlar estas ferramentas no container `worker` com as permissões necessárias. Alternativa mais segura: usar containers especializados para cada ferramenta.

# 5. Estrutura do Repositório

```
asm-healthcare-mvp/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── workers/
│   │   └── utils/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── tools/
│   ├── nuclei/
│   ├── amass/
│   └── subfinder/
├── docker-compose.yml
├── .env.example
├── README.md
└── docs/
    ├── ARCHITECTURE.md
    ├── BACKLOG.md
    └── SECURITY.md
```

# 6. Como rodar localmente (passo-a-passo)

1. Clone o repositório.
2. Copie `.env.example` para `.env` e preencha as chaves de API (Shodan, Censys, VirusTotal se disponível).
3. `docker-compose up --build`
4. Backend será acessível em `http://localhost:8000` (docs em `/docs`)
5. Frontend em `http://localhost:3000`

# 7. API (endpoints principais — esqueleto)

> FastAPI fornece documentação automática em `/docs`.

**Endpoints principais (MVP):**

* `POST /api/scan` — inicia um scan (body: { domain: string, profile?: string, notify\_webhook?: url })
* `GET /api/scan/{scan_id}` — status do scan
* `GET /api/assets` — lista assets (filtros: criticidade, tipo, unidade)
* `GET /api/assets/{asset_id}` — detalhes do asset, vulnerabilidades e evidências
* `POST /api/import/ad` — upload de export de BloodHound/AD\_Miner (JSON/ZIP)
* `GET /api/reports/{report_id}` — download CSV/JSON
* `POST /api/alerts/test` — testar webhook de alerta

# 8. Modelo de dados (simplificado)

**Tables (Postgres):**

* `organizations` (id, name, domain, created\_at)
* `units` (id, organization\_id, name, location)
* `assets` (id, organization\_id, unit\_id, hostname, ip, asn, country, fingerprint, asset\_type, discovered\_at)
* `vulnerabilities` (id, asset\_id, cve, cvss, description, source, discovered\_at, evidence)
* `scans` (id, organization\_id, initiated\_by, status, started\_at, finished\_at)
* `ad_imports` (id, organization\_id, file\_ref, imported\_at, summary\_json)
* `risk_scores` (id, asset\_id, score, vector, computed\_at)

Índices essenciais: `assets(hostname)`, `vulnerabilities(cve)`, `risk_scores(asset_id)`.

# 9. Backlog Ágil

> O backlog abaixo foi organizado por **épicos** e histórias (user stories) com critérios de aceitação e tasks técnicas. Pode ser colado em um board (GitHub Projects / Jira / Trello).

## Épico A — Descoberta e Fingerprinting

**US-A1** — *Como analista de segurança, quero iniciar um scan a partir do domínio para descobrir subdomínios automaticamente.*

* **Critério de aceitação:** Ao solicitar `POST /api/scan` com `domain`, são registrados subdomínios no DB (ex.: `*.hospitalabc.com.br`).
* **Tarefas:** integrar Amass/Subfinder, persistir resultados, deduplicar.

**US-A2** — *Como analista, quero que cada asset tenha fingerprint HTTP.*

* **Critério de aceitação:** Cada host resolvido tem headers, title, tecnologias detectadas (WhatWeb/Wappalyzer).
* **Tarefas:** executar requests, salvar fingerprints.

## Épico B — Enriquecimento e Correlação

**US-B1** — *Enriquecer assets com Shodan / Censys info.*

* **Critério de aceitação:** Para assets públicos, salvar dados de porta, serviço, CVEs indexados (quando presentes).
* **Tarefas:** criar worker de enrichment, cache para evitar limites de API.

**US-B2** — *Detectar exposição de endpoints clínicos (PACS/HIS/EHR).*

* **Critério de aceitação:** Assets cujo banner/fingerprint indicar serviços médicos recebem flag `medical_service=true`.
* **Tarefas:** criar regex/heurísticas para identificar PACS, DICOM, HL7 endpoints.

## Épico C — Vulnerability Scanning

**US-C1** — *Executar Nuclei templates contra assets descobertos.*

* **Critério de aceitação:** Vulnerabilidades com severidade mapeada são salvas no DB.
* **Tarefas:** provisionar templates, executar nuclei, parsear resultados.

## Épico D — Integração AD e Correlação Interna

**US-D1** — *Importar BloodHound export e correlacionar hosts com usuários/admins.*

* **Critério de aceitação:** Upload processado gera resumo: paths de privilégio, contas com exposição.
* **Tarefas:** parser de JSON/ZIP, cross-reference com `assets` via hostname/IP.

## Épico E — Visualização e Export

**US-E1** — *Exibir lista de assets com score de risco e filtros básicos.*

* **Critério de aceitação:** Frontend mostra paginação, filtros por criticidade e tipo.
* **Tarefas:** endpoints paginados, frontend tabelas.

**US-E2** — *Exportar CSV com risco por ativo.*

* **Critério de aceitação:** `GET /api/reports/{report_id}` retorna CSV com colunas definidas.

## Épico F — Alertas e Integração

**US-F1** — *Enviar webhook quando um ativo critico for detectado.*

* **Critério de aceitação:** Configurável por organização, test webhook disponível.

---

# 10. Roadmap / Sprints iniciais (6 semanas)

**Sprint 0 (Infra + Boilerplate) — 1 semana**

* Setup repo, docker-compose, DB, CI (GitHub Actions)
* FastAPI skeleton, healthcheck, /docs
* Frontend skeleton (list assets view)

**Sprint 1 (Discovery + Persistence) — 2 semanas**

* Integrar Amass/Subfinder
* Resolver DNS, persistir assets
* Fingerprinting básico (HTTP)

**Sprint 2 (Enrichment + Nuclei) — 2 semanas**

* Integração Shodan (configurável)
* Nuclei execution + parse
* Persistência de vulnerabilidades

**Sprint 3 (AD import + UI polish) — 1 semana**

* Implementar upload/import de BloodHound
* Correlacionar e exibir resultados no UI
* Export CSV, basic alerts

# 11.
