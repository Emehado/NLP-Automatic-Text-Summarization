# UI Components & Design System

The frontend uses a hand-crafted CSS design system inspired by Apple's Human Interface Guidelines — clean typography, subtle shadows, smooth transitions, and a strict monochromatic palette that works in both light and dark mode.

---

## Design Tokens (CSS Custom Properties)

All colours, shadows, radii, and transitions are defined as CSS variables in `:root`. This makes theming trivial — only one set of overrides is needed for dark mode.

```css
:root {
    --bg:          #ffffff;         /* page background */
    --surface:     #f5f5f7;         /* card backgrounds */
    --surface2:    #e8e8ed;         /* secondary surfaces, inactive toggles */
    --border:      rgba(0,0,0,0.08);/* all borders */
    --text:        #1d1d1f;         /* primary text + buttons */
    --text-secondary: #6e6e73;      /* body text, descriptions */
    --text-tertiary:  #a1a1a6;      /* labels, meta text */
    --accent:      #000000;         /* accent colour (same as text in light mode) */

    --card-shadow:       0 2px 20px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04);
    --card-shadow-hover: 0 8px 40px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06);

    --radius:    18px;              /* large border radius (cards) */
    --radius-sm: 12px;              /* small border radius (inner elements) */
    --transition: cubic-bezier(0.25, 0.46, 0.45, 0.94);  /* easing curve */
}
```

Dark mode overrides:
```css
[data-theme="dark"] {
    --bg:       #000000;
    --surface:  #1c1c1e;
    --surface2: #2c2c2e;
    --border:   rgba(255,255,255,0.1);
    --text:     #f5f5f7;
    /* … */
}
```

---

## Typography

Two typefaces from [Google Fonts](https://fonts.google.com):

| Font | Usage | Style |
|------|-------|-------|
| **DM Sans** | Body text, labels, buttons | Sans-serif, weights 200–600 |
| **DM Serif Display** | Page titles, hero heading, metric values | Serif, includes italic |

The heading hierarchy uses `clamp()` for fluid responsive sizing:
```css
.hero h1 { font-size: clamp(42px, 6vw, 72px); }
.page-title { font-size: clamp(28px, 4vw, 40px); }
```
`clamp(min, preferred, max)` means the font scales with the viewport but never goes below the minimum or above the maximum.

---

## Component Catalogue

### Card

```css
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--card-shadow);
    overflow: hidden;
    transition: box-shadow 0.3s var(--transition), border-color 0.3s;
}
.card:hover { box-shadow: var(--card-shadow-hover); }
```

Cards are the primary container component. They have:
- Surface-coloured background (slightly grey in light mode)
- Subtle shadow that deepens on hover
- Hidden overflow (prevents child elements from exceeding the border radius)

Usage: PDF upload zone, preprocessing options, summarisation config, insights panels.

---

### Button Variants

```css
.btn         { display: inline-flex; align-items: center; gap: 8px;
               padding: 12px 22px; border-radius: 40px; font-size: 14px;
               font-weight: 500; cursor: pointer; border: none; }

.btn-primary   { background: var(--text); color: var(--bg); }
.btn-secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
.btn-ghost     { background: none; color: var(--text-secondary); }
.btn-sm        { padding: 8px 16px; font-size: 12px; }
```

| Variant | When used |
|---------|-----------|
| `btn-primary` | Primary action ("Extract Text", "Generate Summaries") |
| `btn-secondary` | Navigation ("Back") |
| `btn-ghost` | Secondary actions ("Download .txt", copy button) |
| `btn-sm` | Compact contexts (card headers) |

`border-radius: 40px` creates the pill shape. `inline-flex` with `align-items: center` ensures icons and text are vertically aligned.

---

### Toggle Switch

```css
.toggle {
    width: 44px; height: 26px;
    border-radius: 13px;
    background: var(--surface2);
    position: relative;
    transition: background 0.25s;
}
.toggle.on { background: var(--text); }
.toggle::after {
    content: ""; position: absolute;
    width: 20px; height: 20px; border-radius: 50%;
    background: var(--bg); top: 3px; left: 3px;
    transition: transform 0.25s var(--transition);
}
.toggle.on::after { transform: translateX(18px); }
```

The toggle is a `<button>` with a `::after` pseudo-element as the sliding knob. The `.on` class is toggled by JavaScript:

```js
function toggleBtn(id) {
    document.getElementById(id).classList.toggle("on");
}
```

No SVG icons or images needed — pure CSS animation.

---

### Accordion

```html
<div class="accordion-item" id="acc-0">
  <div class="accordion-trigger" onclick="toggleAccordion(0)">
    <div class="accordion-trigger-left">
      <div class="accordion-index">1</div>
      <div>
        <div class="accordion-name">ABSTRACT</div>
        <div class="accordion-meta">142 words</div>
      </div>
    </div>
    <svg class="accordion-chevron">…</svg>
  </div>
  <div class="accordion-content">…</div>
</div>
```

```css
.accordion-content { display: none; }
.accordion-item.open .accordion-content { display: block; }
.accordion-item.open .accordion-chevron { transform: rotate(180deg); }
```

The `.open` class is toggled via JavaScript. The chevron rotates 180° to indicate the expanded state.

---

### Skeleton Loading

```css
.skeleton {
    background: linear-gradient(
        90deg,
        var(--surface) 25%,
        var(--surface2) 50%,
        var(--surface) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 8px;
}
@keyframes shimmer { to { background-position: -200% 0; } }
```

Shown as placeholder cards during the summarisation API call (which can take 30–90 seconds). The shimmer animation uses a moving gradient to simulate loading activity. It is purely CSS — no JavaScript needed.

---

### Bar Chart (Animated)

```css
.bar-fill {
    height: 100%;
    background: var(--text);
    border-radius: 4px;
    transition: width 1s var(--transition);  /* ← the animation */
}
```

Bars start at `width: 0%` in the HTML. The actual width is stored in `data-width`:
```html
<div class="bar-fill" style="width:0%" data-width="72%"></div>
```

When the insights page is entered, `animateBars()` reads `data-width` and applies it, triggering the CSS transition:
```js
function animateBars() {
    document.querySelectorAll(".bar-fill").forEach(bar => {
        bar.style.width = bar.dataset.width;
    });
}
```

This pattern separates the data (stored as an attribute) from the animation (triggered on page entry with a `setTimeout` delay so the user sees the bars animate in).

---

### Keyword Cloud

```css
.keyword-pill.large { font-size: 15px; padding: 8px 18px; }
.keyword-pill       { font-size: 13px; padding: 6px 14px; }
.keyword-pill.small { font-size: 11px; padding: 4px 10px; color: var(--text-tertiary); }
```

Three sizes represent the three frequency tiers. The size class is assigned in JavaScript based on the `score` value from the API:

```js
const cls = k.score > 0.7 ? "large" : k.score < 0.4 ? "small" : "";
```

---

### Spinner

```css
.spinner {
    width: 20px; height: 20px;
    border: 2px solid var(--border);
    border-top-color: var(--text);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
```

A pure CSS spinner — a circle with one coloured arc, rotating. Used next to buttons during API calls.

---

### Progress Bar (Step Indicator)

Each step page includes its own progress track. The `active` and `completed` states change the dot appearance:

```css
.step-dot { width: 30px; height: 30px; border-radius: 50%; background: var(--bg); … }
.progress-step.active    .step-dot { background: var(--text); color: var(--bg); }
.progress-step.completed .step-dot { background: var(--text); color: var(--bg); }
```

Completed steps show a "✓" character instead of a number (set directly in HTML):
```html
<div class="step-dot">✓</div>  <!-- on completed steps -->
<div class="step-dot">2</div>  <!-- on the active/pending step -->
```

The connecting line between steps is a CSS `::after` pseudo-element:
```css
.progress-step:not(:last-child)::after {
    content: ""; position: absolute;
    top: 15px; left: 50%; width: 100%; height: 1px;
    background: var(--border);
}
.progress-step.completed:not(:last-child)::after { background: var(--text); }
```

---

## Responsive Design

At ≤600px viewport width, the layout adapts:

```css
@media (max-width: 600px) {
    .nav-steps     { display: none; }         /* hide step nav in header */
    .grid-2        { grid-template-columns: 1fr; }  /* stack two-column grids */
    .compare-grid  { grid-template-columns: 1fr; }  /* stack before/after compare */
    .metric-row    { flex-direction: column; }       /* stack metric boxes */
    .insight-grid  { grid-template-columns: 1fr; }  /* stack insight cards */
}
```

The navigation step labels are hidden on mobile (too cramped). All two-column layouts collapse to a single column.
