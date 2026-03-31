import os
import re
import tempfile
from transformers import BartTokenizer, BartForConditionalGeneration
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve index.html at root ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))


# ── Load BART model once at startup ───────────────────────────────────────────
MODEL_NAME = "facebook/bart-large-cnn"
print("Loading BART model...")
tokenizer = BartTokenizer.from_pretrained(MODEL_NAME)
model     = BartForConditionalGeneration.from_pretrained(MODEL_NAME)
print("Model loaded.\n")


# ══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def universal_processor(pdf_path: str) -> str:
    doc       = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        blocks = page.get_text("blocks", sort=True)
        for b in blocks:
            full_text += b[4] + "\n"

    # Trim: start at Abstract
    start_match = re.search(r'\n\s*ABSTRACT', full_text, re.IGNORECASE)
    if start_match:
        full_text = full_text[start_match.start():]

    # Trim: stop at References / Bibliography
    for marker in [r'\n\s*REFERENCES', r'\n\s*BIBLIOGRAPHY', r'\n\s*LITERATURE CITED']:
        end_match = list(re.finditer(marker, full_text, re.IGNORECASE))
        if end_match:
            full_text = full_text[:end_match[-1].start()]
            break

    # Clean noise
    full_text = re.sub(r'\([A-Za-z\s&,.]+ \d{4}\)', '', full_text)
    full_text = re.sub(r'https?://\S+', '', full_text)
    full_text = re.sub(r'DOI: \S+', '', full_text)
    clean_text = " ".join(full_text.split())

    return clean_text


SECTION_PATTERNS = [
    ("ABSTRACT",     r"\bABSTRACT\b"),
    ("INTRODUCTION", r"\bINTRODUCTION\b"),
    ("DISCUSSION",   r"\b(?:DISCUSSION|FINDINGS|RESULTS)\b"),
    ("CONCLUSION",   r"\b(?:CONCLUSIONS?|CONCLUDING REMARKS|SUMMARY)\b"),
]

STOP_PATTERN = re.compile(
    r"(?:\n\s*\d+\.(?:\d+\.?)?\s+[A-Z]"
    r"|ABSTRACT|INTRODUCTION|LITERATURE REVIEW"
    r"|METHODOLOGY|METHOD|DATA"
    r"|RESULTS|FINDINGS|DISCUSSION"
    r"|CONCLUSION|REFERENCES|BIBLIOGRAPHY|APPENDIX)",
    re.IGNORECASE,
)


def extract_sections(text: str) -> list[dict]:
    """Return a list of {name, words, text} dicts for each found section."""
    sections = []
    for label, start_regex in SECTION_PATTERNS:
        match = re.search(start_regex, text, re.IGNORECASE)
        if not match:
            continue

        content_start = match.start()
        search_from   = match.end() + 50
        tail          = text[search_from:]
        stop_match    = STOP_PATTERN.search(tail)
        section_text  = text[content_start : search_from + stop_match.start()] \
                        if stop_match else text[content_start:]

        cleaned = section_text.strip()
        if cleaned:
            sections.append({
                "name":  label,
                "words": len(cleaned.split()),
                "text":  cleaned,
            })

    return sections


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


def summarize_chunk(text_chunk: str) -> str:
    inputs = tokenizer(text_chunk, return_tensors="pt", max_length=1024, truncation=True)
    ids    = model.generate(
        inputs["input_ids"],
        max_length=150,
        min_length=40,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True,
    )
    return tokenizer.decode(ids[0], skip_special_tokens=True)


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 1 — POST /extract
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Write upload to a temp file, process, then delete
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        text = universal_processor(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    finally:
        os.unlink(tmp_path)

    if not text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from this PDF.")

    return {"text": text}


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 2 — POST /preprocess
# ══════════════════════════════════════════════════════════════════════════════

class PreprocessOptions(BaseModel):
    lowercase:  Optional[bool] = False
    sectioning: Optional[bool] = True

class PreprocessRequest(BaseModel):
    text:    str
    options: Optional[PreprocessOptions] = PreprocessOptions()


@app.post("/preprocess")
async def preprocess(req: PreprocessRequest):
    text = req.text
    opts = req.options or PreprocessOptions()

    if not text.strip():
        raise HTTPException(status_code=422, detail="Text is empty.")

    # Apply lowercase if requested
    processed = text.lower() if opts.lowercase else text

    # Section extraction or single-block fallback
    if opts.sectioning:
        sections = extract_sections(processed)
        if not sections:
            # No headings found — return full text as one section
            sections = [{
                "name":  "FULL TEXT",
                "words": len(processed.split()),
                "text":  processed,
            }]
    else:
        sections = [{
            "name":  "FULL TEXT",
            "words": len(processed.split()),
            "text":  processed,
        }]

    return {
        "preprocessed_text": processed,
        "sections":          sections,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 3 — POST /summarize
# ══════════════════════════════════════════════════════════════════════════════

MIN_WORDS_TO_SUMMARIZE = 50

class SectionItem(BaseModel):
    name:  str
    words: int
    text:  str

class SummarizeRequest(BaseModel):
    sections: list[SectionItem]


@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    if not req.sections:
        raise HTTPException(status_code=422, detail="No sections provided.")

    # Combine all sections into one document, then summarize as a whole
    combined = " ".join(s.text.strip() for s in req.sections)
    total_words = len(combined.split())

    if total_words < MIN_WORDS_TO_SUMMARIZE:
        return {"summaries": [{"section": "Full Document", "summary": combined}]}

    try:
        chunks = split_text_into_chunks(combined, max_words=400)
        chunk_summaries = [summarize_chunk(c) for c in chunks]
        summary = " ".join(chunk_summaries)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")

    return {"summaries": [{"section": "Full Document", "summary": summary}]}


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 4 — POST /insights
# ══════════════════════════════════════════════════════════════════════════════

from collections import Counter

STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "this","that","these","those","it","its","we","our","they","their",
    "which","who","what","how","when","where","as","if","so","than","more",
    "also","both","each","other","such","into","through","during","before",
    "after","above","below","between","out","up","down","i","he","she","you",
    "not","no","can","all","about","over","while","then","there","here",
    "use","used","using","show","shows","shown","based","result","results",
    "study","paper","research","findings","however","therefore","thus",
    "proposed","presents","provide","provides","within","across","among",
}

# Domain keyword clusters for cross-disciplinary grouping
DOMAIN_CLUSTERS = {
    "NLP": ["language","text","word","sentence","translation","parsing",
            "semantic","syntax","corpus","token","embedding","nlp","lexical"],
    "Machine Learning": ["learning","neural","network","deep","training",
                         "classification","prediction","model","algorithm",
                         "feature","supervised","unsupervised","transformer"],
    "Data Science": ["data","dataset","analysis","statistics","visualization",
                     "preprocessing","sampling","annotation","evaluation","metrics"],
    "Social Science": ["social","society","behavior","community","culture",
                       "policy","human","interaction","perception","attitude"],
    "Education": ["education","student","teaching","curriculum","academic",
                  "knowledge","learning","literacy","classroom","assessment"],
}

# Research pillar keyword groups
PILLAR_GROUPS = {
    "Methodology":  ["method","methodology","approach","framework","procedure","design","strategy"],
    "Evaluation":   ["evaluation","performance","accuracy","precision","recall","benchmark","metric"],
    "Data":         ["data","dataset","corpus","sample","collection","annotation","preprocessing"],
    "Modelling":    ["model","architecture","network","layer","parameter","training","inference"],
    "Application":  ["application","system","implementation","deployment","tool","practice","real-world"],
}

APPLIED_SIGNALS      = ["implement","deploy","system","application","practice",
                         "experiment","real-world","tool","prototype","solution","develop"]
THEORETICAL_SIGNALS  = ["theory","theoretical","conceptual","framework","hypothesis",
                         "paradigm","propose","abstract","formal","principle","concept"]

METHOD_TERMS = {
    "Survey / Review":        ["survey","review","literature","systematic","meta-analysis"],
    "Experiment":             ["experiment","experimental","trial","controlled","laboratory"],
    "Qualitative":            ["qualitative","interview","observation","ethnograph","thematic"],
    "Quantitative":           ["quantitative","statistical","regression","correlation","measure"],
    "Case Study":             ["case study","case-study","case analysis","scenario"],
    "Simulation":             ["simulation","simulate","synthetic","generative","virtual"],
    "Deep Learning":          ["neural network","deep learning","transformer","fine-tun","pre-train"],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-z]{3,}\b', text.lower())


def _score_keywords(tokens: list[str], top_n: int = 20) -> list[dict]:
    counts = Counter(t for t in tokens if t not in STOPWORDS)
    total  = max(counts.most_common(1)[0][1], 1) if counts else 1
    return [
        {"word": word, "score": round(count / total, 2)}
        for word, count in counts.most_common(top_n)
    ]


def _score_groups(text: str, groups: dict) -> list[dict]:
    results = []
    for name, keywords in groups.items():
        hits = sum(len(re.findall(rf'\b{re.escape(k)}\b', text, re.IGNORECASE))
                   for k in keywords)
        results.append({"name": name, "score": hits})
    if not results:
        return results
    max_score = max(r["score"] for r in results) or 1
    for r in results:
        r["score"] = round((r["score"] / max_score) * 100)
    return sorted(results, key=lambda x: x["score"], reverse=True)


def _classify_school(tokens: list[str]) -> dict:
    counts = Counter(t for t in tokens if t not in STOPWORDS)
    top10  = {w for w, _ in counts.most_common(10)}

    empirical   = {"data","experiment","results","evidence","measure","observation","test"}
    theoretical = {"theory","model","framework","concept","hypothesis","formal","propose"}
    applied_kw  = {"system","implementation","application","deploy","tool","practice"}

    e = len(top10 & empirical)
    t = len(top10 & theoretical)
    a = len(top10 & applied_kw)

    if a >= e and a >= t:
        label = "Applied / Engineering"
        desc  = "The research is predominantly applied, focusing on building systems and practical implementations."
        tags  = ["Applied", "Engineering", "System Design"]
        cohesion = "Practice-Oriented"
    elif e >= t:
        label = "Empirical Research"
        desc  = "The research is driven by experimental evidence and quantitative observation."
        tags  = ["Empirical", "Data-Driven", "Evidence-Based"]
        cohesion = "Evidence-Oriented"
    else:
        label = "Theoretical / Conceptual"
        desc  = "The research centres on developing or refining theoretical frameworks and conceptual models."
        tags  = ["Theoretical", "Conceptual", "Model-Driven"]
        cohesion = "Theory-Oriented"

    return {"label": label, "cohesion": cohesion, "tags": tags, "description": desc}


def _alignment(text: str) -> dict:
    a = sum(len(re.findall(rf'\b{re.escape(k)}\b', text, re.IGNORECASE))
            for k in APPLIED_SIGNALS)
    t = sum(len(re.findall(rf'\b{re.escape(k)}\b', text, re.IGNORECASE))
            for k in THEORETICAL_SIGNALS)
    total = a + t or 1
    ap = round((a / total) * 100)
    th = 100 - ap
    if ap > 60:
        desc = "The body of work leans applied, with emphasis on practical systems and real-world deployment."
    elif th > 60:
        desc = "The body of work leans theoretical, centering on conceptual models and formal frameworks."
    else:
        desc = "The research is balanced between applied and theoretical contributions."
    return {"applied": ap, "theoretical": th, "description": desc}


def _detect_methods(text: str) -> list[dict]:
    hits = []
    for name, keywords in METHOD_TERMS.items():
        count = sum(len(re.findall(re.escape(k), text, re.IGNORECASE)) for k in keywords)
        if count:
            hits.append((name, count))
    if not hits:
        return [{"name": "General Analysis", "pct": 100}]
    total = sum(c for _, c in hits)
    return [{"name": n, "pct": round((c / total) * 100)} for n, c in
            sorted(hits, key=lambda x: x[1], reverse=True)]


def _trending(tokens: list[str]) -> list[dict]:
    counts   = Counter(t for t in tokens if t not in STOPWORDS and len(t) > 5)
    top5     = counts.most_common(5)
    trending = []
    for word, count in top5:
        trending.append({
            "name":        word.title(),
            "growth":      f"+{min(count * 10, 99)}%",
            "description": f"Appears frequently across the document ({count} occurrences).",
        })
    return trending


def _cross_disciplinary(tokens: list[str]) -> tuple[list[dict], str]:
    token_set = set(tokens)
    groups    = []
    matched_domains = []

    for domain, keywords in DOMAIN_CLUSTERS.items():
        matched = [k for k in keywords if k in token_set]
        if len(matched) >= 2:
            # Highlight the two most frequent matched keywords
            freq       = Counter(t for t in tokens if t in matched)
            highlights = [w for w, _ in freq.most_common(2)]
            groups.append({"department": domain, "tags": matched, "highlights": highlights})
            matched_domains.append(domain)

    if len(matched_domains) >= 2:
        insight = (f"The research spans {' and '.join(matched_domains[:2])}, "
                   f"suggesting cross-disciplinary relevance across these fields.")
    elif matched_domains:
        insight = f"The research is primarily rooted in {matched_domains[0]}."
    else:
        insight = "No strong cross-disciplinary signals detected in this document."

    return groups, insight


class SummaryItem(BaseModel):
    section: str
    summary: str

class InsightsRequest(BaseModel):
    summaries: list[SummaryItem]


@app.post("/insights")
async def insights(req: InsightsRequest):
    if not req.summaries:
        raise HTTPException(status_code=422, detail="No summaries provided.")

    combined = " ".join(s.summary for s in req.summaries)
    tokens   = _tokenize(combined)

    if not tokens:
        raise HTTPException(status_code=422, detail="Summaries contain no analysable text.")

    cross_disc, cross_insight = _cross_disciplinary(tokens)

    return {
        "keywords":               _score_keywords(tokens, top_n=20),
        "pillars":                _score_groups(combined, PILLAR_GROUPS),
        "school_of_thought":      _classify_school(tokens),
        "alignment":              _alignment(combined),
        "methods":                _detect_methods(combined),
        "trending":               _trending(tokens),
        "cross_disciplinary":     cross_disc,
        "cross_disciplinary_insight": cross_insight,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pipeline:app", host="0.0.0.0", port=8000, reload=True)
