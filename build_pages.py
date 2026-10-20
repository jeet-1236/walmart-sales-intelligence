"""
dashboard_page.html -> docs/ (a standalone site for GitHub Pages)

The artifact page is written against the Dashboard runtime: it expects a `dash`
object for data and a set of CSS custom properties for colour and spacing. This
script wraps that same page, unchanged, in a standalone document that supplies
both -- so the chart code has exactly one implementation.

Usage:  python build_pages.py
"""

import io
import os
import re
import shutil

SRC = "dashboard_page.html"
SOURCES = "dashboard_sources"
OUT = "docs"

page = io.open(SRC, encoding="utf-8").read()

# The artifact page is <style>…</style> + <div class="wsi">…</div> + 5 scripts.
styles = re.findall(r"<style>(.*?)</style>", page, re.S)
scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
body = re.search(r'(<div class="wsi">.*?</div>)\s*(?:<script>|$)', page, re.S)
assert styles and scripts and body, "unexpected shape of dashboard_page.html"
body_html = body.group(1)
assert len(scripts) == 5, f"expected 5 script blocks, found {len(scripts)}"

ids = sorted(f[:-4] for f in os.listdir(SOURCES) if f.endswith(".csv"))

# Mid-tone series colours, chosen to stay legible on both a white and a near-black
# ground so the palette needs no theme switch of its own.
COLORS = ["#3C7FB1", "#C8853F", "#5F9B74", "#A2648A",
          "#7C85BE", "#A8894A", "#5E9B9B", "#B06C62"]

TOKENS = """
/* Layout: one centred column; cards carry the charts, tiles the figures.
   Colour: a steel blue leads, ochre and sage follow, brick reserved for
   "below baseline". Type: IBM Plex Sans throughout, Plex Serif for figures. */
:root {
  color-scheme: light;
  --font-anthropic-sans: "IBM Plex Sans", -apple-system, BlinkMacSystemFont,
    "Segoe UI", Roboto, sans-serif;
  --font-anthropic-serif: "IBM Plex Serif", Georgia, "Times New Roman", serif;

  --color-bg: #FFFFFF;
  --color-panel: #FAFBFC;
  --color-fg: #1C2430;
  --color-fg-muted: #626E7B;
  --color-border-line: #E3E8ED;
  --color-ok: #2F7D53;
  --color-warn: #9A6A14;
  --color-bad: #AC4338;

  --cds-radius: 8px;
  --cds-pad-xs: 4px;  --cds-pad-sm: 8px;  --cds-pad-md: 12px;
  --cds-pad-lg: 16px; --cds-pad-xl: 24px;
  --cds-gap-xs: 4px;  --cds-gap-sm: 8px;  --cds-gap-md: 16px;
  --cds-gap-lg: 28px; --cds-gap-xl: 40px;

  --cds-font-size-caption: 0.8125rem;
  --cds-font-size-body: 0.9375rem;
  --cds-font-size-heading: 1.125rem;
  --cds-font-size-title: 1.5rem;
  --cds-font-weight-medium: 550;

  --cds-chart-grid: #EDF1F4;
  --cds-chart-axis: #BFC8D1;
  --cds-chart-reference: #9AA6B2;
  --cds-chart-muted: #A8B2BC;
  --cds-chart-status-critical: #AC4338;

  --cds-surface-popover: #FFFFFF;
  --cds-border: #D8DEE5;
  --cds-shadow-popover: 0 4px 16px rgba(20, 30, 45, 0.13);
  --cds-text-secondary: #626E7B;
  --cds-dur-slow: 240ms;
  --cds-ease-out: cubic-bezier(0.2, 0, 0, 1);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --color-bg: #12171D;
    --color-panel: #181F27;
    --color-fg: #E6EBF0;
    --color-fg-muted: #94A1AE;
    --color-border-line: #263039;
    --color-ok: #5BBE86;
    --color-warn: #D6A33F;
    --color-bad: #E0736A;
    --cds-chart-grid: #1F2832;
    --cds-chart-axis: #3B4753;
    --cds-chart-reference: #6B7885;
    --cds-chart-muted: #5A6672;
    --cds-chart-status-critical: #E0736A;
    --cds-surface-popover: #1C242D;
    --cds-border: #2E3942;
    --cds-shadow-popover: 0 4px 16px rgba(0, 0, 0, 0.5);
    --cds-text-secondary: #94A1AE;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --color-bg: #12171D;        --color-panel: #181F27;
  --color-fg: #E6EBF0;        --color-fg-muted: #94A1AE;
  --color-border-line: #263039;
  --color-ok: #5BBE86;        --color-warn: #D6A33F;  --color-bad: #E0736A;
  --cds-chart-grid: #1F2832;  --cds-chart-axis: #3B4753;
  --cds-chart-reference: #6B7885; --cds-chart-muted: #5A6672;
  --cds-chart-status-critical: #E0736A;
  --cds-surface-popover: #1C242D; --cds-border: #2E3942;
  --cds-shadow-popover: 0 4px 16px rgba(0, 0, 0, 0.5);
  --cds-text-secondary: #94A1AE;
}

* { box-sizing: border-box; }
html, body { margin: 0; }
body {
  background: var(--color-bg);
  color: var(--color-fg);
  font-family: var(--font-anthropic-sans);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
}
img { max-width: 100%; }
[hidden] { display: none !important; }
#dash-root {
  padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 0 48px;
}
.wsi-boot {
  max-width: 78rem; margin-inline: auto; padding-block: 40px;
  color: var(--color-fg-muted); font-size: var(--cds-font-size-caption);
}
.dash-skeleton {
  display: inline-block; min-width: 3.5rem; border-radius: 4px;
  background: var(--color-border-line); color: transparent !important;
}
.wsi-foot {
  max-width: 78rem; margin: var(--cds-gap-lg) auto 0;
  border-top: 1px solid var(--color-border-line);
  padding-top: var(--cds-gap-md);
  color: var(--color-fg-muted); font-size: var(--cds-font-size-caption);
  line-height: 1.6;
}
.wsi-foot a { color: var(--color-fg); }
"""

SHIM = """
/* ---------------------------------------------------------------------------
   A minimal stand-in for the Dashboard runtime: it loads the source tables
   over fetch and exposes the same `dash` surface the page already uses, so no
   chart code has to change.
   --------------------------------------------------------------------------- */
window.dash = (function () {
  const IDS = %IDS%;
  const COLORS = %COLORS%;
  const DEFAULTS = { format: 'all', store: null };

  const store = {};
  IDS.forEach((id) => {
    store[id] = { status: 'loading', data: [], columns: [], refreshing: false, meta: [] };
  });

  let params = Object.assign({}, DEFAULTS);
  const callbacks = [];
  let booted = false;

  function fire() {
    callbacks.forEach((fn) => {
      try { fn(); } catch (e) { console.error('onData callback failed', e); }
    });
  }

  async function one(id) {
    try {
      const res = await fetch('data/' + id + '.csv', { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const rows = d3.csvParse(await res.text());
      store[id] = {
        status: 'ok', data: rows, columns: rows.columns || [],
        refreshing: false, meta: [],
      };
    } catch (err) {
      store[id] = {
        status: 'error', data: [], columns: [], refreshing: false, meta: [],
        message: String(err && err.message ? err.message : err),
      };
      console.error('could not load ' + id, err);
    }
  }

  async function loadAll() {
    await Promise.all(IDS.map(one));
    booted = true;
    const boot = document.querySelector('.wsi-boot');
    if (boot) boot.remove();
    document.querySelectorAll('.dash-skeleton')
      .forEach((el) => el.classList.remove('dash-skeleton'));
    fire();
  }

  let resizeTimer = null;
  window.addEventListener('resize', () => {
    if (!booted) return;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(fire, 160);
  });

  return {
    colors: COLORS,
    data(id) {
      return store[id] || { status: 'missing', data: [], columns: [], meta: [] };
    },
    onData(fn) {
      callbacks.push(fn);
      try { fn(); } catch (e) { console.error('onData callback failed', e); }
    },
    params() { return Object.assign({}, params); },
    setParams(next) { Object.assign(params, next || {}); fire(); },
    resetParams() { params = Object.assign({}, DEFAULTS); fire(); },
    setLink(name) {
      try { history.replaceState(null, '', name ? '#' + name : ' '); } catch (e) { /* ignore */ }
    },
    refresh() { loadAll(); },
    boot: loadAll,
  };
}());
"""

FOOT = """
<div class="wsi-foot">
  Built from the Walmart Store Sales Forecasting dataset: 421,570
  store-department-week records across 45 stores and 81 departments, 5&nbsp;Feb
  2010 to 26&nbsp;Oct 2012. Every figure is read from a table in
  <code>docs/data/</code>; nothing is recomputed in the browser. Source and the
  analysis pipeline:
  <a href="https://github.com/jeet-1236/walmart-sales-intelligence">github.com/jeet-1236/walmart-sales-intelligence</a>.
</div>
"""

shim = (SHIM.replace("%IDS%", repr(ids).replace("'", '"'))
            .replace("%COLORS%", repr(COLORS).replace("'", '"')))

doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Walmart Sales Intelligence</title>
<meta name="description" content="Eight statistical experiments and a business-impact layer over 421,570 Walmart store-week sales records.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@400;500&display=swap">
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
{TOKENS}
</style>
<style>
{styles[0].strip()}
</style>
</head>
<body>
<div id="dash-root">
<div class="wsi-boot">Loading the source tables&hellip;</div>
{body_html}
{FOOT.strip()}
</div>
<script>
{shim.strip()}
</script>
""" + "\n".join(f"<script>\n{s.strip()}\n</script>" for s in scripts) + """
<script>
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.dash.boot());
  } else {
    window.dash.boot();
  }
</script>
</body>
</html>
"""

shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(doc)
for i in ids:
    shutil.copyfile(os.path.join(SOURCES, f"{i}.csv"),
                    os.path.join(OUT, "data", f"{i}.csv"))
# Pages otherwise runs the tree through Jekyll, which skips files it does not know.
io.open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8").write("")

total = sum(os.path.getsize(os.path.join(OUT, "data", f))
            for f in os.listdir(os.path.join(OUT, "data")))
print(f"docs/index.html   {len(doc.encode('utf-8')) / 1024:>7.0f} KB")
print(f"docs/data/        {total / 1024:>7.0f} KB across {len(ids)} tables")
print(f"script blocks     {doc.count('<script>')}")
print(f"datasets wired    {len(ids)}")
