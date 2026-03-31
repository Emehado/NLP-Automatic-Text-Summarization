# Getting Started

This guide walks you through setting up and running the NLP pipeline from scratch.

---

## Prerequisites

- **Python 3.9 or higher** — check with `python3 --version`
- **pip** — comes with Python
- **4 GB free RAM** — the BART model requires ~1.6 GB of RAM when loaded
- **5 GB free disk space** — for the BART model weights (~1.6 GB) + Python packages

Optional but recommended:
- **NVIDIA GPU with CUDA** — makes the summarisation step ~20× faster (from minutes to seconds)

---

## Step 1: Clone or Download the Project

```bash
git clone <repository-url>
cd NLP-Automatic-Text-Summarization
```

Or extract the zip file into a folder and open a terminal there.

---

## Step 2: Create a Virtual Environment

A virtual environment isolates the project's dependencies from your system Python installation.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

Your terminal prompt should now show `(venv)` at the beginning.

---

## Step 3: Install Dependencies

```bash
pip install fastapi uvicorn "python-multipart" transformers torch pymupdf pydantic
```

**What each package does:**

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework for the API server |
| `uvicorn` | ASGI server that runs FastAPI |
| `python-multipart` | Required by FastAPI to handle file uploads |
| `transformers` | HuggingFace library — loads BART |
| `torch` | PyTorch — required by transformers for tensor computation |
| `pymupdf` | PDF text extraction (`import fitz`) |
| `pydantic` | Data validation (installed automatically with FastAPI) |

**GPU support (optional):** If you have a CUDA-capable NVIDIA GPU, install the GPU version of PyTorch instead. Check your CUDA version with `nvidia-smi`, then get the right command from [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/).

---

## Step 4: Start the Server

```bash
python pipeline.py
```

Or equivalently:
```bash
uvicorn pipeline:app --reload --host 0.0.0.0 --port 8000
```

**First startup will be slow** (30–120 seconds). On the first run, `transformers` downloads the BART model weights (~1.6 GB) from HuggingFace. These are cached in `~/.cache/huggingface/hub/` and subsequent startups will be fast.

You should see:
```
Loading BART model...
Model loaded.

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Step 5: Open the App

Navigate to **http://localhost:8000** in your browser.

You should see the landing page with a "Begin Pipeline" button.

---

## Step 6: Run the Pipeline

1. **Step 1 — Extract:** Click "Begin Pipeline", upload a research PDF, click "Extract Text". Wait for the text preview to appear.

2. **Step 2 — Preprocess:** Click "Continue to Preprocessing". The extracted text is auto-imported. Configure options (Lowercase, Text Sectioning) and click "Process Text". The Before/After comparison and section accordion will appear.

3. **Step 3 — Summarize:** Click "Continue to Summarization". Click "Generate Summaries". **This step is slow** — 30–90 seconds on CPU. A spinner and skeleton loading card will show while waiting.

4. **Step 4 — Insights:** Click "View Insights". Insights load automatically. Explore keywords, research pillars, school of thought, alignment, methods, trending terms, and cross-disciplinary overlaps.

---

## Testing the API Directly

The API auto-documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can test each endpoint interactively through the Swagger UI without writing any code.

### Test with curl

**Extract:**
```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@paper.pdf"
```

**Preprocess:**
```bash
curl -X POST http://localhost:8000/preprocess \
  -H "Content-Type: application/json" \
  -d '{"text": "ABSTRACT This paper…", "options": {"lowercase": true, "sectioning": true}}'
```

**Summarize:**
```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"sections": [{"name": "ABSTRACT", "words": 100, "text": "This paper proposes…"}]}'
```

---

## Common Issues

### "No module named 'multipart'"

```
Error: 422 Unprocessable Entity on /extract
```

**Fix:** `pip install python-multipart`

---

### BART model download fails

**Cause:** No internet connection or HuggingFace is temporarily unavailable.

**Fix:** Ensure you have an internet connection on first run. Model is cached after first download — subsequent runs work offline.

---

### "No text could be extracted from this PDF"

**Cause:** The PDF is a scanned image, not a text-based PDF.

**Fix:** Use a text-based PDF (downloaded from arXiv, journal sites, or created from Word/LaTeX). Scanned PDFs require OCR, which is not supported by this project.

---

### Summarization takes too long

**Cause:** BART runs on CPU by default. A typical paper takes 2–5 minutes on CPU.

**Fix:** Install the GPU version of PyTorch if you have an NVIDIA GPU. See [technologies/overview.md](../technologies/overview.md).

---

### Port 8000 already in use

```
ERROR: [Errno 48] Address already in use
```

**Fix:** Either kill the existing process using port 8000, or start on a different port:

```bash
uvicorn pipeline:app --port 8001
```

And update `API_BASE` in `index.html`:
```js
const API_BASE = "http://localhost:8001";
```

---

## Project Structure

```
NLP-Automatic-Text-Summarization/
├── pipeline.py        ← FastAPI server (run this)
├── index.html         ← Frontend SPA
├── script.js          ← Placeholder for future JS utilities
├── req.md             ← Original milestone requirements
├── venv/              ← Virtual environment (do not commit)
└── docs/              ← This documentation
    ├── README.md
    ├── architecture/
    ├── backend/
    ├── frontend/
    ├── technologies/
    ├── setup/
    └── milestones/
```
