# Frontend Overview

The frontend is a **single-page application** (SPA) contained entirely in `index.html`. It has no build step, no npm packages, and no external JavaScript libraries. Everything — HTML structure, CSS styling, and JavaScript logic — lives in one file.

---

## File Structure

```
index.html
├── <head>
│   ├── Google Fonts (DM Sans, DM Serif Display)
│   └── <style> block (~1200 lines of CSS)
│
└── <body>
    ├── <nav>          Fixed navigation bar with step labels
    ├── <main>
    │   ├── #hero-section    Landing page with "Begin Pipeline" button
    │   ├── #page-0          Step 1 — PDF Upload & Extraction
    │   ├── #page-1          Step 2 — Preprocessing & Section View
    │   ├── #page-2          Step 3 — Summarization
    │   └── #page-3          Step 4 — Insights Dashboard
    ├── #notification    Toast notification (fixed position)
    └── <script>         ~550 lines of inline JavaScript
```

`script.js` exists as a sibling file but currently only contains a comment — it is a placeholder for utilities that may be extracted in the future.

---

## Application State

All application state is stored in a single JavaScript object:

```js
let state = {
    currentStep:      0,       // which page (0–3) is active
    pdfFile:          null,    // the File object selected by the user
    extractedText:    "",      // plain text from /extract
    preprocessedText: "",      // text after /preprocess
    sections:         [],      // array of { name, words, text }
    summaries:        [],      // array of { section, summary }
    isDark:           false,   // current theme
};
```

This is the **single source of truth**. All API responses write into this object, and all rendering reads from it. There is no localStorage, no cookies, no session storage — if you refresh the page, all state is lost and you start over.

---

## Step Navigation

Pages are shown/hidden with CSS `display: none` / `display: block`. Only one page is visible at a time.

```js
function goTo(step) {
    document.getElementById("hero-section").style.display = "none";
    document.querySelectorAll(".page").forEach((p, i) => {
        p.classList.toggle("active", i === step);   // show/hide pages
    });
    document.querySelectorAll(".nav-step").forEach((s, i) => {
        s.classList.toggle("active", i === step);   // highlight nav step
    });
    state.currentStep = step;
    window.scrollTo({ top: 0, behavior: "smooth" });

    if (step === 1) {
        updateStep1ImportMeta();    // refresh the "N words ready" label
        toggleStep1Import();        // re-apply the checkbox state
    }
    if (step === 3) {
        setTimeout(animateBars, 400);  // CSS bar animation
        loadInsights();                // fire POST /insights
    }
}
```

**Step guards** prevent users from skipping ahead without completing prior steps:

```js
const STEP_GUARDS = [
    () => !!state.extractedText   || "Extract text from a PDF in Step 1 first.",
    () => !!state.sections.length || "Run preprocessing in Step 2 first.",
    () => !!state.summaries.length || "Generate a summary in Step 3 first.",
];

function continueToStep(to) {
    const guard = STEP_GUARDS[to - 1];
    const result = guard();
    if (result !== true) {
        showNotification(result);
        return;
    }
    goTo(to);
}
```

Guards return `true` (proceed) or an error string (show as notification and block navigation).

---

## API Communication

All four API calls use the `fetch` API with `async/await`. The base URL is configured at the top of the script:

```js
const API_BASE = "http://localhost:8000";
```

If you deploy to a different host or port, this is the only line to change.

**Pattern used for every API call:**
```js
async function runSomething() {
    showSpinner();
    disableButton();

    try {
        const res = await fetch(`${API_BASE}/endpoint`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();
        // update state and re-render
    } catch (err) {
        showNotification(`Failed: ${err.message}`);
        console.error(err);
    } finally {
        hideSpinner();
        enableButton();
    }
}
```

The `try/catch/finally` pattern ensures the UI always returns to a usable state even if the server throws an error or goes offline.

---

## Theme System

Light/dark mode is implemented with a `data-theme` attribute on `<html>`:

```js
function toggleTheme() {
    state.isDark = !state.isDark;
    document.documentElement.setAttribute("data-theme", state.isDark ? "dark" : "light");
}
```

All colours are CSS custom properties (variables) with two variants:

```css
:root { --bg: #ffffff; --text: #1d1d1f; … }
[data-theme="dark"] { --bg: #000000; --text: #f5f5f7; … }
```

When `data-theme="dark"` is set, the dark-mode overrides take effect throughout the entire document — no class toggling needed on individual elements.

---

## Notification Toast

```js
function showNotification(msg) {
    const el = document.getElementById("notification");
    document.getElementById("notification-text").textContent = msg;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), 3000);
}
```

The notification is always in the DOM but positioned off-screen (`transform: translateY(80px); opacity: 0`). Adding the `show` class transitions it into view. After 3 seconds it slides back out.

---

## Download Functions

Three download functions let users save pipeline outputs as files:

| Function | Output file | Content |
|----------|------------|---------|
| `downloadTxt()` | `extracted.txt` | Raw extracted text |
| `downloadSummaries()` | `summaries.json` | The summaries array |
| `downloadInsights()` | `research-insights.json` | Full report with summaries and sections |

All three use the same browser pattern:
```js
const blob = new Blob([content], { type: "..." });
const a = document.createElement("a");
a.href = URL.createObjectURL(blob);
a.download = "filename";
a.click();
```

`URL.createObjectURL` creates a temporary in-memory URL pointing to the blob. The programmatic click triggers the browser's download mechanism.

---

## References

- [MDN — Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN — CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [MDN — URL.createObjectURL()](https://developer.mozilla.org/en-US/docs/Web/API/URL/createObjectURL_static)
- [MDN — classList.toggle()](https://developer.mozilla.org/en-US/docs/Web/API/DOMTokenList/toggle)
