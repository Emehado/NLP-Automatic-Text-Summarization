# Architecture Overview

## System Components

The project has two layers: a **Python backend** (FastAPI server) and a **browser frontend** (a single HTML file). They communicate over HTTP using JSON (or `multipart/form-data` for file uploads).

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Client)                    │
│                                                         │
│  index.html ── CSS design system ── inline <script>     │
│                                                         │
│  State object holds:                                    │
│    pdfFile · extractedText · sections · summaries       │
└───────────────────┬─────────────────────────────────────┘
                    │  HTTP (fetch API)
                    │  POST /extract      multipart/form-data
                    │  POST /preprocess   application/json
                    │  POST /summarize    application/json
                    │  POST /insights     application/json
                    ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Server  (pipeline.py)              │
│                                                         │
│  ┌──────────────┐  ┌─────────────────┐                 │
│  │  /extract    │  │  /preprocess    │                 │
│  │  PyMuPDF     │  │  extract_       │                 │
│  │  universal_  │  │  sections()     │                 │
│  │  processor() │  │                 │                 │
│  └──────────────┘  └─────────────────┘                 │
│                                                         │
│  ┌──────────────┐  ┌─────────────────┐                 │
│  │  /summarize  │  │  /insights      │                 │
│  │  BART model  │  │  keyword freq · │                 │
│  │  (HuggingFace│  │  pillars · align│                 │
│  │   Transformers│ │  · methods · …  │                 │
│  └──────────────┘  └─────────────────┘                 │
│                                                         │
│  BART model loaded ONCE at startup — lives in memory   │
└─────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Single-file frontend
The entire UI lives in `index.html`. There are no build tools (no webpack, no npm). This keeps the project easy to run — just open it in a browser or serve it via FastAPI's `FileResponse`. The `script.js` file exists as a placeholder for future utilities.

### 2. Model loaded once at startup
Loading `facebook/bart-large-cnn` takes several seconds and uses significant RAM. It is imported globally when `pipeline.py` starts, before any requests are accepted. Every subsequent request reuses the same tokenizer and model objects. This is the standard pattern for ML inference servers.

```python
# pipeline.py — top of file, runs once
MODEL_NAME = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(MODEL_NAME)
model     = BartForConditionalGeneration.from_pretrained(MODEL_NAME)
```

### 3. Stateless API
The server itself is stateless — it does not store any document or session data between requests. All pipeline state (extracted text, sections, summaries) lives in the browser's JavaScript `state` object. This means you can restart the server mid-session and re-submit data without loss.

### 4. Four-endpoint pipeline (not one)
Each processing stage is a separate endpoint rather than a single "process everything" call. This design choice:
- Lets the frontend show intermediate results at each step
- Allows students to test individual stages with curl or Postman
- Keeps each function small and testable in isolation

### 5. No database
Academic papers are ephemeral inputs — there is no requirement to store them. Temp files created during PDF upload are deleted immediately after text extraction. The only persistence is the JSON downloads the user can trigger at steps 3 and 4.

---

## Request/Response Flow

```
Browser                          FastAPI
  │                                 │
  │──── POST /extract (PDF) ───────►│
  │                                 │  tempfile.NamedTemporaryFile
  │                                 │  fitz.open(pdf_path)
  │                                 │  universal_processor()
  │◄─── { text: string } ──────────│
  │                                 │
  │──── POST /preprocess (JSON) ───►│
  │                                 │  extract_sections()
  │◄─── { preprocessed_text,        │
  │       sections: [...] } ────────│
  │                                 │
  │──── POST /summarize (JSON) ────►│
  │                                 │  split_text_into_chunks()
  │                                 │  summarize_chunk() × N (BART)
  │◄─── { summaries: [...] } ───────│
  │                                 │
  │──── POST /insights (JSON) ─────►│
  │                                 │  _score_keywords()
  │                                 │  _score_groups()
  │                                 │  _classify_school()
  │                                 │  _alignment()
  │                                 │  _detect_methods()
  │                                 │  _trending()
  │                                 │  _cross_disciplinary()
  │◄─── { keywords, pillars,        │
  │       school_of_thought,        │
  │       alignment, methods,       │
  │       trending,                 │
  │       cross_disciplinary } ─────│
```

---

## File Map

```
project root/
├── pipeline.py      ← FastAPI server + all NLP logic
├── index.html       ← Complete SPA (HTML + CSS + JS in one file)
├── script.js        ← Placeholder for future external utilities
├── req.md           ← Original milestone requirements
├── venv/            ← Python virtual environment (not committed)
└── docs/            ← This documentation
```
