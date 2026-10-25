# Medalliance Agentic Data Pipeline

This project implements a simple agentic data pipeline for a few CSV files in a Medalliance-style architecture:

- Bronze: raw ingestion and validation
- Silver: cleaning, deduplication, and standardization
- Gold: business-ready curated output

Each layer can optionally use an AI agent backed by the Claude API.

## Quick start

1. Create a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your Claude API key
4. Place CSV files in `data/raw`
5. Run:

```bash
python -m medalliance.pipeline --input-dir data/raw --output-dir warehouse --use-claude
```

## Example architecture

```text
raw/ -> bronze/ -> silver/ -> gold/
```

Each layer can be processed by a dedicated agent with custom logic.
