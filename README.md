# NLP Automatic Text Summarization

A tool that takes an academic research PDF and turns it into a structured summary and research insights — powered by Facebook's BART AI model.

You upload a paper. It reads it, summarises it, and tells you the key themes, research methods, and how it fits across disciplines.

---

## What you need before starting

- A computer running **macOS** or **Windows**
- **Python 3.9 or newer** (free to download)
- An internet connection for the first setup (to download the AI model, ~1.6 GB)
- About **5 GB of free disk space**
- About **4 GB of free RAM**

> **Don't have Python?** Jump to the [Installing Python](#installing-python) section below.

---

## Quick start (Mac)

Open the **Terminal** app. You can find it by pressing `Cmd + Space` and typing "Terminal".

Then run these three commands, one at a time:

```bash
make install
```
```bash
make dev
```
```bash
make open
```

That's it. The app opens in your browser at `http://localhost:8000`.

---

## Quick start (Windows)

Open **Command Prompt** or **PowerShell**. You can find either by pressing the Windows key and typing their name.

Run these commands one at a time:

```bat
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn python-multipart transformers torch pymupdf pydantic
```

Then start the server:

```bat
venv\Scripts\uvicorn pipeline:app --reload
```

Open your browser and go to: **http://localhost:8000**

> Windows users: `make` is not built into Windows. The commands above do the same thing manually. See the [Windows section](#windows-step-by-step) below for full details.

---

## Installing Python

### Mac

1. Open Terminal (`Cmd + Space`, type "Terminal", press Enter)
2. Check if Python is already installed:
   ```bash
   python3 --version
   ```
   If you see something like `Python 3.11.4`, you're good. Skip to [Running the project (Mac)](#running-the-project-mac).

3. If not installed, download it from **https://www.python.org/downloads/**
   - Click the yellow "Download Python 3.x.x" button
   - Open the downloaded `.pkg` file and follow the installer

4. Confirm it worked:
   ```bash
   python3 --version
   ```

### Windows

1. Open Command Prompt (Windows key → type "cmd" → Enter)
2. Check if Python is already installed:
   ```bat
   python --version
   ```
   If you see `Python 3.x.x`, skip to [Running the project (Windows)](#windows-step-by-step).

3. If not installed, download it from **https://www.python.org/downloads/**
   - Click the yellow "Download Python 3.x.x" button
   - Run the installer
   - **Important:** On the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install

4. Close and reopen Command Prompt, then confirm:
   ```bat
   python --version
   ```

---

## Running the project (Mac)

### Step 1 — Navigate to the project folder

In Terminal, use `cd` to go into the project folder. For example:

```bash
cd Desktop/NLP-Automatic-Text-Summarization
```

> **Tip:** You can drag the folder from Finder into the Terminal window instead of typing the path.

### Step 2 — Install everything

```bash
make install
```

This creates a virtual environment (an isolated space for this project's packages) and installs all required libraries.

**This will take a few minutes.** You will see a lot of text scrolling — that is normal.

You only need to do this once.

### Step 3 — Start the server

```bash
make dev
```

You will see something like:

```
Loading BART model...
Model loaded.

INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**The first time you start the server**, it will download the AI model (~1.6 GB). This happens once — it is cached on your computer after that. Wait for "Model loaded." to appear before proceeding.

### Step 4 — Open the app

```bash
make open
```

Or just open your browser manually and go to **http://localhost:8000**.

### Stopping the server

Press `Ctrl + C` in the Terminal window.

---

## Running the project (Windows — step by step) {#windows-step-by-step}

### Step 1 — Open Command Prompt in the project folder

Option A — Navigate with `cd`:
```bat
cd Desktop\NLP-Automatic-Text-Summarization
```

Option B — In File Explorer, open the project folder, click the address bar at the top, type `cmd`, and press Enter. This opens Command Prompt already inside that folder.

### Step 2 — Create a virtual environment

```bat
python -m venv venv
```

A `venv` folder will appear in the project directory. This is your isolated Python environment.

### Step 3 — Activate the virtual environment

```bat
venv\Scripts\activate
```

Your prompt will change to show `(venv)` at the beginning:
```
(venv) C:\Users\YourName\Desktop\NLP-Automatic-Text-Summarization>
```

> If you see an error about "execution policy" in PowerShell, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then try the activate command again.

### Step 4 — Install everything

```bat
pip install fastapi uvicorn python-multipart transformers torch pymupdf pydantic
```

This will take several minutes. You will see packages being downloaded and installed.

You only need to do this once.

### Step 5 — Start the server

```bat
venv\Scripts\uvicorn pipeline:app --reload
```

Wait until you see:
```
Loading BART model...
Model loaded.

INFO:     Uvicorn running on http://0.0.0.0:8000
```

**The first time you run this**, the AI model (~1.6 GB) will be downloaded. This is a one-time download.

### Step 6 — Open the app

Open your browser and go to: **http://localhost:8000**

### Stopping the server

Press `Ctrl + C` in the Command Prompt window.

### Next time you want to run it (Windows)

You do not need to reinstall. Just:

```bat
venv\Scripts\activate
venv\Scripts\uvicorn pipeline:app --reload
```

---

## Using the app

Once the server is running and you are on **http://localhost:8000**, click **"Begin Pipeline"** and follow the four steps:

| Step | What to do | What happens |
|------|-----------|-------------|
| **1 — Extract** | Upload a research PDF, click "Extract Text" | The app reads the PDF and pulls out the text |
| **2 — Preprocess** | Click "Process Text" | The text is split into sections (Abstract, Introduction, etc.) |
| **3 — Summarize** | Click "Generate Summaries" | The AI writes a summary of the paper |
| **4 — Insights** | Happens automatically | You see keywords, research methods, themes, and more |

> **Step 3 is slow.** On most laptops it takes 1–3 minutes. This is normal — the AI model is doing heavy work. A loading spinner will show the whole time.

---

## Mac commands reference

| Command | What it does |
|---------|-------------|
| `make install` | First-time setup — creates venv and installs packages |
| `make dev` | Start the server with auto-reload (recommended during development) |
| `make run` | Start the server without auto-reload |
| `make open` | Open http://localhost:8000 in your browser |
| `make clean` | Remove temporary Python cache files |
| `make reset` | Delete the venv entirely (use if something is broken) |

After `make reset`, run `make install` again to start fresh.

---

## Troubleshooting

### "python3: command not found" (Mac) or "python is not recognized" (Windows)
Python is not installed or not on your PATH. Follow the [Installing Python](#installing-python) section.

### "make: command not found" (Mac)
Install Xcode Command Line Tools:
```bash
xcode-select --install
```

### The first startup is taking very long
The AI model is downloading for the first time (~1.6 GB). This is normal. Leave it running and wait for "Model loaded." to appear.

### "Address already in use" — port 8000 is busy
Something else is already using port 8000. Either:
- Stop the other process
- Or start on a different port:
  - **Mac:** `make dev PORT=8001`
  - **Windows:** `venv\Scripts\uvicorn pipeline:app --reload --port 8001`

  Then open **http://localhost:8001** instead.

### "No text could be extracted from this PDF"
The PDF is a scanned image, not a text-based document. Use a PDF downloaded from a journal website, arXiv, or created from Word or LaTeX. Scanned PDFs are not supported.

### The page loads but the API calls fail
Make sure the server is still running in your terminal. If it crashed, start it again with `make dev` (Mac) or the uvicorn command (Windows).

---

## Project structure

```
NLP-Automatic-Text-Summarization/
├── pipeline.py     ← the server and all AI logic (Python)
├── index.html      ← the entire frontend (HTML + CSS + JavaScript)
├── Makefile        ← task runner shortcuts (Mac/Linux)
├── script.js       ← placeholder for future JavaScript utilities
└── docs/           ← detailed technical documentation
```

---

## Detailed documentation

Full technical documentation for students and developers is in the [`docs/`](./docs/README.md) folder, covering:

- How the AI pipeline works
- How every API endpoint is built
- How the frontend is structured
- Deep dives into BART, FastAPI, and PyMuPDF
