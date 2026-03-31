# BART Model — Deep Dive

**Model:** `facebook/bart-large-cnn`
**Task:** Abstractive text summarisation
**Paper:** [BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation (Lewis et al., 2020)](https://arxiv.org/abs/1910.13461)

---

## What is BART?

BART (**B**idirectional and **A**uto-**R**egressive **T**ransformers) is a transformer-based sequence-to-sequence model developed by Facebook AI (now Meta AI). It belongs to the same family as T5 and has a similar architecture to the original Transformer (Vaswani et al., 2017).

BART was pre-trained using a **denoising** objective: the model is trained to reconstruct original text from corrupted versions. Corruption techniques include:
- Token masking (like BERT)
- Token deletion
- Text infilling (replacing spans with single mask tokens)
- Sentence permutation
- Document rotation

This makes BART an excellent foundation for generation tasks like summarisation, translation, and question answering.

---

## Architecture

```
Input text
    │
    ▼
┌──────────────────────────────────────┐
│           ENCODER (Bidirectional)    │
│                                      │
│  Token embeddings                    │
│  + Positional embeddings             │
│         │                            │
│  12 × Transformer encoder layers     │
│  (self-attention → feed-forward)     │
│         │                            │
│  Context-rich hidden states          │
└──────────────────────────────────────┘
    │
    ▼ (encoder-decoder cross-attention)
┌──────────────────────────────────────┐
│           DECODER (Autoregressive)   │
│                                      │
│  12 × Transformer decoder layers     │
│  (self-attention → cross-attention   │
│   → feed-forward)                    │
│         │                            │
│  One token generated at a time       │
│  Each token conditions on all        │
│  previous tokens + encoder output    │
└──────────────────────────────────────┘
    │
    ▼
Generated summary tokens → decoded text
```

**BART-large** has:
- 12 encoder layers + 12 decoder layers
- 16 attention heads
- 1024 hidden dimension
- ~406 million parameters

---

## How Summarisation Works

### Step 1: Tokenisation

```python
inputs = tokenizer(text_chunk, return_tensors="pt", max_length=1024, truncation=True)
```

The BartTokenizer converts words into **subword tokens** using Byte-Pair Encoding (BPE). BPE splits rare words into smaller pieces:
- "summarization" → `["summar", "ization"]`
- "NLP" → `["NLP"]` (common enough to be one token)

The vocabulary has ~50,000 entries. Each word maps to 1–4 tokens on average.

**Maximum 1024 tokens** is BART's architectural limit — its positional embeddings only go up to position 1024. Longer inputs are truncated.

### Step 2: Encoding

The tokenised input is passed through the encoder's 12 transformer layers. Each layer applies:
1. **Multi-head self-attention**: every token attends to every other token bidirectionally — the encoder can see the full input context at once
2. **Feed-forward network**: a two-layer fully connected network applied position-wise
3. **Layer normalisation + residual connections**

The result is a sequence of **contextualised hidden states** — each position holds a vector that encodes that token's meaning in context.

### Step 3: Decoding with Beam Search

```python
ids = model.generate(
    inputs["input_ids"],
    max_length=150,
    min_length=40,
    length_penalty=2.0,
    num_beams=4,
    early_stopping=True,
)
```

The decoder generates tokens one at a time, autoregressively (each token conditions on all previously generated tokens). This project uses **beam search** to produce higher-quality output than greedy decoding.

#### How Beam Search Works

Instead of always choosing the single highest-probability next token (greedy), beam search keeps `num_beams=4` candidate sequences:

```
Step 1: Start with <s> token
        Compute probability of all ~50,000 next tokens
        Keep top 4:
          Beam 1: <s> "This"    (prob 0.31)
          Beam 2: <s> "The"     (prob 0.28)
          Beam 3: <s> "A"       (prob 0.15)
          Beam 4: <s> "In"      (prob 0.10)

Step 2: For each beam, compute all possible next tokens
        Keep top 4 overall (by cumulative log-probability):
          Beam 1: <s> "This" "paper"  (prob 0.31 × 0.42 = 0.130)
          Beam 2: <s> "The"  "study"  (prob 0.28 × 0.44 = 0.123)
          …

… continue until all beams produce </s> (end of sequence)

Final: return the beam with highest cumulative probability
```

Beam search explores a wider space of possible sequences than greedy decoding, producing more fluent and complete summaries at the cost of more computation.

#### Length Penalty (`length_penalty=2.0`)

Without length penalty, beam search tends to prefer shorter sequences (they have fewer tokens to accumulate probability mass). `length_penalty=2.0` divides the cumulative score by `length^2.0`, strongly penalising short sequences and pushing the model toward longer, more informative summaries.

Formula: `score = log_prob_sum / (sequence_length ^ length_penalty)`

A value of 1.0 gives no penalty. Values > 1.0 favour longer sequences.

### Step 4: Decoding Tokens to Text

```python
tokenizer.decode(ids[0], skip_special_tokens=True)
```

The generated token IDs are converted back to a string. `ids[0]` selects the first (and only) batch item. `skip_special_tokens=True` removes `<s>`, `</s>`, and `<pad>` tokens.

---

## Why `bart-large-cnn`?

BART comes in several variants:

| Model | Parameters | Trained on |
|-------|------------|-----------|
| `bart-base` | 139M | Denoising pre-training only |
| `bart-large` | 406M | Denoising pre-training only |
| `bart-large-cnn` | 406M | Pre-trained then fine-tuned on CNN/DailyMail |
| `bart-large-xsum` | 406M | Pre-trained then fine-tuned on XSum (more abstractive) |

`bart-large-cnn` was fine-tuned on the CNN/DailyMail dataset — a collection of 300,000+ news article/highlight pairs. This fine-tuning teaches BART the specific task of summarisation: identify the key information, rephrase it in fewer words.

**CNN/DailyMail summaries** are extractive-leaning (they often use sentences similar to the article). This makes `bart-large-cnn` good at producing faithful, conservative summaries — suitable for academic papers where accuracy matters.

`bart-large-xsum` (trained on BBC XSum) produces shorter, more abstractive summaries that sometimes take more creative liberties — less suitable for research paper summarisation.

---

## ROUGE Score Context

ROUGE (Recall-Oriented Understudy for Gisting Evaluation) is the standard metric for summarisation quality.

`facebook/bart-large-cnn` achieves on CNN/DailyMail:
- **ROUGE-1:** 44.16
- **ROUGE-2:** 21.28
- **ROUGE-L:** 40.90

These are state-of-the-art scores at time of publication. The scores measure n-gram overlap between the generated summary and reference summaries.

Reference: [ROUGE metric explained](https://en.wikipedia.org/wiki/ROUGE_(metric))

---

## References

- [Lewis et al. 2020 — BART paper (arXiv)](https://arxiv.org/abs/1910.13461)
- [HuggingFace — facebook/bart-large-cnn](https://huggingface.co/facebook/bart-large-cnn)
- [HuggingFace Transformers — Text generation strategies](https://huggingface.co/docs/transformers/generation_strategies)
- [Vaswani et al. 2017 — Attention is All You Need](https://arxiv.org/abs/1706.03762)
- [CNN/DailyMail dataset](https://huggingface.co/datasets/cnn_dailymail)
