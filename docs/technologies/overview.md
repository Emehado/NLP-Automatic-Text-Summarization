# Technology Stack

This document lists every technology used in the project, why it was chosen, and where to learn more.

---

## Backend

| Technology | Version | Role |
|------------|---------|------|
| **Python** | 3.9+ | Primary programming language |
| **FastAPI** | 0.100+ | Web framework — HTTP server + request routing |
| **Uvicorn** | 0.20+ | ASGI server that runs the FastAPI app |
| **Pydantic** | v2 | Request/response validation via type annotations |
| **PyMuPDF (fitz)** | 1.22+ | PDF parsing and text extraction |
| **HuggingFace Transformers** | 4.30+ | Loads and runs the BART model |
| **PyTorch** | 2.0+ | Tensor computation — required by Transformers |
| **BART-large-CNN** | — | Pre-trained abstractive summarisation model |

---

## Frontend

| Technology | Role |
|------------|------|
| **HTML5** | Document structure |
| **CSS3** | Styling, animations, responsive layout |
| **Vanilla JavaScript (ES2022)** | All interactivity, fetch API calls |
| **Google Fonts** | DM Sans + DM Serif Display typefaces |
| **SVG icons** | Inline SVG icons (no icon library dependency) |

---

## Why These Choices?

### FastAPI over Flask or Django

FastAPI uses Python type annotations to automatically:
- Validate request bodies (via Pydantic)
- Generate OpenAPI/Swagger documentation
- Produce meaningful error messages for invalid inputs

Flask requires manual validation. Django is significantly more complex than needed for a four-endpoint API. FastAPI hits the sweet spot of simplicity + features for ML inference APIs.

Reference: [FastAPI vs Flask comparison](https://fastapi.tiangolo.com/alternatives/)

### BART over GPT-2 or T5 for Summarization

| Model | Architecture | Strength |
|-------|-------------|----------|
| BART-large-CNN | Encoder-Decoder | Trained specifically on summarisation (CNN/DailyMail) |
| T5 | Encoder-Decoder | General text-to-text, needs more fine-tuning for summarisation |
| GPT-2 | Decoder-only | Text generation, not naturally suited to summarisation |

BART (`facebook/bart-large-cnn`) was fine-tuned on the CNN/DailyMail news summarisation dataset — one of the standard benchmarks for the task. It produces fluent, abstractive summaries out of the box without any fine-tuning. This is the right choice for a project that needs a working summariser without training infrastructure.

### PyMuPDF over pdfminer or pypdf

| Library | Speed | Accuracy | Block ordering |
|---------|-------|----------|----------------|
| PyMuPDF | Fast (C library) | High | Yes (`sort=True`) |
| pdfminer | Slow (pure Python) | Good | Manual |
| pypdf | Medium | Basic | No |

PyMuPDF wraps MuPDF, a professional C library used in PDF viewers. It is significantly faster than pure-Python alternatives and handles complex PDF structures (multi-column layouts, embedded fonts) more reliably.

### Vanilla JavaScript over React/Vue

For a four-page pipeline with a single API integration, a full JavaScript framework would add complexity without benefit. Vanilla JS with the Fetch API is sufficient. There is no state synchronization complexity (only one page is active at a time), no component lifecycle to manage, and the final output is one HTML file that requires zero build steps.

### Single HTML file

The entire frontend is one file. Advantages:
- Zero build configuration
- FastAPI can serve it with a single `FileResponse` line
- Students can open it directly in a browser (as a file:// URL) for development
- Nothing to install, no npm, no bundler

---

## Detailed Guides

- [BART Model](./bart-model.md) — How BART works internally
- [FastAPI & Pydantic](./fastapi.md) — Framework features used in this project
- [PyMuPDF](./pymupdf.md) — PDF parsing library details

---

## Dependency Installation

```bash
pip install fastapi uvicorn "python-multipart" transformers torch pymupdf pydantic
```

**`python-multipart`** is required by FastAPI to parse `multipart/form-data` (file uploads). It is not listed in some guides but will cause a 422 error on file upload endpoints if missing.

**`torch`** installs PyTorch. By default this installs the CPU version. For GPU acceleration:
```bash
# CUDA 12.1 example — check https://pytorch.org/get-started/locally/ for your version
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Reference: [PyTorch Installation Guide](https://pytorch.org/get-started/locally/)
