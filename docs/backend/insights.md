# Insights Engine

**File:** `pipeline.py`
**Endpoint:** `POST /insights`
**Key functions:** `_tokenize`, `_score_keywords`, `_score_groups`, `_classify_school`, `_alignment`, `_detect_methods`, `_trending`, `_cross_disciplinary`

---

## Overview

The insights stage analyses the generated summaries using classical NLP techniques — no ML model is involved here. It uses regular expressions, word frequency counting (`collections.Counter`), and hand-crafted keyword dictionaries to produce eight distinct outputs. All analysis runs on the **combined text** of all summaries.

```python
combined = " ".join(s.summary for s in req.summaries)
tokens   = _tokenize(combined)
```

---

## Tokenization

```python
def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-z]{3,}\b', text.lower())
```

This extracts all lowercase words of **3 or more characters**. One-letter and two-letter words (like "a", "an", "it", "of") are excluded because they are overwhelmingly stopwords. The pattern `\b[a-z]{3,}\b` uses:
- `\b` — word boundary anchors
- `[a-z]{3,}` — only lowercase alphabetic characters, minimum 3

The text is lowercased first so "Language" and "language" are treated as the same word.

---

## Stopword List

```python
STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    # … ~90 total words
    "use","used","using","show","shows","shown","based","result","results",
    "study","paper","research","findings","however","therefore","thus",
    "proposed","presents","provide","provides","within","across","among",
}
```

This is a domain-aware stopword list. In addition to standard English function words (the, and, or…), it includes common **academic paper words** like "study", "paper", "research", "proposed", "results", "findings" — words that appear in almost every research paper and are therefore not informative for distinguishing this paper from others.

This is a key NLP design decision: domain-specific stopwords often matter more than generic ones.

---

## 1. Keywords (`_score_keywords`)

**Goal:** Find the most frequently occurring meaningful words.

```python
def _score_keywords(tokens: list[str], top_n: int = 20) -> list[dict]:
    counts = Counter(t for t in tokens if t not in STOPWORDS)
    total  = max(counts.most_common(1)[0][1], 1) if counts else 1
    return [
        {"word": word, "score": round(count / total, 2)}
        for word, count in counts.most_common(top_n)
    ]
```

**Algorithm:**
1. Count each non-stopword token using `Counter`
2. Find the maximum count (the top word's frequency)
3. Normalise: `score = count / max_count`
4. Return top 20 words

**Result:** The most frequent word gets score `1.0`, all others are relative to it.

**Frontend rendering:** Words with score > 0.7 get the `large` CSS class (bigger pills), score < 0.4 get `small`, everything else is medium.

---

## 2. Research Pillars (`_score_groups`)

**Goal:** Measure how much the text covers each of five research dimensions.

```python
PILLAR_GROUPS = {
    "Methodology":  ["method","methodology","approach","framework","procedure","design","strategy"],
    "Evaluation":   ["evaluation","performance","accuracy","precision","recall","benchmark","metric"],
    "Data":         ["data","dataset","corpus","sample","collection","annotation","preprocessing"],
    "Modelling":    ["model","architecture","network","layer","parameter","training","inference"],
    "Application":  ["application","system","implementation","deployment","tool","practice","real-world"],
}
```

```python
def _score_groups(text: str, groups: dict) -> list[dict]:
    results = []
    for name, keywords in groups.items():
        hits = sum(len(re.findall(rf'\b{re.escape(k)}\b', text, re.IGNORECASE))
                   for k in keywords)
        results.append({"name": name, "score": hits})
    max_score = max(r["score"] for r in results) or 1
    for r in results:
        r["score"] = round((r["score"] / max_score) * 100)
    return sorted(results, key=lambda x: x["score"], reverse=True)
```

For each pillar group, it counts **all regex hits** across all keywords in that group, then normalises the scores so the highest group = 100.

**`re.escape(k)`** ensures keywords with special regex characters (like `"real-world"` containing `-`) are treated as literal strings.

**Frontend:** Rendered as an animated horizontal bar chart.

---

## 3. School of Thought (`_classify_school`)

**Goal:** Classify the research as Applied, Empirical, or Theoretical.

```python
empirical   = {"data","experiment","results","evidence","measure","observation","test"}
theoretical = {"theory","model","framework","concept","hypothesis","formal","propose"}
applied_kw  = {"system","implementation","application","deploy","tool","practice"}
```

```python
def _classify_school(tokens: list[str]) -> dict:
    counts = Counter(t for t in tokens if t not in STOPWORDS)
    top10  = {w for w, _ in counts.most_common(10)}

    e = len(top10 & empirical)
    t = len(top10 & theoretical)
    a = len(top10 & applied_kw)

    if a >= e and a >= t:   label = "Applied / Engineering"
    elif e >= t:            label = "Empirical Research"
    else:                   label = "Theoretical / Conceptual"
    …
```

This uses **set intersection** on the top 10 most frequent words. The idea: the most frequent domain-specific words in a paper reveal its primary orientation. A paper about building systems will have words like "implementation", "deploy", "system" in its top-10; an empirical paper will have "data", "experiment", "results".

**Why top 10 only?** Using all tokens would dilute the signal — every paper mentions "theory" and "data" somewhere. The top 10 words are the most distinctive vocabulary of that particular text.

---

## 4. Research Alignment (`_alignment`)

**Goal:** Quantify the applied vs. theoretical balance as a percentage.

```python
APPLIED_SIGNALS     = ["implement","deploy","system","application","practice",
                        "experiment","real-world","tool","prototype","solution","develop"]
THEORETICAL_SIGNALS = ["theory","theoretical","conceptual","framework","hypothesis",
                        "paradigm","propose","abstract","formal","principle","concept"]

def _alignment(text: str) -> dict:
    a = sum(len(re.findall(rf'\b{re.escape(k)}\b', text, re.IGNORECASE))
            for k in APPLIED_SIGNALS)
    t = sum(len(re.findall(rf'\b{re.escape(k)}\b', text, re.IGNORECASE))
            for k in THEORETICAL_SIGNALS)
    total = a + t or 1
    ap = round((a / total) * 100)
    th = 100 - ap
```

Unlike school-of-thought which uses top-N frequency, alignment counts every occurrence of signal words across the full text. This makes it a more sensitive continuous measurement rather than a categorical classification.

**`a + t or 1`** is a Python idiom for avoiding division by zero: if both `a` and `t` are 0, use 1 as the denominator.

---

## 5. Method Detection (`_detect_methods`)

**Goal:** Identify what research methodology the paper uses.

```python
METHOD_TERMS = {
    "Survey / Review":  ["survey","review","literature","systematic","meta-analysis"],
    "Experiment":       ["experiment","experimental","trial","controlled","laboratory"],
    "Qualitative":      ["qualitative","interview","observation","ethnograph","thematic"],
    "Quantitative":     ["quantitative","statistical","regression","correlation","measure"],
    "Case Study":       ["case study","case-study","case analysis","scenario"],
    "Simulation":       ["simulation","simulate","synthetic","generative","virtual"],
    "Deep Learning":    ["neural network","deep learning","transformer","fine-tun","pre-train"],
}
```

```python
def _detect_methods(text: str) -> list[dict]:
    hits = []
    for name, keywords in METHOD_TERMS.items():
        count = sum(len(re.findall(re.escape(k), text, re.IGNORECASE)) for k in keywords)
        if count:
            hits.append((name, count))
    total = sum(c for _, c in hits)
    return [{"name": n, "pct": round((c / total) * 100)} for n, c in
            sorted(hits, key=lambda x: x[1], reverse=True)]
```

Note: `"Deep Learning"` keywords include partial strings like `"fine-tun"` — this matches both "fine-tuning" and "fine-tuned" without requiring two separate entries (a form of stemming by prefix).

---

## 6. Trending Terms (`_trending`)

**Goal:** Surface the top 5 high-frequency domain-specific words.

```python
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
```

The filter `len(t) > 5` removes short common words that escaped the stopword list. Longer words (6+ chars) tend to be more domain-specific (e.g. "learning", "sentence", "training").

**`growth` field:** This is a display proxy — `count × 10` capped at 99%. It is not a real growth metric (there is no historical data to compare to). It is used to make the UI's trending list look meaningful. This is an honest trade-off: real trend detection would require comparing against a corpus of previous papers.

---

## 7. Cross-Disciplinary Detection (`_cross_disciplinary`)

**Goal:** Identify which academic domains the paper touches.

```python
DOMAIN_CLUSTERS = {
    "NLP":              ["language","text","word","sentence","translation","parsing",
                         "semantic","syntax","corpus","token","embedding","nlp","lexical"],
    "Machine Learning": ["learning","neural","network","deep","training","classification",
                         "prediction","model","algorithm","feature","supervised","unsupervised","transformer"],
    "Data Science":     ["data","dataset","analysis","statistics","visualization",
                         "preprocessing","sampling","annotation","evaluation","metrics"],
    "Social Science":   ["social","society","behavior","community","culture","policy",
                         "human","interaction","perception","attitude"],
    "Education":        ["education","student","teaching","curriculum","academic",
                         "knowledge","learning","literacy","classroom","assessment"],
}
```

```python
def _cross_disciplinary(tokens: list[str]) -> tuple[list[dict], str]:
    token_set = set(tokens)
    for domain, keywords in DOMAIN_CLUSTERS.items():
        matched = [k for k in keywords if k in token_set]
        if len(matched) >= 2:   # must match at least 2 keywords to count
            freq       = Counter(t for t in tokens if t in matched)
            highlights = [w for w, _ in freq.most_common(2)]
            groups.append({"department": domain, "tags": matched, "highlights": highlights})
```

**Using `token_set`** (a Python `set`) instead of `list` for the `in` lookup makes each check O(1) instead of O(n), which is important when the keyword lists are long.

**Threshold of 2 matches** prevents a domain being flagged just because one incidental word appeared. Two matches indicates genuine relevance.

**Highlights** are the two most frequently occurring matched keywords — these are highlighted in the UI's cross-disciplinary grid (black background instead of white).

---

## References

- [Python `collections.Counter`](https://docs.python.org/3/library/collections.html#collections.Counter)
- [Python `re` module](https://docs.python.org/3/library/re.html)
- [TF-IDF — the standard approach to keyword scoring](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) *(this project uses simpler raw frequency, not TF-IDF)*
- [Research methodology types](https://research-methodology.net/research-methodology/research-approach/)
