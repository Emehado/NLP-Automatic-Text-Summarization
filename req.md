# NLP Pipeline — Requirements & Milestones

## Milestone 1 — FastAPI Server + `/extract` Endpoint

Convert `pipeline.py` from a batch script into a running FastAPI server and implement the first endpoint.

**Tasks**
- [x] Add FastAPI app with CORS middleware
- [x] Load BART tokenizer and model once at startup (reuse across requests)
- [x] Implement `POST /extract`
  - Accept PDF file upload via `UploadFile`
  - Save to a temp file, run `universal_processor()`, delete temp file
  - Return `{ "text": string }`
- [x] Serve `index.html` as a static file at `/` so the app is accessible at `http://localhost:8000`

**Test**
- Run `uvicorn pipeline:app --reload`
- Open `http://localhost:8000` — UI should load
- Upload a PDF, click "Extract Text" — extracted text should appear in the preview with word count


---

## Milestone 2 — `/preprocess` Endpoint + Frontend Bug Fixes

Implement the preprocessing endpoint and fix the two known bugs in `index.html`.

**Tasks**
- [x] Implement `POST /preprocess`
  - Accept `{ text: string, options: { lowercase: bool, sectioning: bool } }`
  - Apply `lowercase` if enabled
  - Run `extract_sections()` if `sectioning` is enabled; otherwise treat full text as one section
  - Return `{ "preprocessed_text": string, "sections": [{ "name": string, "words": int, "text": string }] }`
- [x] Fix `index.html` — remove broken `toggle-punct` reference from `runPreprocessing()`
- [x] Fix `index.html` — rename option key from `remove_stopwords` → `sectioning` to match the "Text Sectioning" toggle label
- [x] Clean up `script.js` — remove the two duplicate orphaned functions (`runExtraction`, `runSummarization`)

**Test**
- Complete Step 1 (extract a PDF)
- Click "Use Extracted Text" in Step 2, then click "Process Text"
- Before/After comparison should populate; Section Breakdown accordion should show extracted sections
- Toggle "Text Sectioning" off → full text returned as a single section
- Toggle "Lowercase" on → preprocessed text should be lowercase


---

## Milestone 3 — `/summarize` Endpoint

Wire up BART summarization to the API.

**Tasks**
- [x] Implement `POST /summarize`
  - Accept `{ "sections": [{ "name": string, "words": int, "text": string }] }`
  - For each section, run chunked BART summarization (`split_text_into_chunks` + `summarize_chunk`)
  - Return `{ "summaries": [{ "section": string, "summary": string }] }`
- [x] Add basic error handling — if a section is too short to summarize meaningfully, return the text as-is

**Test**
- Complete Steps 1 and 2
- Click "Generate Summaries" in Step 3
- Skeleton cards should appear while loading, then be replaced with real summary cards
- Each card should show the section name and its summary
- "Download JSON" button should produce a valid `summaries.json`
- Note: this step will be slow (~30–60s depending on hardware) — spinner must remain visible throughout


---

## Milestone 4 — `/insights` Endpoint

Implement the analysis layer that populates the Insights page (Step 4).

**Tasks**
- [x] Implement `POST /insights`
  - Accept `{ "summaries": [{ "section": string, "summary": string }] }`
  - Combine all summary text for analysis
  - **Keywords**: compute word frequency on combined text (exclude stopwords); normalize scores to 0–1; return top 20
  - **Pillars**: score occurrence of domain keyword groups (e.g. methodology, evaluation, model, data, framework) against the text
  - **School of Thought**: classify dominant theme based on top keywords (e.g. "Empirical", "Theoretical", "Mixed Methods"); include cohesion tag and description
  - **Alignment**: count applied vs theoretical signal words; return percentages and a one-sentence description
  - **Methods**: detect research method terms (survey, experiment, qualitative, quantitative, case study, simulation); return name + percentage share
  - **Trending**: return the top 5 high-frequency noun phrases or domain terms as trending topics with a short description each
  - **Cross-disciplinary**: cluster keywords into broad domain groups (NLP, ML, Social Science, Education, etc.); flag shared/highlighted terms
  - **Cross-disciplinary insight**: one-sentence narrative summary of cross-domain connections
- [x] Return the full structure the frontend expects (see comments in `loadInsights()` in `index.html`)

**Test**
- Complete Steps 1–3
- Navigate to Step 4 — all insight cards should populate
- Keyword cloud should show sized pills (large for high score, small for low)
- Bar charts should animate in
- Alignment bar should reflect applied vs theoretical split
- "Download Full Report" should produce a valid `research-insights.json`
