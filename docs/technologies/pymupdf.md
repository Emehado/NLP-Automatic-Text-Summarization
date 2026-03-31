# PyMuPDF (fitz)

**PyMuPDF** is the Python binding for MuPDF, a lightweight PDF and XPS viewer written in C. In Python it is imported as `fitz` (a historical naming convention from the underlying Artifex codebase).

References:
- [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/)
- [MuPDF — Artifex](https://mupdf.com/)

---

## Why `fitz` as the Import Name?

When you install `pymupdf` and write `import fitz`, you might find this confusing. "Fitz" was the name of an older, unrelated PDF library that PyMuPDF was once compatible with. The name stuck. All PyMuPDF code uses `import fitz`.

```python
import fitz  # PyMuPDF
```

---

## Core Objects

### `fitz.Document`

Represents an open PDF file.

```python
doc = fitz.open(pdf_path)
```

Key properties:
- `len(doc)` — number of pages
- `doc[i]` — access page by index
- `for page in doc:` — iterate pages

### `fitz.Page`

Represents a single page.

```python
page = doc[0]  # first page
```

Key methods used in this project:
- `page.get_text("blocks", sort=True)` — extract text as a list of blocks

---

## Understanding Text Blocks

`page.get_text("blocks", sort=True)` returns a list of tuples:

```python
[
    (x0, y0, x1, y1, "text content", block_no, block_type),
    …
]
```

| Index | Type | Meaning |
|-------|------|---------|
| 0 | float | Left x-coordinate of the block |
| 1 | float | Top y-coordinate of the block |
| 2 | float | Right x-coordinate of the block |
| 3 | float | Bottom y-coordinate of the block |
| 4 | str | The text content |
| 5 | int | Block number |
| 6 | int | Block type (0=text, 1=image) |

The project only uses index 4 (the text):
```python
for b in blocks:
    full_text += b[4] + "\n"
```

### `sort=True`

Without `sort=True`, blocks are returned in the order they appear in the PDF's internal structure, which may not match reading order. `sort=True` sorts blocks by their position: top-to-bottom, then left-to-right within the same vertical band.

This is critical for multi-column academic papers. Without it, you might get:

```
Left column paragraph 1
Right column paragraph 1    ← wrong: mixed columns
Left column paragraph 2
Right column paragraph 2
```

With `sort=True` you get proper reading order:
```
Left column paragraph 1
Left column paragraph 2     ← correct: finishes left column
Right column paragraph 1
Right column paragraph 2
```

Note: `sort=True` uses a heuristic that works well for standard two-column layouts but may still produce issues with complex PDF structures (tables, sidebars, footnotes).

---

## Text Extraction Modes

`get_text()` supports several modes:

| Mode | Returns | Best for |
|------|---------|---------|
| `"text"` | Simple string | Single-column docs |
| `"blocks"` | List of block tuples | Multi-column, layout-aware |
| `"words"` | List of individual words with positions | Word-level analysis |
| `"dict"` | Detailed nested dict | Fine-grained font/style access |
| `"html"` | HTML string | Web display |
| `"rawdict"` | Low-level dict | Debugging |

This project uses `"blocks"` for the layout-awareness.

---

## PDF Types: Text vs. Scanned

There are two fundamental types of PDFs:

**Text-based PDFs** (also called "born-digital"): the text is stored directly in the PDF as characters. PyMuPDF can extract this immediately. Most academic papers downloaded from arXiv, journal websites, or created from Word/LaTeX are text-based.

**Scanned PDFs**: the pages are images of physical documents. There is no text layer. `get_text()` returns empty strings. Extracting text from scanned PDFs requires OCR (Optical Character Recognition). Common tools: Tesseract (`pytesseract`), AWS Textract, Google Cloud Document AI.

**This project does not support scanned PDFs.** If a user uploads a scanned PDF, the `universal_processor` will return an empty string and the endpoint will return a `422` error:
```python
if not text.strip():
    raise HTTPException(status_code=422, detail="No text could be extracted from this PDF.")
```

---

## Performance

PyMuPDF is notably fast compared to pure-Python PDF libraries:
- Written in C (wrapped with Python bindings)
- Processes a typical 10-page PDF in milliseconds
- Handles PDFs with hundreds of pages without significant slowdown

For context: `pdfminer.six` (a pure-Python alternative) may take several seconds on the same document.

---

## Temporary File Pattern

The upload endpoint uses a temporary file rather than passing bytes directly to PyMuPDF:

```python
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    tmp.write(await file.read())
    tmp_path = tmp.name
```

**Why not pass bytes directly?** `fitz.open()` can accept bytes via `fitz.open(stream=bytes_data, filetype="pdf")`, which would avoid the temp file. The temp file approach was used here for clarity and to match the original batch-script design of the code. Both approaches work.

---

## References

- [PyMuPDF — API reference for Page.get_text()](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text)
- [PyMuPDF — Text extraction guide](https://pymupdf.readthedocs.io/en/latest/how-to-open-a-file.html)
- [Tesseract OCR (for scanned PDFs)](https://github.com/tesseract-ocr/tesseract)
