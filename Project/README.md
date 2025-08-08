# H-ASM - Open Source ASM for Healthcare (MVP)

**Visão:** Plataforma ASM focada no setor de saúde com descoberta, enriquecimento, varredura e correlação com contexto clínico (PACS/HIS/EHR). MVP containerizado em Docker Compose.

## Status
MVP scaffold — discovery, mock enrichment, Nuclei integration point, FastAPI backend, Streamlit frontend, Celery worker.

## Quickstart (local, demo)
1. Copy `.env.example` to `.env` and edit if needed.
2. Start containers:
```bash
docker compose up --build
```
3. Open:
- API: `http://localhost:8000`
- Frontend (Streamlit): `http://localhost:8501`

## Structure
- `backend/` — FastAPI app, worker tasks, service wrappers (discovery/nuclei)
- `frontend/` — Streamlit UI for demos
- `tools/` — place nuclei templates and binaries

## CI
A simple GitHub Actions workflow runs lint and basic checks on PRs. See `.github/workflows/ci.yml`.

## Contributing
See `CONTRIBUTING.md` for contribution guidelines.

## Security & Privacy
This project is intended for authorized security testing only. Do **not** run against targets without explicit permission. Be mindful of LGPD/HIPAA: avoid storing PHI/PII in public repos or logs.

## License
MIT
