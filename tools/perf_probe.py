"""Reusable scroll-performance probe for Sloppy pages.

Loads each URL in headless Chromium, waits for the page to settle, then
performs a programmatic smooth scroll from top to bottom while recording:

  - per-frame times (via requestAnimationFrame), long tasks (PerformanceObserver
    'longtask'), CDP Performance.getMetrics deltas (layout/recalc-style/script
    duration and counts), and static DOM stats (element count, max depth,
    images, and counts of box-shadow / filter / backdrop-filter / sticky /
    will-change / transform elements).

Usage:

    python tools/perf_probe.py
    python tools/perf_probe.py --urls heroes/anti-mage.html hero_changes.html
    python tools/perf_probe.py --label before
    python tools/perf_probe.py --label after --budget-p95 25

Writes a JSON report to outputs/perf/<date>[_<label>].json and prints a
readable table. Exits with code 1 if any page's p95 frame time exceeds the
budget (default 25ms), so it can be wired into CI later.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import statistics
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / "perf"

DEFAULT_URLS = [
    "heroes/anti-mage.html",
    "heroes/invoker.html",
    "items/battle-fury.html",
    "patches/7.41.html",
    "patches/7.38.html",
    "hero_changes.html",
    "item_changes.html",
    "heroes_dyn.html",
    "items_dyn.html",
    "heroes_stats.html",
    "hero_lab.html",
]

DEFAULT_BASE_URL = "http://localhost:8799"

# CDP metrics we care about for the layout/style/script cost breakdown.
CDP_METRIC_NAMES = (
    "LayoutCount",
    "RecalcStyleCount",
    "LayoutDuration",
    "RecalcStyleDuration",
    "ScriptDuration",
    "TaskDuration",
)

INIT_SCRIPT = """
(() => {
  window.__perfProbe = { frames: [], longTasks: [], collecting: false, _lastTs: null };
  try {
    const po = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        window.__perfProbe.longTasks.push({ start: entry.startTime, duration: entry.duration });
      }
    });
    po.observe({ entryTypes: ['longtask'] });
  } catch (e) { /* longtask not supported */ }

  function loopFrames(ts) {
    const p = window.__perfProbe;
    if (p.collecting) {
      if (p._lastTs != null) p.frames.push(ts - p._lastTs);
      p._lastTs = ts;
    } else {
      p._lastTs = null;
    }
    requestAnimationFrame(loopFrames);
  }
  requestAnimationFrame(loopFrames);
})();
"""

DOM_STATS_SCRIPT = """
() => {
  const all = document.querySelectorAll('*');
  let maxDepth = 0;
  const stack = [[document.body, 0]];
  while (stack.length) {
    const [el, d] = stack.pop();
    if (d > maxDepth) maxDepth = d;
    for (const child of el.children) stack.push([child, d + 1]);
  }
  let boxShadow = 0, filterCnt = 0, backdrop = 0, sticky = 0, willChange = 0, transform = 0;
  all.forEach(el => {
    const s = getComputedStyle(el);
    if (s.boxShadow && s.boxShadow !== 'none') boxShadow++;
    if (s.filter && s.filter !== 'none') filterCnt++;
    if (s.backdropFilter && s.backdropFilter !== 'none') backdrop++;
    if (s.position === 'sticky') sticky++;
    if (s.willChange && s.willChange !== 'auto') willChange++;
    if (s.transform && s.transform !== 'none') transform++;
  });
  return {
    elementCount: all.length,
    maxDepth,
    images: document.images.length,
    boxShadow, filter: filterCnt, backdrop, sticky, willChange, transform,
  };
}
"""

SCROLL_SCRIPT = """
async () => {
  const p = window.__perfProbe;
  p.frames = [];
  p.longTasks = [];
  const doc = document.scrollingElement || document.documentElement;
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 80));
  const end = doc.scrollHeight - window.innerHeight;
  p.collecting = true;
  const stepPx = 90; // roughly a few mouse-wheel notches per tick
  let pos = 0;
  await new Promise(resolve => {
    function tick() {
      pos = Math.min(pos + stepPx, Math.max(end, 0));
      window.scrollTo(0, pos);
      if (pos >= end || end <= 0) { resolve(); return; }
      requestAnimationFrame(() => setTimeout(tick, 0));
    }
    tick();
  });
  await new Promise(r => setTimeout(r, 250));
  p.collecting = false;
  return { frames: p.frames.slice(), longTasks: p.longTasks.slice(), scrollHeight: doc.scrollHeight };
}
"""


def percentile(values, pct):
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def run_one(page, context, url, budget_p95_ms):
    cdp = context.new_cdp_session(page)
    cdp.send("Performance.enable")

    page.goto(url, wait_until="networkidle", timeout=45000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(150)

    dom_stats = page.evaluate(DOM_STATS_SCRIPT)

    before = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}
    scroll_result = page.evaluate(SCROLL_SCRIPT)
    after = {m["name"]: m["value"] for m in cdp.send("Performance.getMetrics")["metrics"]}

    cdp_deltas = {
        name: round((after.get(name, 0.0) - before.get(name, 0.0)) * 1000, 2)  # s -> ms
        if "Duration" in name else round(after.get(name, 0.0) - before.get(name, 0.0), 2)
        for name in CDP_METRIC_NAMES
    }

    frames = scroll_result["frames"]
    long_tasks = scroll_result["longTasks"]
    p50 = round(percentile(frames, 50), 2)
    p95 = round(percentile(frames, 95), 2)
    fmax = round(max(frames), 2) if frames else 0.0
    over_16 = sum(1 for f in frames if f > 16.7)
    over_33 = sum(1 for f in frames if f > 33.0)
    pct_over_16 = round(100.0 * over_16 / len(frames), 1) if frames else 0.0
    pct_over_33 = round(100.0 * over_33 / len(frames), 1) if frames else 0.0

    return {
        "url": url,
        "dom": dom_stats,
        "frames": {
            "count": len(frames),
            "p50_ms": p50,
            "p95_ms": p95,
            "max_ms": fmax,
            "pct_over_16_7ms": pct_over_16,
            "pct_over_33ms": pct_over_33,
        },
        "long_tasks": {
            "count": len(long_tasks),
            "total_ms": round(sum(t["duration"] for t in long_tasks), 2),
        },
        "cdp_deltas_ms": cdp_deltas,
        "pass": p95 <= budget_p95_ms,
    }


def print_table(results, budget_p95_ms):
    header = (
        f"{'URL':38} {'p95(ms)':>8} {'>16.7ms%':>9} {'>33ms%':>8} "
        f"{'longtasks':>10} {'Layout(ms)':>11} {'Recalc(ms)':>11} {'Script(ms)':>11} {'STATUS':>7}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(
            f"{r['url']:38} {r['frames']['p95_ms']:>8} {r['frames']['pct_over_16_7ms']:>9} "
            f"{r['frames']['pct_over_33ms']:>8} {r['long_tasks']['count']:>10} "
            f"{r['cdp_deltas_ms']['LayoutDuration']:>11} {r['cdp_deltas_ms']['RecalcStyleDuration']:>11} "
            f"{r['cdp_deltas_ms']['ScriptDuration']:>11} {status:>7}"
        )
    print(f"\nBudget: p95 frame time <= {budget_p95_ms}ms")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--urls", nargs="*", default=DEFAULT_URLS, help="Relative paths (or absolute URLs)")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--out", default=None, help="Output JSON path (default: outputs/perf/<date>[_<label>].json)")
    ap.add_argument("--label", default=None, help="Suffix for the default output filename (e.g. before/after)")
    ap.add_argument("--budget-p95", type=float, default=25.0, help="Fail budget for p95 frame time in ms")
    ap.add_argument("--extra-style", default=None, help="Path to a CSS file to inject via add_style_tag (A/B testing)")
    ap.add_argument("--extra-script", default=None, help="Path to a JS file to inject via add_init_script (A/B testing)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date = _dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_path = Path(args.out) if args.out else OUT_DIR / f"{date}{'_' + args.label if args.label else ''}.json"

    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 900})
        context.add_init_script(INIT_SCRIPT)
        if args.extra_script:
            context.add_init_script(Path(args.extra_script).read_text(encoding="utf-8"))
        page = context.new_page()
        if args.extra_style:
            css_text = Path(args.extra_style).read_text(encoding="utf-8")

            def _inject_style(p, css=css_text):
                p.add_style_tag(content=css)

            page.on("load", _inject_style)

        for rel in args.urls:
            url = rel if rel.startswith("http") else f"{args.base_url.rstrip('/')}/{rel.lstrip('/')}"
            try:
                r = run_one(page, context, url, args.budget_p95)
            except Exception as exc:  # keep going, report the failure
                r = {"url": url, "error": str(exc), "pass": False}
            results.append(r)

        browser.close()

    report = {
        "date": date,
        "base_url": args.base_url,
        "budget_p95_ms": args.budget_p95,
        "results": results,
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    ok_results = [r for r in results if "error" not in r]
    print_table(ok_results, args.budget_p95)
    errored = [r for r in results if "error" in r]
    for r in errored:
        print(f"ERROR  {r['url']}: {r['error']}")
    print(f"\nJSON report: {out_path}")

    failed = any(not r["pass"] for r in results)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
