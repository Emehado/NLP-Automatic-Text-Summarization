# API Reference

Base URL: `http://localhost:8000`

Auto-generated interactive docs available at: `http://localhost:8000/docs`

---

## `GET /`

Serves the frontend (`index.html`).

**Response:** HTML page (text/html)

---

## `POST /extract`

Accepts a PDF file, extracts and cleans text from it.

### Request

Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | A `.pdf` file |

### Response `200 OK`

```json
{
  "text": "ABSTRACT This paper proposes a novel approach to…"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Clean plain text extracted from the PDF. Begins at the Abstract and ends before the References section. In-text citations, URLs, and DOIs are removed. |

### Error Responses

| Status | Condition |
|--------|-----------|
| `400` | File does not have a `.pdf` extension |
| `422` | PDF was parsed but no text could be extracted |
| `500` | PyMuPDF threw an exception during processing |

### Example (curl)

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@my_paper.pdf"
```

---

## `POST /preprocess`

Takes raw text, optionally lowercases it, and splits it into named sections.

### Request

Content-Type: `application/json`

```json
{
  "text": "ABSTRACT This paper…",
  "options": {
    "lowercase": false,
    "sectioning": true
  }
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | — | The raw text to process |
| `options.lowercase` | boolean | No | `false` | Convert all text to lowercase before sectioning |
| `options.sectioning` | boolean | No | `true` | Split text into named sections. If `false`, returns full text as one section named `"FULL TEXT"` |

### Response `200 OK`

```json
{
  "preprocessed_text": "abstract this paper…",
  "sections": [
    {
      "name": "ABSTRACT",
      "words": 142,
      "text": "abstract this paper proposes…"
    },
    {
      "name": "INTRODUCTION",
      "words": 387,
      "text": "introduction natural language processing…"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `preprocessed_text` | string | The full text after applying the selected options |
| `sections` | array | List of detected sections |
| `sections[].name` | string | Section label: `ABSTRACT`, `INTRODUCTION`, `DISCUSSION`, `CONCLUSION`, or `FULL TEXT` |
| `sections[].words` | integer | Word count of this section |
| `sections[].text` | string | The text content of this section |

### Notes
- If no section headings are found, the response contains a single section with `name: "FULL TEXT"`.
- The same fallback occurs when `sectioning` is `false`.

### Error Responses

| Status | Condition |
|--------|-----------|
| `422` | `text` field is empty or whitespace-only |

### Example (curl)

```bash
curl -X POST http://localhost:8000/preprocess \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ABSTRACT This paper studies…",
    "options": { "lowercase": true, "sectioning": true }
  }'
```

---

## `POST /summarize`

Generates an abstractive summary of the provided sections using the BART model.

### Request

Content-Type: `application/json`

```json
{
  "sections": [
    {
      "name": "ABSTRACT",
      "words": 142,
      "text": "This paper proposes…"
    },
    {
      "name": "INTRODUCTION",
      "words": 387,
      "text": "Natural language processing has…"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sections` | array | Yes | Array of section objects from the `/preprocess` response |
| `sections[].name` | string | Yes | Section label |
| `sections[].words` | integer | Yes | Word count |
| `sections[].text` | string | Yes | Section text to summarize |

### Response `200 OK`

```json
{
  "summaries": [
    {
      "section": "Full Document",
      "summary": "This study presents a transformer-based approach…"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `summaries` | array | Always contains exactly one item (the full-document summary) |
| `summaries[].section` | string | Always `"Full Document"` |
| `summaries[].summary` | string | BART-generated abstractive summary |

### Performance Note
This endpoint is **slow** (30–90 seconds on CPU). The BART model runs heavy matrix multiplications. On a GPU-equipped machine it is much faster. The frontend shows a spinner during this wait.

### Error Responses

| Status | Condition |
|--------|-----------|
| `422` | `sections` array is empty |
| `500` | BART model threw an exception |

### Example (curl)

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "sections": [
      { "name": "ABSTRACT", "words": 100, "text": "This paper…" }
    ]
  }'
```

---

## `POST /insights`

Runs NLP analysis on the generated summaries to produce keywords, research pillar scores, school of thought classification, alignment, methods distribution, trending terms, and cross-disciplinary overlaps.

### Request

Content-Type: `application/json`

```json
{
  "summaries": [
    {
      "section": "Full Document",
      "summary": "This study applies deep learning to sentiment analysis…"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summaries` | array | Yes | The summaries array from `/summarize` |
| `summaries[].section` | string | Yes | Section label |
| `summaries[].summary` | string | Yes | Summary text to analyse |

### Response `200 OK`

```json
{
  "keywords": [
    { "word": "learning", "score": 1.0 },
    { "word": "sentiment", "score": 0.82 }
  ],
  "pillars": [
    { "name": "Modelling", "score": 100 },
    { "name": "Evaluation", "score": 72 },
    { "name": "Data", "score": 54 },
    { "name": "Methodology", "score": 40 },
    { "name": "Application", "score": 28 }
  ],
  "school_of_thought": {
    "label": "Applied / Engineering",
    "cohesion": "Practice-Oriented",
    "tags": ["Applied", "Engineering", "System Design"],
    "description": "The research is predominantly applied…"
  },
  "alignment": {
    "applied": 63,
    "theoretical": 37,
    "description": "The body of work leans applied…"
  },
  "methods": [
    { "name": "Deep Learning", "pct": 58 },
    { "name": "Quantitative", "pct": 42 }
  ],
  "trending": [
    {
      "name": "Sentiment",
      "growth": "+70%",
      "description": "Appears frequently across the document (7 occurrences)."
    }
  ],
  "cross_disciplinary": [
    {
      "department": "Machine Learning",
      "tags": ["learning", "neural", "training", "model"],
      "highlights": ["learning", "model"]
    }
  ],
  "cross_disciplinary_insight": "The research is primarily rooted in Machine Learning."
}
```

Full response field reference:

| Field | Type | Description |
|-------|------|-------------|
| `keywords` | array | Top 20 words by frequency. `score` is normalised 0–1 (1.0 = most frequent). |
| `pillars` | array | Research pillar scores normalised to 0–100. Sorted descending. |
| `school_of_thought.label` | string | One of: `"Applied / Engineering"`, `"Empirical Research"`, `"Theoretical / Conceptual"` |
| `school_of_thought.cohesion` | string | Short cohesion tag: `"Practice-Oriented"`, `"Evidence-Oriented"`, or `"Theory-Oriented"` |
| `school_of_thought.tags` | string[] | Three classification tags |
| `school_of_thought.description` | string | Human-readable explanation |
| `alignment.applied` | integer | Percentage of applied signal words (0–100) |
| `alignment.theoretical` | integer | `100 - applied` |
| `alignment.description` | string | One-sentence description of the balance |
| `methods` | array | Each detected method with its percentage share of total method hits |
| `trending` | array | Top 5 high-frequency terms (length > 5 chars). `growth` is a display-only proxy metric. |
| `cross_disciplinary` | array | Domains with ≥ 2 matched keywords. Each has `tags` (all matches) and `highlights` (top 2). |
| `cross_disciplinary_insight` | string | Auto-generated sentence about cross-domain connections |

### Error Responses

| Status | Condition |
|--------|-----------|
| `422` | `summaries` array is empty, or summary text produces no analysable tokens |

### Example (curl)

```bash
curl -X POST http://localhost:8000/insights \
  -H "Content-Type: application/json" \
  -d '{
    "summaries": [
      { "section": "Full Document", "summary": "This paper applies…" }
    ]
  }'
```
