# Summarization

**File:** `pipeline.py`
**Functions:** `summarize_chunk()`, `split_text_into_chunks()`
**Endpoint:** `POST /summarize`
**Model:** `facebook/bart-large-cnn`

---

## What This Stage Does

Takes the preprocessed sections, combines them into a single document, and uses the BART transformer model to generate a coherent abstractive summary. The result is a single paragraph that captures the key ideas of the paper.

---

## The Summarization Function

```python
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
```

This function is the heart of the pipeline. Here is what each argument does:

### Tokenizer Parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `return_tensors="pt"` | `"pt"` | Return PyTorch tensors (needed by the model) |
| `max_length=1024` | 1024 | Hard limit on input tokens (BART's architectural limit) |
| `truncation=True` | True | If input exceeds 1024 tokens, silently cut it |

### Generation Parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| `max_length=150` | 150 tokens | Maximum summary length (~100–120 words) |
| `min_length=40` | 40 tokens | Minimum summary length (prevents one-sentence summaries) |
| `length_penalty=2.0` | 2.0 | Penalises short sequences — pushes the model toward longer summaries |
| `num_beams=4` | 4 | Beam search width — keeps 4 candidate sequences at each step |
| `early_stopping=True` | True | Stop when all beams reach an end-of-sequence token |

For a detailed explanation of BART and beam search, see [BART Model](../technologies/bart-model.md).

---

## The Full Summarization Flow

```python
@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    # 1. Combine all sections
    combined = " ".join(s.text.strip() for s in req.sections)
    total_words = len(combined.split())

    # 2. Short-circuit for very short texts
    if total_words < MIN_WORDS_TO_SUMMARIZE:  # MIN = 50
        return {"summaries": [{"section": "Full Document", "summary": combined}]}

    # 3. Chunk and summarize
    chunks = split_text_into_chunks(combined, max_words=400)
    chunk_summaries = [summarize_chunk(c) for c in chunks]
    summary = " ".join(chunk_summaries)

    # 4. Return
    return {"summaries": [{"section": "Full Document", "summary": summary}]}
```

### Why combine sections first?

Rather than summarising each section separately, all section texts are joined into one string before chunking. This is intentional:

1. **Context coherence:** BART produces more coherent output when it can see how ideas connect across the abstract, introduction, and discussion — rather than being forced to summarise each in isolation.
2. **Simpler output:** One summary card is easier to read than four disconnected ones.
3. **BART's training data:** BART was trained on full news articles, not article fragments. Giving it a full document plays to its strengths.

---

## Chunking Strategy

For long papers, the combined text might be 3,000–10,000 words. BART cannot process this in one call — it has a 1024-token input limit. The solution is to split into 400-word chunks:

```
combined text (e.g. 2000 words)
  │
  ├─ Chunk 1: words 1–400
  ├─ Chunk 2: words 401–800
  ├─ Chunk 3: words 801–1200
  ├─ Chunk 4: words 1201–1600
  └─ Chunk 5: words 1601–2000
       │
       Each chunk → summarize_chunk() → 40–150 token summary
       │
  " ".join(all chunk summaries) → final summary
```

**Trade-off:** Splitting at word boundaries (not sentence boundaries) can cause BART to receive a fragment sentence as the last input. In practice this rarely degrades output quality because BART is trained to handle truncated input.

---

## Performance Characteristics

| Hardware | Approximate time per chunk |
|----------|--------------------------|
| CPU (modern laptop) | 15–30 seconds |
| CPU (older or constrained) | 30–90 seconds |
| GPU (CUDA) | 1–3 seconds |

A typical 5,000-word paper produces ~12 chunks at 400 words each. On CPU this can take several minutes.

### Why is it so slow on CPU?

BART-large has **406 million parameters**. Each forward pass through the encoder and decoder requires hundreds of millions of floating-point multiplications. GPUs are designed for exactly this kind of parallel matrix arithmetic — CPUs process it sequentially. The `transformers` library will automatically use a GPU if CUDA is available.

---

## The `skip_special_tokens=True` Argument

```python
tokenizer.decode(ids[0], skip_special_tokens=True)
```

BART's vocabulary includes special tokens like `<s>` (start of sequence), `</s>` (end of sequence), and `<pad>`. These are needed during model computation but should not appear in the final text. `skip_special_tokens=True` strips them from the decoded output.

---

## References

- [HuggingFace — facebook/bart-large-cnn model card](https://huggingface.co/facebook/bart-large-cnn)
- [HuggingFace Transformers — Text generation](https://huggingface.co/docs/transformers/main_classes/text_generation)
- [HuggingFace Transformers — BartForConditionalGeneration](https://huggingface.co/docs/transformers/model_doc/bart)
- [Lewis et al. 2020 — BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation](https://arxiv.org/abs/1910.13461)
