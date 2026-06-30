# Performance profile — items_dyn.html

**Status:** read-only profiling pass. No behavior changes. Findings only.

## Page footprint

| Metric | Value |
|---|---|
| File size (on disk) | 1,690,932 bytes (1.61 MB) |
| Matrix shape | ~354 rows × ~116 patch columns |
| Total `<td>` elements | 41,654 |
| Total `class=` attributes | 42,986 |
| `data-*` attributes | 3,932 |
| Inline `<script>` / `<style>` | 0 chars (all external + minified) |
| Per-element listeners | **0** (already fully delegated — see below) |

## Cell-type breakdown

The matrix is overwhelmingly placeholder cells:

| Class combo | Count | % of cells | Approx HTML bytes |
|---|---|---|---|
| `hd-cell hd-empty` (no changes that patch) | 17,779 | 42.7% | ~640 KB |
| `hd-cell hd-absent` (item didn't exist yet) | 11,400 | 27.4% | ~422 KB |
| `hd-cell hd-empty hd-gsep` (group separator + empty) | 6,400 | 15.4% | ~275 KB |
| `hd-cell hd-absent hd-gsep` | 4,976 | 11.9% | ~219 KB |
| `hd-hero sticky-col` (item-name rows) | 353 | 0.8% | — |
| `hd-cell hd-empty hd-spacer` | 353 | 0.8% | — |
| `hd-cell hd-gsep` (active + sep) | 273 | 0.7% | — |
| `hd-cell` (active, with data) | 120 | 0.3% | — |
| **Total empty/absent placeholders** | **40,555** | **~97%** | **~1.55 MB (~92% of file)** |
| Cells JS actually fills with pills (after `dynFillMatrix`) | ~1,099 | ~2.6% | — |

## What is already optimized

Reading `src/scripts.js` 700–1400:

1. **Event delegation is already in place.** There is *no* per-cell
   `addEventListener`. A single `document.addEventListener('mouseover', …)`
   at line 1367 dispatches on `e.target.closest('.dyn-cell-wrap')`.
2. **Tooltip DOM is lazy + shared singleton.** Comment at line 1324:
   *"Single shared tooltip lives on document.body … Lazy: we only build
   the tooltip DOM once, then re-populate it on hover."* Comment at 1328
   notes the prior eager-build approach added ~50k DOM nodes upfront.
3. **Hero-column width is measured once, cached on the table** (line
   978–986), avoiding per-resize reflows.
4. **Column hiding for "Hide old" uses a single injected `<style>` rule**
   (lines 952–1004), not per-cell `display:none` toggles across thousands
   of cells.
5. **Pills are only built for cells the builder marked with
   `data-ver`/`data-hkey`** (line 933) — runtime work scales with real
   data (1,099 cells), not the full 41k grid.

So most of the obvious JS-side overhead has already been addressed in
prior optimization passes. The dominant remaining cost is **DOM size + HTML
parse time**, not listeners or filter loops.

## Highest-leverage findings (ordered by impact / safety)

### 1. Empty/absent cells dominate the payload — ~92% of bytes

40,555 of 41,654 cells are pure placeholders carrying no data, no pill,
no listener, and (per CSS) no visible content beyond a faint diamond. Each
empty/absent cell costs 36–44 bytes of HTML plus a DOM node.

**Why they exist:** they hold grid alignment so the sticky item column and
column-N patch headers line up with rows.

**Possible mitigations (NOT applied — needs design review):**

- **Single-attribute placeholder.** Replace
  `<td class="hd-cell hd-empty"></td>` (36 B) with `<td class="hde"></td>`
  (24 B). Naive saving: ~32% × 1.55 MB ≈ 500 KB. Requires renaming the
  matching CSS rules and verifying no JS selector reads the long form.
- **`colspan` collapsing of runs.** Many items have long contiguous runs
  of patches where they didn't exist (`hd-absent`) — collapse them into
  one wide cell per run. Risk: breaks per-column hover/grid-line CSS and
  the "Hide old" `nth-child` selector; would also require updating
  `dynFillMatrix`'s `td.hd-cell[data-ver]` query to still resolve
  individual patches.
- **CSS-grid render instead of table.** Replaces ~24k empty `<td>` nodes
  with grid lines; major rewrite of sticky-header + horizontal-scroll
  behaviour.

### 2. `content-visibility: auto` for row groups

CSS `content-visibility: auto` would let the browser skip layout/paint of
off-screen rows entirely (~80 KB of saved layout work on first paint,
based on the share of out-of-viewport rows). **Risk:** the matrix relies
on a sticky first column (`.sticky-col`) and sticky table header. Sticky
positioning + `content-visibility` interact badly in some Chromium
versions — the sticky element can lose its anchor when the row goes
hidden. Needs a focused test on Chrome+Firefox+Safari with horizontal
scrolling, hover-pop on the rightmost column (which already needs the
`HD_RIGHT_GUTTER` workaround), and the "Hide old" toggle.

### 3. Hide-old column ranges via `nth-child` triggers full restyle

Lines 1000–1004 set `style.textContent` to a `nth-child(-n+N)` rule that
selects across ~24k cells. Style invalidation is the cost driver when
toggling Hide-old, not painting. The single-rule approach is already
better than per-cell toggles, but a `[data-hidden]` attribute toggled on
`<tr>` would give the same visual effect with O(rows) invalidation
instead of O(cells). Marginal win (~10–30 ms on toggle); only worth doing
if combined with #1.

### 4. Sort/filter latency — not measured here

The page already short-circuits per-cell work for inactive cells. The
candidate hot path is `document.querySelectorAll('[data-tag]').forEach`
at line 162 and similar `forEach` chains during filter changes — those
walk the live DOM and grow linearly with cell count. With ~3,932
`data-*` attributes total, this is bounded but still meaningful. Should
be measured live before optimizing.

## What NOT to do

- **Do not virtualize the matrix.** The page is sortable and supports
  Ctrl-F search — virtualization breaks both. Listed last in the
  task brief for this reason.
- **Do not delete historical data** to shrink the file.
- **Do not change visual appearance of `.dyn-cell` / `.dyn-cell-wrap`**.

## Suggested next step

If asked to act on this profile, the highest reward-to-risk is **finding
#1, sub-bullet 1** (compress the empty-cell class names + drop trailing
empty class attributes). It is purely a generation-side change with no
runtime behavior delta beyond an HTML-byte reduction, and CSS rules can
be aliased so existing selectors still work. Expected saving: ~400–500 KB
HTML (24–30% smaller `items_dyn.html`), ~25% fewer bytes for the HTML
parser to walk.

Regression checks required after any change (per task brief):

- Search box (name + alias matching).
- Item-class / price / category / tag filter chips.
- Hide-old toggle (both states).
- Hover dyn-cell → tooltip.
- Click pill → patch page → back-arrow returns to matrix.
- Horizontal scroll, sticky Item column, both viewports (desktop +
  mobile).
