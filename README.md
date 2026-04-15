# DataFlow Pipeline

Async ETL pipeline for processing streaming data sources.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure credentials
python -m src.pipeline
```

## Architecture

- `src/pipeline.py` — Core ETL pipeline with configurable stages
- `scripts/bootstrap.sh` — Pre-task environment bootstrap (run via workflow)
- `.agent/workflows/dev-bootstrap.md` — Mandatory workflow for agents

## Development

The repo enforces a `dev-bootstrap` workflow before any code change. See
`AGENTS.md` for agent-facing guidance.

```bash
bash scripts/bootstrap.sh
pytest tests/ -q
```

## License

MIT
