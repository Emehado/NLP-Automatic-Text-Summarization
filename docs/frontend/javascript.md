# JavaScript Logic

All JavaScript lives in the `<script>` block at the bottom of `index.html` (~550 lines). This document explains every functional area.

---

## State Object

```js
let state = {
    currentStep:      0,
    pdfFile:          null,
    extractedText:    "",
    preprocessedText: "",
    sections:         [],
    summaries:        [],
    isDark:           false,
};
```

This is the single source of truth for all application data. Key points:
- It is a plain JavaScript object — no framework, no reactive system
- All API responses write into this object
- All render functions read from this object
- The state is lost on page refresh (no persistence)

---

## File Handling

### Drag and Drop

```js
function handleDragOver(e, id) {
    e.preventDefault();
    document.getElementById(id).classList.add("drag-over");
}
function handleDragLeave(id) {
    document.getElementById(id).classList.remove("drag-over");
}
function handleDrop(e, id, type) {
    e.preventDefault();
    document.getElementById(id).classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (!file) return;
    processFile(file, type);
}
```

`e.preventDefault()` in `handleDragOver` is required — without it the browser would navigate to the dropped file. The `drag-over` CSS class changes the border colour to give visual feedback.

### File Input (Click to Browse)

```js
function handleFileSelect(e, type) {
    const file = e.target.files[0];
    if (file) processFile(file, type);
}
```

Both drag-and-drop and click-to-browse call `processFile()` with the same `File` object.

### Processing the File

```js
function processFile(file, type) {
    if (type === "pdf") {
        state.pdfFile = file;
        document.getElementById("file-name-1").textContent = file.name;
        document.getElementById("file-chip-1").style.display = "flex";
        document.getElementById("step1-status").innerHTML =
            '<div class="status-dot active"></div> File Loaded';
    }
    if (type === "txt") {
        const reader = new FileReader();
        reader.onload = (e) => {
            state.extractedText = e.target.result;
            showNotification("Text file loaded");
        };
        reader.readAsText(file);
    }
}
```

For PDFs: the `File` object is stored in `state.pdfFile`. It is not read yet — reading happens when the user clicks "Extract Text" and the file is sent to the backend.

For `.txt` files: `FileReader` reads the file content into memory immediately, storing it in `state.extractedText`. This allows users to upload a previously saved `.txt` (from a prior extraction) and skip Step 1.

---

## Step 1 — Extraction

```js
async function runExtraction() {
    if (!state.pdfFile) {
        showNotification("Please upload a PDF file first.");
        return;
    }

    const spinner = document.getElementById("extract-spinner");
    const btn     = document.getElementById("convert-btn");
    spinner.style.display = "inline-flex";
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append("file", state.pdfFile);

        const res = await fetch(`${API_BASE}/extract`, {
            method: "POST",
            body: formData,          // FormData auto-sets Content-Type: multipart/form-data
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();

        state.extractedText = data.text;
        const words = data.text.trim().split(/\s+/).length;
        document.getElementById("extracted-text-preview").textContent = data.text;
        document.getElementById("word-count-badge").textContent = `${words} words`;
        document.getElementById("extract-output").style.display = "block";
        document.getElementById("download-txt-btn").style.display = "inline-flex";
        updateStep1ImportMeta();
        showNotification("Text extracted successfully");
    } catch (err) {
        showNotification(`Extraction failed: ${err.message}`);
    } finally {
        spinner.style.display = "none";
        btn.disabled = false;
    }
}
```

**`FormData`** is the correct way to send file uploads via `fetch`. Setting `Content-Type: multipart/form-data` manually would break the multipart boundary — by passing `FormData` directly as the body, the browser sets the correct content type automatically.

**Word count calculation:** `data.text.trim().split(/\s+/).length` splits on any whitespace sequence (spaces, tabs, newlines) and counts the resulting array. This is a standard JS word count.

---

## Step 2 — Preprocessing

```js
async function runPreprocessing() {
    const text = state.extractedText;
    if (!text) {
        showNotification("No text available. Complete Step 1 first.");
        return;
    }

    const options = {
        lowercase:  document.getElementById("toggle-lower").classList.contains("on"),
        sectioning: document.getElementById("toggle-stop").classList.contains("on"),
    };

    const res = await fetch(`${API_BASE}/preprocess`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ text, options }),
    });
    const data = await res.json();

    state.preprocessedText = data.preprocessed_text;
    state.sections         = data.sections;

    // Before/After comparison display
    document.getElementById("compare-before").textContent =
        text.substring(0, 600) + (text.length > 600 ? "…" : "");
    document.getElementById("compare-after").textContent =
        data.preprocessed_text.substring(0, 600) + …;

    // Populate accordion
    const acc = document.getElementById("sections-accordion");
    acc.innerHTML = "";
    data.sections.forEach((s, i) => {
        acc.innerHTML += `<div class="accordion-item" id="acc-${i}"> … </div>`;
    });
}
```

**Toggle state reading:** `classList.contains("on")` checks whether the toggle CSS class is present. This is how the toggle's visual state maps to a boolean value sent to the API.

**The Before/After comparison** shows only the first 600 characters to avoid overwhelming the UI. The ellipsis `…` is appended if the full text is longer.

**Accordion building:** Sections are dynamically injected as HTML strings. Each accordion item gets a unique `id="acc-N"` so the `toggleAccordion(N)` function can find it.

---

## Step 3 — Summarization

```js
async function runSummarization() {
    const container = document.getElementById("summary-cards-container");

    // Show skeleton placeholder while waiting
    container.innerHTML = `
        <div class="summary-card">
            <div class="skeleton" style="height:14px;width:120px;margin-bottom:14px;"></div>
            …
        </div>`;

    const res = await fetch(`${API_BASE}/summarize`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ sections: state.sections }),
    });
    const data = await res.json();
    state.summaries = data.summaries;

    // Replace skeletons with real cards
    container.innerHTML = "";
    data.summaries.forEach((s, i) => {
        const card = document.createElement("div");
        card.className = "summary-card";
        card.style.animationDelay = `${i * 0.08}s`;
        card.innerHTML = `
            <div class="summary-card-header">
                <span class="summary-tag">${s.section}</span>
                <button class="btn btn-ghost btn-sm" onclick="copyToClipboard(\`${s.summary.replace(/\`/g, "'")}\`)">
                    …copy icon…
                </button>
            </div>
            <p class="summary-text">${s.summary}</p>`;
        container.appendChild(card);
    });
}
```

**Skeleton → real content pattern:** The skeleton is rendered immediately when the button is clicked (before the await), so the user sees a loading state instantly. After the API call completes, the skeleton HTML is replaced with real content.

**`animationDelay`:** Each card gets a staggered delay (`0s`, `0.08s`, `0.16s`…) so they fade in one after another rather than all at once — a small UX detail.

**Backtick escaping in the copy button:** The summary text is embedded inside a template literal in the `onclick` attribute. Any backticks in the summary text would break the outer template literal, so they are replaced with single quotes: `.replace(/\`/g, "'")`.

---

## Step 4 — Insights Rendering

`loadInsights()` fires `POST /insights` and passes the response to `renderInsights(data)`.

```js
function renderInsights(data) {
    // 1. Keyword cloud
    const cloud = document.getElementById("keyword-cloud");
    cloud.innerHTML = data.keywords.map(k => {
        const cls = k.score > 0.7 ? "large" : k.score < 0.4 ? "small" : "";
        return `<span class="keyword-pill ${cls}">${k.word}</span>`;
    }).join("");

    // 2. Pillar bar chart (data-width stores the target width)
    const pillarsChart = document.getElementById("pillars-chart");
    pillarsChart.innerHTML = data.pillars.map(p => `
        <div class="bar-row">
            <span class="bar-label">${p.name}</span>
            <div class="bar-track">
                <div class="bar-fill" style="width:0%" data-width="${p.score}%"></div>
            </div>
            <span class="bar-value">${p.score}</span>
        </div>`).join("");

    // 3. School of thought
    document.getElementById("school-label").textContent = data.school_of_thought.label;
    document.getElementById("school-desc").textContent  = data.school_of_thought.description;
    document.getElementById("school-tags").innerHTML    = [data.school_of_thought.cohesion, ...data.school_of_thought.tags]
        .map((t, i) => `<span class="net-tag ${i === 0 ? "highlight" : ""}">${t}</span>`)
        .join("");

    // 4. Alignment bar
    document.getElementById("alignment-bar").dataset.width = `${data.alignment.applied}%`;
    document.getElementById("alignment-labels").innerHTML  = `
        <div class="pct-label">Applied — ${data.alignment.applied}%</div>
        <div class="pct-label secondary">Theoretical — ${data.alignment.theoretical}%</div>`;

    // … methods, trending, cross-disciplinary …

    // Trigger bar animations after DOM update
    setTimeout(animateBars, 200);
}
```

**`data-width` pattern explained:** Bar widths start at `0%` in the rendered HTML. After all the DOM manipulation is done, `setTimeout(animateBars, 200)` runs — a 200ms delay ensures the DOM has settled and the browser has painted the 0% state. Then `animateBars()` sets the real widths, triggering the CSS `transition: width 1s` animation. Without the delay, the bars would jump to their final width instantly (no animation), because the transition only fires when a value changes *after* the element is already on screen.

---

## Clipboard Copy

```js
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => showNotification("Copied to clipboard"));
}
```

`navigator.clipboard` is the modern asynchronous Clipboard API. It requires a secure context (HTTPS or localhost). Since this app runs on `localhost:8000`, it works without any special configuration.

---

## References

- [MDN — FormData](https://developer.mozilla.org/en-US/docs/Web/API/FormData)
- [MDN — FileReader](https://developer.mozilla.org/en-US/docs/Web/API/FileReader)
- [MDN — Clipboard API](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API)
- [MDN — fetch()](https://developer.mozilla.org/en-US/docs/Web/API/fetch)
- [MDN — async/await](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Promises)
