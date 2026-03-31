# NLP Automatic Text Summarization — Documentation

> **Group 11** — A four-step NLP pipeline that turns academic research PDFs into structured summaries and insights, powered by the BART transformer model and a FastAPI backend.

---

## Table of Contents

| Section | Description |
|---------|-------------|
| [Setup & Running](./setup/getting-started.md) | How to install dependencies and start the server |
| [Architecture Overview](./architecture/overview.md) | High-level system design and component map |
| [Data Flow](./architecture/data-flow.md) | How data moves through the pipeline step by step |
| [Backend Overview](./backend/overview.md) | FastAPI server structure and design decisions |
| [API Reference](./backend/api-reference.md) | All four endpoints documented with request/response shapes |
| [PDF Extraction](./backend/pdf-extraction.md) | How PDFs are parsed, cleaned, and trimmed |
| [Preprocessing](./backend/preprocessing.md) | Section detection, tokenization, and text normalisation |
| [Summarization](./backend/summarization.md) | BART model, beam search, chunking strategy |
| [Insights Engine](./backend/insights.md) | Keyword scoring, pillars, methods, alignment, cross-disciplinary |
| [Frontend Overview](./frontend/overview.md) | Single-page app structure, state management |
| [UI Components](./frontend/ui-components.md) | Design system, CSS variables, component catalogue |
| [JavaScript Logic](./frontend/javascript.md) | Step navigation, fetch calls, rendering functions |
| [Technologies](./technologies/overview.md) | Full technology stack with rationale |
| [BART Model](./technologies/bart-model.md) | Deep dive into how BART works |
| [FastAPI & Pydantic](./technologies/fastapi.md) | Framework features used in this project |
| [PyMuPDF](./technologies/pymupdf.md) | PDF parsing library explained |
| [Development Milestones](./milestones/development-history.md) | The four build milestones and what each introduced |

---

## Quick Start (30 seconds)

```bash
# 1. Install Python dependencies
pip install fastapi uvicorn transformers torch pymupdf pydantic

# 2. Start the server
python pipeline.py

# 3. Open the app
open http://localhost:8000
```

See [Getting Started](./setup/getting-started.md) for the full guide including virtual environment setup.

---

## What the Project Does

The pipeline accepts an academic research PDF and returns a structured summary plus rich analytical insights. It proceeds in exactly four steps:

```
PDF file
  │
  ▼
[Step 1 — Extract]      POST /extract      → raw cleaned text
  │
  ▼
[Step 2 — Preprocess]   POST /preprocess   → sections array
  │
  ▼
[Step 3 — Summarize]    POST /summarize    → BART summaries
  │
  ▼
[Step 4 — Insights]     POST /insights     → keywords, methods,
                                             alignment, trends…
```

Each step is a separate API call. The frontend is a single HTML file that calls these endpoints in sequence and renders the results interactively.
