# PDF Extraction

**File:** `pipeline.py`
**Function:** `universal_processor(pdf_path: str) -> str`
**Endpoint:** `POST /extract`

---

## What This Stage Does

Takes a PDF file path, uses PyMuPDF to read every page, extracts all text blocks, trims the content to the academically relevant portions (Abstract → References), cleans leftover noise, and returns a single clean string.

---

## Step-by-Step Walkthrough

### 1. Opening the PDF

```python
import fitz  # PyMuPDF

doc = fitz.open(pdf_path)
full_text = ""
```

`fitz` is the Python binding for MuPDF, a high-performance PDF rendering library written in C. `fitz.open()` loads the PDF into memory and returns a `Document` object. See [PyMuPDF documentation](./pymupdf.md).

### 2. Iterating Pages and Extracting Blocks

```python
for page in doc:
    blocks = page.get_text("blocks", sort=True)
    for b in blocks:
        full_text += b[4] + "\n"
```

`page.get_text("blocks", sort=True)` returns a list of text blocks. Each block `b` is a tuple:
```
(x0, y0, x1, y1, "text content", block_no, block_type)
```
Index `4` is the text content. `sort=True` returns blocks in reading order (top-to-bottom, left-to-right), which is critical for multi-column academic papers.

**Why blocks instead of `page.get_text("text")`?**
The `"blocks"` mode gives you layout-aware grouping. It respects columns and avoids merging a right-column paragraph with a left-column one just because they are at the same vertical position.

Reference: [PyMuPDF — Page.get_text()](https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text)

---

### 3. Trimming to Abstract

```python
start_match = re.search(r'\n\s*ABSTRACT', full_text, re.IGNORECASE)
if start_match:
    full_text = full_text[start_match.start():]
```

Academic papers typically have title, author names, affiliations, and keywords before the Abstract. This content adds noise without adding meaning. By finding the first occurrence of "ABSTRACT" (case-insensitive) and discarding everything before it, we keep only the body of the paper.

**`re.IGNORECASE`** ensures this matches "Abstract", "ABSTRACT", "abstract", etc.

---

### 4. Trimming at References

```python
for marker in [r'\n\s*REFERENCES', r'\n\s*BIBLIOGRAPHY', r'\n\s*LITERATURE CITED']:
    end_match = list(re.finditer(marker, full_text, re.IGNORECASE))
    if end_match:
        full_text = full_text[:end_match[-1].start()]
        break
```

Everything after the references section is irrelevant to the content (it is just citations and appendices). The code uses `re.finditer` and takes the **last** match — this is important because "References" might appear in headings like "2.3 Related References" before the final bibliography.

**Three markers are tried in order:** `REFERENCES`, `BIBLIOGRAPHY`, `LITERATURE CITED` — covering the different conventions used across academic disciplines.

---

### 5. Noise Removal

```python
# Remove in-text citations like (Smith & Jones 2019) or (Author et al., 2021)
full_text = re.sub(r'\([A-Za-z\s&,.]+ \d{4}\)', '', full_text)

# Remove URLs
full_text = re.sub(r'https?://\S+', '', full_text)

# Remove DOI strings
full_text = re.sub(r'DOI: \S+', '', full_text)

# Normalise whitespace
clean_text = " ".join(full_text.split())
```

| Regex | Removes | Example |
|-------|---------|---------|
| `\([A-Za-z\s&,.]+ \d{4}\)` | In-text citations | `(Zhang et al. 2021)` |
| `https?://\S+` | URLs | `https://arxiv.org/abs/2301.00000` |
| `DOI: \S+` | DOI strings | `DOI: 10.1145/3442188` |
| `" ".join(full_text.split())` | Extra whitespace | `"word  \n  word"` → `"word word"` |

The final `" ".join(full_text.split())` is a Python idiom for collapsing all whitespace (spaces, tabs, newlines) into single spaces. It is equivalent to `re.sub(r'\s+', ' ', text).strip()`.

---

## Handling Temporary Files

The upload endpoint wraps the processing in a `try/finally` to guarantee the temp file is always deleted:

```python
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    tmp.write(await file.read())
    tmp_path = tmp.name

try:
    text = universal_processor(tmp_path)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
finally:
    os.unlink(tmp_path)   # ← always runs, even if an exception occurred
```

**Why `delete=False`?** On Windows, `NamedTemporaryFile` locks the file while it is open. PyMuPDF needs to open it separately. Setting `delete=False` and manually calling `os.unlink()` works on all platforms.

---

## Limitations

| Limitation | Explanation |
|------------|-------------|
| Scanned PDFs | If the PDF is a scanned image (not text-based), `get_text()` returns empty strings. OCR would be required (e.g. Tesseract). |
| Complex layouts | Two-column papers with figures can sometimes have block ordering issues. `sort=True` mitigates this. |
| Non-standard headings | If a paper uses "Summary" instead of "Abstract", the trim step won't find a start marker and uses the full text. |
| Embedded tables | Table cells are extracted as raw text blocks, which can appear garbled. |

---

## References

- [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/)
- [Python `re` module](https://docs.python.org/3/library/re.html)
- [Python `tempfile` module](https://docs.python.org/3/library/tempfile.html)
