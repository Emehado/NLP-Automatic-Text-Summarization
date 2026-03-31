# Preprocessing

**File:** `pipeline.py`
**Functions:** `extract_sections()`, `split_text_into_chunks()`
**Endpoint:** `POST /preprocess`

---

## What This Stage Does

Takes the raw extracted text and organises it into meaningful structural units. Specifically:
1. Optionally converts text to lowercase
2. Detects and extracts named sections (Abstract, Introduction, Discussion, Conclusion)
3. Returns each section's name, word count, and text

This output is used both for display (the accordion UI) and as the input to the summarisation stage.

---

## Section Detection Deep Dive

### The Target Sections

```python
SECTION_PATTERNS = [
    ("ABSTRACT",     r"\bABSTRACT\b"),
    ("INTRODUCTION", r"\bINTRODUCTION\b"),
    ("DISCUSSION",   r"\b(?:DISCUSSION|FINDINGS|RESULTS)\b"),
    ("CONCLUSION",   r"\b(?:CONCLUSIONS?|CONCLUDING REMARKS|SUMMARY)\b"),
]
```

Four canonical sections are targeted, each with flexible regex patterns:

| Label | Matched Headings |
|-------|-----------------|
| `ABSTRACT` | "ABSTRACT" only |
| `INTRODUCTION` | "INTRODUCTION" only |
| `DISCUSSION` | "DISCUSSION", "FINDINGS", or "RESULTS" |
| `CONCLUSION` | "CONCLUSION", "CONCLUSIONS", "CONCLUDING REMARKS", "SUMMARY" |

**`\b` word boundaries** prevent partial matches — for example, `\bABSTRACT\b` will not match "ABSTRACTING" or "ABSTRACT-BASED".

**Non-capturing groups** `(?:...)` allow alternation (`|`) without creating a capture group, which is slightly more efficient.

---

### The Stop Pattern

Once a section's start is found, the algorithm needs to know where it ends. This is handled by `STOP_PATTERN`:

```python
STOP_PATTERN = re.compile(
    r"(?:\n\s*\d+\.(?:\d+\.?)?\s+[A-Z]"
    r"|ABSTRACT|INTRODUCTION|LITERATURE REVIEW"
    r"|METHODOLOGY|METHOD|DATA"
    r"|RESULTS|FINDINGS|DISCUSSION"
    r"|CONCLUSION|REFERENCES|BIBLIOGRAPHY|APPENDIX)",
    re.IGNORECASE,
)
```

This pattern matches any of:
- A numbered heading like `2.` or `2.1` followed by a capital letter (covers headings like "2.1 Related Work")
- Any known section heading name

The section content is sliced from its start to the next position where `STOP_PATTERN` matches.

---

### The Extraction Algorithm

```python
def extract_sections(text: str) -> list[dict]:
    sections = []
    for label, start_regex in SECTION_PATTERNS:
        match = re.search(start_regex, text, re.IGNORECASE)
        if not match:
            continue

        content_start = match.start()
        search_from   = match.end() + 50          # skip past the heading itself
        tail          = text[search_from:]
        stop_match    = STOP_PATTERN.search(tail)

        section_text = text[content_start : search_from + stop_match.start()] \
                       if stop_match else text[content_start:]

        cleaned = section_text.strip()
        if cleaned:
            sections.append({
                "name":  label,
                "words": len(cleaned.split()),
                "text":  cleaned,
            })

    return sections
```

**Line-by-line explanation:**

| Step | Code | What it does |
|------|------|-------------|
| 1 | `re.search(start_regex, text)` | Find the section heading anywhere in the text |
| 2 | `content_start = match.start()` | Record the character position of the heading |
| 3 | `search_from = match.end() + 50` | Skip 50 chars past the heading (past the heading text itself) |
| 4 | `tail = text[search_from:]` | Take everything after the heading |
| 5 | `STOP_PATTERN.search(tail)` | Find the next section heading in the tail |
| 6 | Slice | Cut from `content_start` to the stop position |
| 7 | `len(cleaned.split())` | Count words by splitting on whitespace |

**Fallback:** If `stop_match` is `None` (no subsequent heading found), the section runs to the end of the text.

---

### Fallback: No Sections Found

```python
if opts.sectioning:
    sections = extract_sections(processed)
    if not sections:
        sections = [{
            "name":  "FULL TEXT",
            "words": len(processed.split()),
            "text":  processed,
        }]
```

If `extract_sections` returns an empty list (no known headings were found — possible for non-standard papers or pre-processed text), the entire text is returned as a single section called `"FULL TEXT"`. This ensures the rest of the pipeline always receives at least one section.

---

## Text Chunking for Summarisation

```python
def split_text_into_chunks(text: str, max_words: int = 400) -> list[str]:
    words, chunks, chunk = text.split(), [], []
    for word in words:
        chunk.append(word)
        if len(chunk) >= max_words:
            chunks.append(" ".join(chunk))
            chunk = []
    if chunk:
        chunks.append(" ".join(chunk))
    return chunks
```

BART has a maximum input of 1024 tokens (roughly 750–900 words). To be safe, text is split at **400 words**. This function:
- Splits on whitespace (not sentences), so splits may occur mid-sentence
- Preserves word order exactly
- Uses a sliding accumulator pattern (common in streaming/chunking code)

**Why 400 words?** A word is typically 1–2 tokens after tokenisation. 400 words × 1.5 tokens/word ≈ 600 tokens, well within BART's 1024 limit with room for the summary output length.

---

## Lowercase Option

```python
processed = text.lower() if opts.lowercase else text
```

Lowercasing is optional and defaults to off (`false` in the API). It can be useful if downstream text analysis tools are case-sensitive, but BART works equally well with mixed-case text.

---

## References

- [Python `re` module — regular expression syntax](https://docs.python.org/3/library/re.html)
- [HuggingFace BART tokenizer max_length](https://huggingface.co/facebook/bart-large-cnn)
- [Pydantic BaseModel for request validation](https://docs.pydantic.dev/latest/)
