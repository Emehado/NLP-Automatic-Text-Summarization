from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import fitz  # PyMuPDF
import re
import os
import shutil
from typing import List, Optional
from transformers import BartTokenizer, BartForConditionalGeneration

app = FastAPI()

# Enable CORS so your HTML file can talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD MODELS ONCE ---
MODEL_NAME = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(MODEL_NAME)
model = BartForConditionalGeneration.from_pretrained(MODEL_NAME)


input_folder = "input path"  # Folder where you uploaded the 10 PDFs
output_folder = "output path"  # Folder where you want to save the extracted text

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def universal_processor(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    
    # Step A: Layout-Aware Extraction (Handles columns automatically)
    for page in doc:
        blocks = page.get_text("blocks", sort=True)
        for b in blocks:
            full_text += b[4] + "\n"
    
    # Step B: Identify the Start (Find 'Abstract')
    # We look for 'Abstract' and keep everything after it.
    start_match = re.search(r'\n\s*ABSTRACT', full_text, re.IGNORECASE)
    if start_match:
        full_text = full_text[start_match.start():]

    # Step C: Identify the End (Find 'References')
    # We search from the bottom up to find the final bibliography
    end_markers = [r'\n\s*REFERENCES', r'\n\s*BIBLIOGRAPHY', r'\n\s*LITERATURE CITED']
    for marker in end_markers:
        end_match = list(re.finditer(marker, full_text, re.IGNORECASE))
        if end_match:
            # Take the very last occurrence of the word 'References'
            full_text = full_text[:end_match[-1].start()]
            break

    # Step D: Deep Clean Noise
    # 1. Remove in-text citations like (Damoah, 2021) or (Damoah et al. 2020)
    full_text = re.sub(r'\([A-Za-z\s&,.]+ \d{4}\)', '', full_text)
    
    # 2. Remove standard journal footers (URLs and DOIs)
    full_text = re.sub(r'https?://\S+', '', full_text)
    full_text = re.sub(r'DOI: \S+', '', full_text)
    
    # 3. Flatten extra whitespace and newlines
    clean_text = " ".join(full_text.split())
    
    return clean_text

# --- RUN THE LOOP ---
for filename in os.listdir(input_folder):
    if filename.endswith(".pdf"):
        print(f"Processing {filename}...")
        try:
            cleaned_content = universal_processor(os.path.join(input_folder, filename))
            
            # Save as .txt
            txt_name = filename.replace(".pdf", ".txt")
            with open(os.path.join(output_folder, txt_name), "w", encoding="utf-8") as f:
                f.write(cleaned_content)
        except Exception as e:
            print(f"Could not process {filename}: {e}")

print("\n--- ALL PAPERS CONVERTED AND CLEANED ---")









# Prepare the text for summarization
import os
import re

INPUT_FOLDER  = "input path here"  # Folder where you saved the cleaned .txt files
OUTPUT_FOLDER = "output path here"  # Folder to save the extracted sections (will be created if it doesn't exist)

SECTIONS = [
    ("ABSTRACT",      r"\bABSTRACT\b"),
    ("INTRODUCTION",  r"\bINTRODUCTION\b"),
    ("DISCUSSION",    r"\b(?:DISCUSSION|FINDINGS|RESULTS)\b"),
    ("CONCLUSION",    r"\b(?:CONCLUSIONS?|CONCLUDING REMARKS|SUMMARY)\b"),
]

STOP_PATTERN = re.compile(
    r"(?:\n\s*\d+\.(?:\d+\.?)?\s+[A-Z]"
    r"|ABSTRACT|INTRODUCTION|LITERATURE REVIEW"
    r"|METHODOLOGY|METHOD|DATA"
    r"|RESULTS|FINDINGS|DISCUSSION"
    r"|CONCLUSION|REFERENCES|BIBLIOGRAPHY|APPENDIX)",
    re.IGNORECASE,
)

# ── EXTRACTION ────────────────────────────────────────────────────────────────
def extract_sections(text: str, filename: str) -> str:
    """Extract target sections from a single document."""
    chunks = []

    for label, start_regex in SECTIONS:
        match = re.search(start_regex, text, re.IGNORECASE)

        if not match:
            print(f"  ⚠️  [{filename}] Section not found: {label}")
            continue

        # Start just before the heading; skip past heading + buffer to avoid
        # the heading itself re-triggering the stop pattern
        content_start = match.start()
        search_from   = match.end() + 50
        tail          = text[search_from:]

        stop_match = STOP_PATTERN.search(tail)
        section_text = text[content_start : search_from + stop_match.start()] \
                       if stop_match else text[content_start:]

        cleaned = section_text.strip()
        if cleaned:
            chunks.append(f"{'─' * 60}\n{label}\n{'─' * 60}\n{cleaned}")

    return "\n\n".join(chunks)


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    # Validate input folder
    if not os.path.isdir(INPUT_FOLDER):
        print(f"❌  Input folder not found:\n    {INPUT_FOLDER}")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".txt")]

    if not txt_files:
        print(f"⚠️  No .txt files found in:\n    {INPUT_FOLDER}")
        return

    print(f"📂  Found {len(txt_files)} file(s). Starting extraction...\n")

    saved, skipped = 0, 0

    for filename in sorted(txt_files):
        input_path  = os.path.join(INPUT_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"SECTIONS_{filename}")

        print(f"🔍  Processing: {filename}")

        try:
            with open(input_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            result = extract_sections(content, filename)

            if result.strip():
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"  ✅  Saved → SECTIONS_{filename}")
                saved += 1
            else:
                print(f"  ⏭️  Skipped (no sections extracted)")
                skipped += 1

        except Exception as e:
            print(f"  ❌  Error reading {filename}: {e}")
            skipped += 1

    print(f"\n{'═' * 50}")
    print(f"  Done!  Saved: {saved}  |  Skipped: {skipped}")
    print(f"  Output folder: {OUTPUT_FOLDER}")
    print(f"{'═' * 50}")


if __name__ == "__main__":
    main()












# Text Summary (BART Text Summarizer)


import os
from transformers import BartTokenizer, BartForConditionalGeneration

# ── Step 1: Set your folder paths ───────────────────────────
INPUT_FOLDER  = "input path here"  # Folder where you saved the cleaned .txt files
OUTPUT_FOLDER = "output path here"  # Folder to save the summaries (will be created if it doesn't exist)

# ── Step 2: Create output folder if it doesn't exist ────────
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    print(f"Created output folder: {OUTPUT_FOLDER}")

# ── Step 3: Load BART model and tokenizer ───────────────────
# force_download=True ensures a fresh download (fixes corruption)
print("Loading BART model... (fresh download, may take a few minutes)")

MODEL_NAME = "facebook/bart-large-cnn"

tokenizer = BartTokenizer.from_pretrained(
    MODEL_NAME,
    force_download=True       # Forces a clean re-download
)

model = BartForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    force_download=True,      # Forces a clean re-download
    ignore_mismatched_sizes=True  # Skips size-mismatch errors
)

print("Model loaded successfully!\n")

# ── Step 4: Split long text into chunks ─────────────────────
# BART handles ~1024 tokens max, so we chunk long documents

def split_text_into_chunks(text, max_words=400):
    """Splits text into smaller chunks of max_words each."""
    words  = text.split()
    chunks = []
    chunk  = []

    for word in words:
        chunk.append(word)
        if len(chunk) >= max_words:
            chunks.append(" ".join(chunk))
            chunk = []

    if chunk:                       # Save the final leftover chunk
        chunks.append(" ".join(chunk))

    return chunks


# ── Step 5: Summarize a single chunk ────────────────────────

def summarize_chunk(text_chunk):
    """Tokenizes and summarizes one chunk of text."""
    inputs = tokenizer(
        text_chunk,
        return_tensors="pt",
        max_length=1024,
        truncation=True
    )

    summary_ids = model.generate(
        inputs["input_ids"],
        max_length=150,
        min_length=40,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )

    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


# ── Step 6: Find all .txt files ─────────────────────────────

txt_files = [f for f in sorted(os.listdir(INPUT_FOLDER)) if f.endswith(".txt")]
print(f"Found {len(txt_files)} .txt file(s) to summarize.\n")

# ── Step 7: Loop through each file ──────────────────────────

for filename in txt_files:
    print(f"Processing: {filename}")

    input_path = os.path.join(INPUT_FOLDER, filename)

    with open(input_path, "r", encoding="utf-8") as f:
        full_text = f.read()

    # Split into chunks
    chunks = split_text_into_chunks(full_text, max_words=400)
    print(f"  → Split into {len(chunks)} chunk(s)")

    # Summarize each chunk
    all_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"  → Summarizing chunk {i + 1} of {len(chunks)}...")
        all_summaries.append(summarize_chunk(chunk)) 

    # Join all chunk summaries
    final_summary = " ".join(all_summaries)

    # Save summary to output folder
    output_filename = filename.replace(".txt", "_summary.txt")
    output_path     = os.path.join(OUTPUT_FOLDER, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"FILE: {filename}\n")
        f.write("=" * 50 + "\n")
        f.write(final_summary + "\n")

    print(f"  ✓ Saved: {output_path}\n")

# ── Done ─────────────────────────────────────────────────────
print("=" * 50)
print(f"All done! {len(txt_files)} file(s) summarized.")
print(f"Check the '{OUTPUT_FOLDER}' folder for your results.")
