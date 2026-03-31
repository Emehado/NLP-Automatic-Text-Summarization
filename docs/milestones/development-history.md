# Development History — Milestones

The project was built in four sequential milestones, each introducing one API endpoint and the corresponding frontend step. This incremental approach allowed the team to test each stage in isolation before building the next.

---

## Milestone 1 — FastAPI Server + `/extract`

**Goal:** Convert the original batch script into a live API server and implement PDF text extraction.

### What Was Built

- Created the FastAPI application with CORS middleware
- Loaded the BART model and tokenizer once at server startup (not per-request)
- Implemented `POST /extract` — accepts a PDF upload, extracts text using `universal_processor()`, returns JSON
- Added `GET /` to serve `index.html` as the UI

### Key Technical Decision: Load Model at Startup

```python
# Runs once when the server starts
MODEL_NAME = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(MODEL_NAME)
model     = BartForConditionalGeneration.from_pretrained(MODEL_NAME)
```

Loading BART takes ~5–15 seconds and uses ~1.6 GB of RAM. If it were loaded per-request, every summarisation call would take an extra 15 seconds and potentially crash on memory-constrained machines. Loading once at startup is the standard pattern for ML inference APIs.

### How to Test
```bash
uvicorn pipeline:app --reload
# Open http://localhost:8000, upload a PDF, click "Extract Text"
```

---

## Milestone 2 — `/preprocess` Endpoint + Frontend Fixes

**Goal:** Implement text preprocessing and section detection, and fix two bugs in the frontend.

### What Was Built

- Implemented `POST /preprocess` with `lowercase` and `sectioning` options
- `extract_sections()` using regex patterns for ABSTRACT, INTRODUCTION, DISCUSSION, CONCLUSION
- `split_text_into_chunks()` for chunking long texts for BART

### Bugs Fixed

**Bug 1 — Broken `toggle-punct` reference:**
The frontend's `runPreprocessing()` was reading a toggle element with ID `toggle-punct` that did not exist in the HTML. This caused a `Cannot read properties of null` error. The element was removed from the function call.

**Bug 2 — Wrong option key name:**
The frontend was sending `remove_stopwords: true/false` to the API, but the backend expected `sectioning: true/false`. The frontend key was renamed to match the backend.

**Bug 3 — Duplicate functions in `script.js`:**
`script.js` contained copies of `runExtraction()` and `runSummarization()` that conflicted with the versions in `index.html`. The duplicates were removed.

### Architecture Insight

This milestone established the separation of concerns:
- `index.html` owns the UI and calls the API
- `pipeline.py` owns all NLP logic
- `script.js` is reserved for future external utilities

---

## Milestone 3 — `/summarize` Endpoint

**Goal:** Wire BART summarisation to the API and update the frontend to call it.

### What Was Built

- Implemented `POST /summarize` combining all sections and running BART
- Chunking strategy: 400 words per chunk to stay within BART's 1024-token limit
- Fallback: texts under 50 words are returned as-is (too short to summarise)
- Frontend: skeleton loading cards, real summary cards, "Download JSON" button

### Key Technical Decision: One Summary vs. Per-Section

The original milestone brief suggested summarising each section separately. After consideration, the implementation combines all sections into one document before summarisation. Reasons:
1. BART produces more coherent output with full document context
2. One summary is more useful than four disconnected section summaries
3. Reduces total inference time (4 separate calls vs. chunked one call)

### Performance Note

Summarisation is intentionally slow on CPU:
- A 3,000-word paper → ~7 chunks × 15–30s each = 2–3 minutes
- The frontend shows a spinner and skeleton UI throughout
- The spinner must remain visible — the `finally` block ensures it is always hidden when done

---

## Milestone 4 — `/insights` Endpoint

**Goal:** Implement the analysis layer that populates the Insights dashboard.

### What Was Built

Seven analysis functions:
1. `_score_keywords()` — top-20 word frequency with normalised 0–1 scores
2. `_score_groups()` — research pillar coverage (Methodology, Evaluation, Data, Modelling, Application)
3. `_classify_school()` — school of thought via top-10 word overlap
4. `_alignment()` — applied vs. theoretical signal word counting
5. `_detect_methods()` — research method detection (survey, experiment, deep learning, etc.)
6. `_trending()` — top-5 high-frequency domain terms
7. `_cross_disciplinary()` — cross-domain keyword clustering

Frontend updates:
- Keyword cloud (size-weighted pills)
- Animated bar charts for pillars and methods
- Alignment percentage bar with CSS transition
- Trending list with growth indicators
- Cross-disciplinary keyword network grid
- "Download Full Report" as `research-insights.json`

### Design Philosophy

All insight functions use classical NLP techniques (frequency counting, regex matching, set intersections) rather than additional ML models. This was a deliberate choice:
- **Speed:** Insights compute in milliseconds, not minutes
- **Transparency:** Students can read and understand exactly how each metric is calculated
- **No additional dependencies:** No extra models to download or load

The trade-off: the insights are keyword-based heuristics, not semantic analysis. They work well for research papers with standard academic vocabulary but could produce misleading results for highly specialised or non-English text.

### State of the Insights on First Entry

When the user navigates to Step 4, `goTo(3)` triggers `loadInsights()` automatically. If summaries exist (`state.summaries.length > 0`), it fires `POST /insights` immediately. If no summaries exist yet, `loadInsights()` returns early and the insights panels show their placeholder text.

---

## Summary of Milestones

| Milestone | Endpoint | Frontend Feature | Key Challenge |
|-----------|----------|-----------------|---------------|
| 1 | `POST /extract` | PDF upload, text preview | Model loading strategy |
| 2 | `POST /preprocess` | Section accordion, before/after compare | Regex section detection, bug fixes |
| 3 | `POST /summarize` | Summary cards, skeleton loading | Chunking strategy, slow inference UX |
| 4 | `POST /insights` | Full insights dashboard | Multiple analysis algorithms, animated charts |
