# Data Flow — From PDF to Insights

This document traces exactly what happens to a research paper as it passes through each stage of the pipeline.

---

## Stage 1 — PDF Upload & Text Extraction

**Trigger:** User clicks "Extract Text" after selecting a PDF.

**Frontend action:**
```js
const formData = new FormData();
formData.append("file", state.pdfFile);
const res = await fetch(`${API_BASE}/extract`, { method: "POST", body: formData });
const data = await res.json();   // { text: string }
state.extractedText = data.text;
```

**Backend action (`universal_processor`):**

```
PDF bytes received via UploadFile
  │
  ▼
Written to a temp file (tempfile.NamedTemporaryFile)
  │
  ▼
fitz.open(pdf_path)  — PyMuPDF opens the PDF
  │
  ▼
For each page:
  page.get_text("blocks", sort=True)
  Concatenate block[4] (the text field of each block)
  │
  ▼
Trim start:  find first occurrence of "ABSTRACT" → discard everything before
Trim end:    find last "REFERENCES" / "BIBLIOGRAPHY" → discard everything after
  │
  ▼
Noise removal (regex):
  • In-text citations   e.g.  (Smith et al. 2021)
  • URLs                e.g.  https://arxiv.org/…
  • DOI strings         e.g.  DOI: 10.1145/…
  │
  ▼
" ".join(full_text.split())  — collapse all whitespace to single spaces
  │
  ▼
Return clean string
```

**What is stored on the client:** `state.extractedText` (plain string).

---

## Stage 2 — Preprocessing & Section Detection

**Trigger:** User clicks "Process Text".

**Frontend sends:**
```json
{
  "text": "ABSTRACT This paper proposes…",
  "options": {
    "lowercase": true,
    "sectioning": true
  }
}
```

**Backend action (`extract_sections`):**

```
Receive preprocessed text
  │
  ├─ lowercase option → text.lower()
  │
  └─ sectioning option → extract_sections(text)
       │
       For each target section label:
       ["ABSTRACT", "INTRODUCTION", "DISCUSSION", "CONCLUSION"]
         │
         ├─ regex search for label in text
         ├─ record start position
         ├─ look 50 chars ahead, then search for the STOP_PATTERN
         │    (next heading or section marker)
         └─ slice text[content_start : stop_position]
       │
       Return list of { name, words, text } dicts
       │
       If no sections found: return full text as one "FULL TEXT" section
```

**STOP_PATTERN** (what it looks for to end a section):
```
numbered heading (e.g. "2.1 Methodology")
ABSTRACT · INTRODUCTION · LITERATURE REVIEW · METHODOLOGY
METHOD · DATA · RESULTS · FINDINGS · DISCUSSION
CONCLUSION · REFERENCES · BIBLIOGRAPHY · APPENDIX
```

**Frontend stores:** `state.sections` (array of objects), renders an accordion UI.

---

## Stage 3 — BART Summarization

**Trigger:** User clicks "Generate Summaries".

**Frontend sends:**
```json
{
  "sections": [
    { "name": "ABSTRACT", "words": 150, "text": "…" },
    { "name": "INTRODUCTION", "words": 400, "text": "…" }
  ]
}
```

**Backend action:**

```
Combine all section texts into one document string
  │
  Count total words
  │
  If total_words < 50:
    return the raw text as-is (too short for BART)
  │
  split_text_into_chunks(combined, max_words=400)
    → break into chunks of ≤ 400 words
    → preserves word boundaries (no mid-word splits)
  │
  For each chunk:
    summarize_chunk(chunk)
      │
      tokenizer(chunk, max_length=1024, truncation=True)
        → convert words to token IDs
      │
      model.generate(
        max_length=150,
        min_length=40,
        length_penalty=2.0,   ← penalises short summaries
        num_beams=4,          ← beam search explores 4 candidates
        early_stopping=True   ← stop when all beams hit EOS token
      )
      │
      tokenizer.decode(ids, skip_special_tokens=True)
        → convert token IDs back to human-readable text
  │
  Join all chunk summaries into one string
  │
  Return { summaries: [{ section: "Full Document", summary: "…" }] }
```

**Why one combined summary?** All sections are merged before summarisation. BART was trained on news articles (CNN/DailyMail), where the entire article context helps produce a coherent summary. Summarising each section separately and concatenating the results tends to produce repetitive or disconnected output.

**Frontend stores:** `state.summaries`. Renders summary cards. Enables "Download JSON".

---

## Stage 4 — Insights Analysis

**Trigger:** Automatic when user navigates to Step 4 (if summaries exist).

**Frontend sends:**
```json
{
  "summaries": [
    { "section": "Full Document", "summary": "…" }
  ]
}
```

**Backend combines all summary text, then runs 7 analysis functions in sequence:**

### 4a. Keywords (`_score_keywords`)
```
tokenize combined text  →  re.findall(r'\b[a-z]{3,}\b', text.lower())
remove stopwords (built-in list of ~90 common English words)
Counter(tokens).most_common(20)
normalize: score = count / max_count  (so top word = 1.0)
return [{ word, score }]
```

### 4b. Research Pillars (`_score_groups`)
```
For each pillar group (Methodology, Evaluation, Data, Modelling, Application):
  count total regex hits of all keywords in that group
normalize: max_group_score = 100
return [{ name, score }] sorted descending
```

### 4c. School of Thought (`_classify_school`)
```
take top-10 most frequent words
count overlaps with three keyword sets:
  empirical   = { data, experiment, results, evidence, measure, … }
  theoretical = { theory, model, framework, concept, hypothesis, … }
  applied     = { system, implementation, application, deploy, tool, … }

if applied ≥ empirical AND applied ≥ theoretical → "Applied / Engineering"
elif empirical ≥ theoretical                      → "Empirical Research"
else                                              → "Theoretical / Conceptual"
```

### 4d. Alignment (`_alignment`)
```
count occurrences of APPLIED_SIGNALS words
count occurrences of THEORETICAL_SIGNALS words
applied_pct = applied / (applied + theoretical) × 100
```

### 4e. Methods (`_detect_methods`)
```
for each method category (Survey, Experiment, Qualitative, Quantitative,
                          Case Study, Simulation, Deep Learning):
  count keyword hits
return as percentage share of total hits
```

### 4f. Trending (`_trending`)
```
filter tokens to length > 5 (longer words are more domain-specific)
Counter → top 5
"growth" field = min(count × 10, 99)%  (a proxy metric for display)
```

### 4g. Cross-Disciplinary (`_cross_disciplinary`)
```
for each domain cluster (NLP, Machine Learning, Data Science,
                         Social Science, Education):
  find matched keywords in the token set
  if ≥ 2 keywords matched → include this domain
  highlight top-2 most frequent matched keywords

if ≥ 2 domains matched → generate "spans X and Y" insight string
```

**Frontend renders:** keyword cloud (size-weighted pills), pillar bar chart, school of thought card, alignment percentage bar, methods bar chart, trending list, cross-disciplinary network grid.

---

## End-to-End Data Summary

| Stage | Input | Output | Stored in |
|-------|-------|--------|-----------|
| Extract | PDF file | Plain text string | `state.extractedText` |
| Preprocess | Text + options | Sections array | `state.sections` |
| Summarize | Sections array | Summaries array | `state.summaries` |
| Insights | Summaries array | Insights object | Rendered to DOM only |
