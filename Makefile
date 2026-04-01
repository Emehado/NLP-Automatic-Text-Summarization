# ─────────────────────────────────────────────────────────────
# NLP Automatic Text Summarization — Task Runner
# Usage: make <command>
# ─────────────────────────────────────────────────────────────

PYTHON  := python3
VENV    := venv
PIP     := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
HOST    := 0.0.0.0
PORT    := 8000

.DEFAULT_GOAL := help

# ── help ──────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  NLP Pipeline — available commands:"
	@echo ""
	@echo "  make install    Install all dependencies into the venv"
	@echo "  make run        Start the server  (http://localhost:$(PORT))"
	@echo "  make dev        Start with auto-reload on file changes"
	@echo "  make open       Open the app in your default browser"
	@echo "  make clean      Remove __pycache__ and .pyc files"
	@echo "  make reset      Delete the venv (full clean slate)"
	@echo ""

# ── install ───────────────────────────────────────────────────
.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install fastapi uvicorn "python-multipart" transformers torch pymupdf pydantic
	@echo ""
	@echo "  Done. Run 'make dev' to start the server."

# ── run ───────────────────────────────────────────────────────
.PHONY: run
run:
	$(UVICORN) pipeline:app --host $(HOST) --port $(PORT)

# ── dev (auto-reload) ─────────────────────────────────────────
.PHONY: dev
dev:
	$(UVICORN) pipeline:app --host $(HOST) --port $(PORT) --reload

# ── open browser ──────────────────────────────────────────────
.PHONY: open
open:
	@open http://localhost:$(PORT) 2>/dev/null || \
	 xdg-open http://localhost:$(PORT) 2>/dev/null || \
	 start http://localhost:$(PORT) 2>/dev/null || \
	 echo "  Open http://localhost:$(PORT) in your browser"

# ── clean ─────────────────────────────────────────────────────
.PHONY: clean
clean:
	find . -type d -name __pycache__ -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc"             -not -path "./venv/*" -delete 2>/dev/null; true
	@echo "  Cleaned."

# ── reset (nuke venv) ─────────────────────────────────────────
.PHONY: reset
reset:
	rm -rf $(VENV)
	@echo "  venv removed. Run 'make install' to start fresh."
