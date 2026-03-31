# FastAPI & Pydantic

**FastAPI** is the Python web framework used to build the API server. **Pydantic** is its data validation layer — FastAPI uses Pydantic under the hood for all request/response handling.

References:
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Pydantic documentation](https://docs.pydantic.dev/)

---

## Why FastAPI?

FastAPI was designed specifically for building APIs. Its key advantages used in this project:

1. **Automatic request validation** via Pydantic models
2. **Auto-generated API documentation** (Swagger UI at `/docs`)
3. **Async support** with `async def` handlers
4. **Type annotations as the API contract** — no separate schema files needed
5. **High performance** — one of the fastest Python web frameworks (benchmarks: [TechEmpower](https://www.techempower.com/benchmarks/))

---

## How FastAPI Uses Pydantic

Every `POST` endpoint defines its expected request body as a Pydantic `BaseModel`:

```python
from pydantic import BaseModel
from typing import Optional

class PreprocessOptions(BaseModel):
    lowercase:  Optional[bool] = False
    sectioning: Optional[bool] = True

class PreprocessRequest(BaseModel):
    text:    str
    options: Optional[PreprocessOptions] = PreprocessOptions()
```

When a request arrives at `POST /preprocess`, FastAPI:
1. Reads the JSON body
2. Validates it against `PreprocessRequest`
3. If validation fails → automatically returns `422 Unprocessable Entity` with a detailed error message
4. If validation passes → passes the typed `req` object to the handler function

You get this validation for free — no manual `if "text" not in body:` checks.

### Optional Fields with Defaults

```python
class PreprocessOptions(BaseModel):
    lowercase:  Optional[bool] = False   # default: False
    sectioning: Optional[bool] = True    # default: True
```

`Optional[bool]` means the field can be `None` or `bool`. The `= False`/`= True` provides a default. If the client omits `lowercase` from the JSON, Pydantic fills in `False`. If the client sends `"lowercase": null`, Pydantic accepts it (because of `Optional`).

---

## Async Handlers

```python
@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    # ... await file.read() ...
```

FastAPI supports both `def` (synchronous) and `async def` (asynchronous) handler functions. The `/extract` endpoint uses `async def` because `await file.read()` reads the uploaded file asynchronously.

**Why async?** Async I/O allows the server to handle other requests while waiting for slow I/O operations (disk reads, network requests). For this project, all four endpoints could technically be synchronous (BART inference blocks the event loop anyway), but `async def` is the FastAPI convention and is future-proof.

---

## Dependency Injection — `UploadFile` and `File`

```python
from fastapi import FastAPI, UploadFile, File, HTTPException

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
```

`File(...)` is a FastAPI **dependency** — it tells FastAPI this parameter should come from the request form data (not the JSON body). `...` means the field is required (no default).

`UploadFile` is FastAPI's wrapper for uploaded files. It exposes:
- `file.filename` — original filename
- `file.content_type` — MIME type
- `await file.read()` — read the file bytes asynchronously

---

## HTTPException

```python
from fastapi import HTTPException

raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
```

`HTTPException` is the FastAPI way to return error responses. When raised, FastAPI sends:
```json
{
  "detail": "Only PDF files are accepted."
}
```

The client sees the HTTP status code (400, 422, 500) and the detail message. This is much cleaner than manually building error response dictionaries.

---

## CORS Middleware

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**CORS** (Cross-Origin Resource Sharing) is a browser security mechanism that blocks requests from one origin (domain+port) to another. For example:
- If `index.html` is served at `http://localhost:8000` and makes a request to `http://localhost:8000/extract` → same origin, no CORS issue
- If `index.html` is opened as `file:///Users/…/index.html` and makes a request to `http://localhost:8000/extract` → different origin, CORS is needed

`allow_origins=["*"]` permits requests from any origin. In production this should be restricted to the specific domain of your frontend.

---

## Auto-Generated Documentation

FastAPI reads your Pydantic models and route decorators to generate OpenAPI documentation:

- **Swagger UI:** http://localhost:8000/docs
  Interactive — you can test endpoints directly in the browser
- **ReDoc:** http://localhost:8000/redoc
  Read-only, cleaner layout for reference

Example of what `/docs` shows for `POST /preprocess`:
- Request body schema (from `PreprocessRequest`)
- All required and optional fields with types and defaults
- Response schema
- "Try it out" button that sends a real request

---

## Uvicorn — The ASGI Server

FastAPI is an ASGI (Asynchronous Server Gateway Interface) application. It needs an ASGI server to run. The project uses **Uvicorn**:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pipeline:app", host="0.0.0.0", port=8000, reload=True)
```

Or from the terminal:
```bash
uvicorn pipeline:app --reload --host 0.0.0.0 --port 8000
```

| Flag | Meaning |
|------|---------|
| `pipeline:app` | Module `pipeline`, object `app` |
| `--reload` | Watch for file changes, auto-restart |
| `--host 0.0.0.0` | Listen on all network interfaces |
| `--port 8000` | Port number |

**WSGI vs ASGI:** Traditional Python web servers (Flask, Django) use WSGI (synchronous). FastAPI uses ASGI, which supports `async/await` and WebSockets. Uvicorn is the most common ASGI server.

Reference: [Uvicorn documentation](https://www.uvicorn.org/)
