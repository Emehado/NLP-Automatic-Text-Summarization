# Backend Overview

The backend is a single Python file: `pipeline.py`. It serves both the API and the frontend UI.

---

## Server Setup

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**FastAPI** is a modern Python web framework. It automatically generates interactive API documentation at `/docs` (Swagger UI) and `/redoc`. See [FastAPI & Pydantic](../technologies/fastapi.md).

**CORS middleware** allows the browser to call the API even when the page is loaded from a different origin (e.g. if you open `index.html` directly as a `file://` URL instead of via `http://localhost:8000`). `allow_origins=["*"]` permits requests from any origin — this is appropriate for a local development tool but would need tightening in production.

---

## Serving the Frontend

```python
@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))
```

When a browser navigates to `http://localhost:8000`, FastAPI responds with the `index.html` file. This means one `uvicorn` process serves both the API and the UI — no separate web server is needed.

`BASE_DIR` is resolved relative to `pipeline.py` itself:
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
```
This ensures the path works correctly regardless of which directory you launch the server from.

---

## Module Structure

`pipeline.py` is organised into clearly separated sections:

| Lines | Section | Purpose |
|-------|---------|---------|
| 1–19 | Imports & app setup | FastAPI, CORS, model imports |
| 22–26 | UI route | Serve `index.html` at `/` |
| 29–34 | Model loading | Load BART once at startup |
| 40–68 | `universal_processor()` | PDF → clean text |
| 70–111 | Section patterns + `extract_sections()` | Text → named sections |
| 114–136 | `split_text_into_chunks()` + `summarize_chunk()` | BART chunking & inference |
| 141–163 | `POST /extract` | Milestone 1 endpoint |
| 166–210 | `POST /preprocess` | Milestone 2 endpoint |
| 213–247 | `POST /summarize` | Milestone 3 endpoint |
| 250–466 | `POST /insights` | Milestone 4 endpoint + all analysis helpers |
| 469–475 | Entry point | `uvicorn.run(...)` |

---

## Starting the Server

The file includes a standard Python entry point:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pipeline:app", host="0.0.0.0", port=8000, reload=True)
```

- `"pipeline:app"` — tells uvicorn to find the `app` object inside `pipeline.py`
- `host="0.0.0.0"` — listens on all network interfaces (not just localhost), useful for testing from another device on the same network
- `reload=True` — watches for file changes and restarts automatically during development

You can also start it directly with:
```bash
uvicorn pipeline:app --reload
```

---

## Error Handling Pattern

Every endpoint follows the same pattern:

```python
@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    try:
        # … processing …
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    finally:
        os.unlink(tmp_path)  # always clean up temp file
```

- `400 Bad Request` — invalid input (wrong file type, empty text)
- `422 Unprocessable Entity` — input is structurally correct but semantically invalid
- `500 Internal Server Error` — unexpected exception during processing

FastAPI also automatically returns `422` for requests that fail Pydantic model validation (e.g. missing required fields), without you writing any extra code.

---

## Auto-Generated API Docs

Because FastAPI uses Python type annotations and Pydantic models, it generates interactive documentation automatically. Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These pages let you test any endpoint directly in your browser — useful for debugging individual pipeline stages.
