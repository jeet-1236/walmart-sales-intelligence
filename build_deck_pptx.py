"""
Builds "Walmart Sales Intelligence.pptx" - a presentation of the project and
the dashboard.

Figures come from report_figures/, which is rendered from the same
dashboard_sources tables the dashboard reads, so the deck cannot disagree with
the dashboard or the written reports.

Usage:  python build_deck_pptx.py
"""

import os

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

SRC, FIG = "dashboard_sources", "report_figures"
OUT = "Walmart Sales Intelligence.pptx"
REPO = "github.com/jeet-1236/walmart-sales-intelligence"
LIVE = "jeet-1236.github.io/walmart-sales-intelligence"

# The dashboard's own palette, so the deck and the dashboard read as one thing.
DARK = RGBColor(0x16, 0x20, 0x2B)
BLUE = RGBColor(0x2F, 0x6D, 0x9E)
OCHRE = RGBColor(0xC8, 0x7F, 0x3D)
SAGE = RGBColor(0x5B, 0x8C, 0x6A)
BRICK = RGBColor(0xB5, 0x48, 0x38)
INK = RGBColor(0x1C, 0x24, 0x30)
FADE = RGBColor(0x62, 0x6E, 0x7B)
PALE = RGBColor(0xEE, 0xF3, 0xF8)
MIST = RGBColor(0x9A, 0xA3, 0xAB)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ICE = RGBColor(0xC6, 0xD8, 0xE8)

HEAD, BODY = "Cambria", "Calibri"
W, H = 13.333, 7.5
M = 0.62                      # slide margin

L = lambda n: pd.read_csv(os.path.join(SRC, n + ".csv"))
kp = L("kpis").set_index("metric")
K = lambda m: float(kp.loc[m, "value"])
q = L("eda_quality").set_index("metric")
Q = lambda m: float(q.loc[m, "value"])

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]


def slide(dark=False):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = DARK if dark else WHITE
    return s


def text(s, txt, x, y, w, h, size=16, color=INK, bold=False, font=BODY,
         align=PP_ALIGN.LEFT, italic=False, anchor=MSO_ANCHOR.TOP,
         space_after=0, line=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    lines = txt if isinstance(txt, list) else [txt]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line:
            p.line_spacing = line
        r = p.add_run()
        r.text = ln
        f = r.font
        f.size, f.bold, f.italic, f.name = Pt(size), bold, italic, font
        f.color.rgb = color
    return tb


def rect(s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE,
         line_w=1.0):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(line_w)
    sh.shadow.inherit = False
    sh.text_frame.text = ""
    return sh


def pic(s, name, x, y, maxw, maxh):
    """Place a figure inside the box, keeping its aspect ratio, centred."""
    path = os.path.join(FIG, name + ".png")
    if not os.path.exists(path):
        return None
    iw, ih = Image.open(path).size
    scale = min(maxw / (iw / 96), maxh / (ih / 96))
    w, h = (iw / 96) * scale, (ih / 96) * scale
    return s.shapes.add_picture(path, Inches(x + (maxw - w) / 2),
                                Inches(y + (maxh - h) / 2),
                                Inches(w), Inches(h))


def head(s, title, kicker=None, dark=False):
    """A content-slide title, in the same place on every content slide."""
    if kicker:
        text(s, kicker.upper(), M, 0.44, W - 2 * M, 0.26, size=11,
             color=OCHRE, bold=True, font=BODY)
    text(s, title, M, 0.74, W - 2 * M, 0.72, size=30, bold=True, font=HEAD,
         color=WHITE if dark else INK)


def card(s, x, y, w, h, title, lines, accent=BLUE, tsize=14, bsize=11.5):
    rect(s, x, y, w, h, fill=PALE)
    dot = rect(s, x + 0.22, y + 0.26, 0.17, 0.17, fill=accent,
               shape=MSO_SHAPE.OVAL)
    text(s, title, x + 0.52, y + 0.20, w - 0.74, 0.32, size=tsize, bold=True,
         color=INK)
    text(s, lines, x + 0.52, y + 0.58, w - 0.74, h - 0.70, size=bsize,
         color=FADE, space_after=4, line=1.25)


def stat(s, x, y, w, value, label, color=BLUE, vsize=40):
    text(s, value, x, y, w, 0.66, size=vsize, bold=True, font=HEAD,
         color=color, align=PP_ALIGN.CENTER)
    text(s, label, x, y + 0.70, w, 0.56, size=11, color=FADE,
         align=PP_ALIGN.CENTER, line=1.2)


def notes(s, txt):
    s.notes_slide.notes_text_frame.text = txt


def divider(kicker, title, sub, note=None):
    s = slide(dark=True)
    text(s, kicker.upper(), M, 2.55, W - 2 * M, 0.3, size=13, color=OCHRE,
         bold=True)
    text(s, title, M, 2.95, W - 2 * M, 0.95, size=40, bold=True, font=HEAD,
         color=WHITE)
    text(s, sub, M, 4.00, 8.6, 0.8, size=15, color=ICE, line=1.3)
    if note:
        notes(s, note)
    return s


# ==================================================================== 1 TITLE
s = slide(dark=True)
text(s, "WALMART STORE SALES  ·  DATA ANALYSIS MINI PROJECT", M, 1.55,
     W - 2 * M, 0.32, size=13, color=OCHRE, bold=True)
text(s, "Walmart Sales Intelligence", M, 2.00, W - 2 * M, 1.05, size=50,
     bold=True, font=HEAD, color=WHITE)
text(s, "Eight statistical experiments and a business-impact layer over "
        "421,570 store-department-week sales records, published as an "
        "interactive dashboard.", M, 3.20, 9.2, 1.0, size=16, color=ICE,
     line=1.35)
rect(s, M, 4.52, 3.1, 0.035, fill=OCHRE)
for i, (val, lab) in enumerate([("421,570", "records"), ("45", "stores"),
                                ("81", "departments"), ("143", "weeks")]):
    x = M + i * 2.05
    text(s, val, x, 4.85, 1.9, 0.56, size=28, bold=True, font=HEAD, color=WHITE)
    text(s, lab, x, 5.42, 1.9, 0.3, size=11.5, color=MIST)
text(s, ["Dashboard   " + LIVE, "Code   " + REPO], M, 6.35, 8.5, 0.8,
     size=12.5, color=ICE, space_after=3)
notes(s, "A public Walmart dataset of weekly sales from 45 stores over two and "
         "a half years. The deck covers what we did, what we found, and the "
         "dashboard we built from it.")

# ================================================================ 2 WHAT WE DID
s = slide()
head(s, "From four spreadsheets to one dashboard", "How it was built")
pic(s, "guide_pipeline", M, 1.52, 6.5, 5.5)
steps = [
    ("1  Collect", "Four CSV files: sales, store details and weekly "
     "conditions."),
    ("2  Join", "Merge into one table. One row is one department, in one "
     "store, in one week."),
    ("3  Clean", "Fix data types, handle missing values, add the columns the "
     "analysis needs."),
    ("4  Analyse", "Eight experiments in Python, from descriptive statistics "
     "to forecasting."),
    ("5  Publish", "Save every result as a small table, then draw it as an "
     "interactive dashboard."),
]
y = 1.58
for t, d in steps:
    rect(s, 7.35, y, 0.045, 0.92, fill=BLUE)
    text(s, t, 7.62, y + 0.02, 5.0, 0.3, size=14, bold=True, color=INK)
    text(s, d, 7.62, y + 0.36, 5.05, 0.6, size=11.5, color=FADE, line=1.22)
    y += 1.03
notes(s, "The key design decision is step 5. Python does all the heavy work "
         "once and writes small tables. The dashboard only draws them, which "
         "is why it opens instantly and needs no server.")

# =================================================================== 3 DATASET
s = slide()
head(s, "The dataset", "What we started with")
text(s, "Walmart Store Sales Forecasting — a public dataset of weekly "
        "sales from 45 stores, supplied as four files.", M, 1.58, 11.0, 0.4,
     size=14, color=FADE)
files = [("train.csv", "Weekly sales per store and department. The main file.",
          SAGE),
         ("stores.csv", "Store type (A, B or C) and size in square feet.", SAGE),
         ("features.csv", "Temperature, fuel price, CPI, unemployment and five "
          "markdown columns.", SAGE),
         ("test.csv", "Same shape but no sales column — not used, there is "
          "nothing to analyse.", BRICK)]
y = 2.20
for n, d, col in files:
    rect(s, M, y, 7.3, 0.82, fill=PALE)
    rect(s, M + 0.24, y + 0.30, 0.16, 0.16, fill=col, shape=MSO_SHAPE.OVAL)
    text(s, n, M + 0.54, y + 0.15, 2.0, 0.3, size=13.5, bold=True, color=INK)
    text(s, d, M + 2.52, y + 0.14, 4.6, 0.6, size=11, color=FADE, line=1.2)
    y += 0.94
rect(s, 8.35, 2.20, 4.38, 3.46, fill=DARK)
text(s, "AFTER JOINING", 8.70, 2.50, 3.7, 0.28, size=11, bold=True, color=OCHRE)
rows = [("421,570 × 16", "rows × columns"),
        ("45  /  81", "stores / departments"),
        ("143", "weeks, Feb 2010 – Oct 2012"),
        ("$6.74B", "total sales covered")]
yy = 2.92
for v, lab in rows:
    text(s, v, 8.70, yy, 3.7, 0.4, size=21, bold=True, font=HEAD, color=WHITE)
    text(s, lab, 8.70, yy + 0.40, 3.7, 0.26, size=10.5, color=MIST)
    yy += 0.68
text(s, "One row means: one department, in one store, in one week.", M, 5.95,
     11.5, 0.4, size=13, italic=True, color=BLUE)
notes(s, "test.csv exists for a prediction competition. With the sales column "
         "removed there is nothing in it to analyse, so we left it out.")

# ============================================================= 4 PREPROCESSING
PREP_A = [
    ("Merging", "Joined on Store, then on Store + Date. The second needs both "
     "keys because conditions change every week."),
    ("Type conversion", "Dates to datetime, the holiday flag to boolean, the "
     "markdown columns to numbers."),
    ("Missing values", "Dropped rows with no sales figure. Kept the markdown "
     "gaps visible rather than silently zero-filling them."),
    ("Feature engineering", "Added Year, Month, Week-of-year, TotalMarkDown "
     "and a HasMarkDown flag."),
    ("Duplicate check", "Verified Store + Dept + Date appears exactly once. A "
     "bad join silently inflates every total."),
    ("Aggregation", "Built store-week, store-department and chain-week "
     "summary tables for the different questions."),
]
PREP_B = [
    ("Outlier detection", "Flagged values outside the Tukey fences — and "
     "deliberately kept them, because they are the peak weeks."),
    ("Standardisation", "Rescaled six features before K-Means. Without it, "
     "store size alone would decide every cluster."),
    ("Dimensionality reduction", "Used PCA to squeeze six features into two, "
     "so the store groups can be drawn on a scatter plot."),
    ("Sampling", "Drew random, stratified and systematic samples at several "
     "sizes to test against the full dataset."),
    ("Within-group centring", "Removed each store-department's own mean before "
     "measuring the markdown effect."),
    ("Train / holdout split", "Hid the final 13 weeks so the forecast could be "
     "tested on data it had never seen."),
]
for part, (ttl, kicker, items) in enumerate([
        ("Getting the data into shape", "Preprocessing · 1 of 2", PREP_A),
        ("Preparing it for modelling", "Preprocessing · 2 of 2", PREP_B)]):
    s = slide()
    head(s, ttl, kicker)
    cw, ch, gap = 3.92, 2.18, 0.22
    for i, (t, d) in enumerate(items):
        r, c = divmod(i, 3)
        card(s, M + c * (cw + gap), 1.70 + r * (ch + gap), cw, ch, t, d,
             accent=[BLUE, OCHRE, SAGE][c], tsize=13.5, bsize=11)
    notes(s, "Each technique is here for a reason, not for the sake of a "
             "checklist. Two are worth saying out loud: we detected outliers "
             "but did not remove them, and we centred within store-department "
             "before judging markdowns.")

# ============================================================= 5 DIVIDER: DATA
divider("Part one", "What the data told us",
        "Before any modelling, we profiled every column. Three things changed "
        "how we read everything that followed.",
        "Exploratory data analysis comes before modelling for a reason: it is "
        "where you find the faults that would otherwise sit underneath every "
        "later conclusion.")

# ============================================================ 6 EDA: MISSING
s = slide()
head(s, "Only 23% of rows are complete", "Data quality")
text(s, "Every gap is in the five markdown columns. They are empty for the "
        "first two years and only begin in November 2011.", M, 1.58, 11.5, 0.4,
     size=14, color=FADE)
pic(s, "missing", M, 2.15, 5.85, 3.1)
pic(s, "missing_time", 6.85, 2.15, 5.85, 3.1)
rect(s, M, 5.52, 12.1, 1.26, fill=DARK)
text(s, "WHY THIS MATTERS", M + 0.34, 5.74, 4.0, 0.26, size=11, bold=True,
     color=OCHRE)
text(s, "Inside the window where markdowns are recorded, every single row has "
        "one. The data never shows a week with no discount, so "
        "“with discount versus without” cannot be measured here.",
     M + 0.34, 6.06, 11.4, 0.62, size=13, color=WHITE, line=1.25)
notes(s, "We only found this by profiling the raw files. The joined file fills "
         "those gaps with zero, and zero reads as 'we discounted nothing' when "
         "the truth is 'nobody recorded it'.")

# ======================================================= 7 EDA: DISTRIBUTION
s = slide()
head(s, "Sales are lopsided, and that is the business", "Distribution")
pic(s, "distribution", M, 1.62, 8.3, 3.5)
x0 = 9.25
stat(s, x0, 1.80, 3.45, "{:.1f}".format(K("e6_skew")), "skewness — a "
     "normal distribution would be 0", color=BLUE, vsize=38)
stat(s, x0, 3.18, 3.45, "{:.1f}%".format(K("e1_outlier_pct")),
     "of rows fall outside the Tukey fences", color=OCHRE, vsize=38)
stat(s, x0, 4.56, 3.45, "{:.0f}%".format(K("e1_outlier_revenue_pct")),
     "of all revenue sits inside those rows", color=BRICK, vsize=38)
text(s, "Normally you would remove outliers. Here you must not — removing "
        "them would delete Christmas.", M, 5.42, 8.3, 0.5, size=13,
     italic=True, color=BLUE, line=1.25)
notes(s, "The average weekly sale per department is about $16,000 but the "
         "middle value is only $7,600. A few enormous weeks pull the average "
         "up.")

# ======================================================== 8 DIVIDER: FINDINGS
divider("Part two", "Four findings that change a decision",
        "Each one contradicts the obvious reading of the data.",
        "These four were chosen because each one would lead to a different "
        "decision than the obvious reading of the same chart.")

# ============================================================ 9 FINDING: FLAG
s = slide()
head(s, "The holiday flag points at the wrong weeks", "Finding 1")
pic(s, "trend", M, 1.58, 8.25, 2.95)
pic(s, "holidays", M + 0.9, 4.60, 6.5, 2.40)
x0 = 9.20
card(s, x0, 1.62, 3.52, 1.72, "The flag marks a trough",
     "It lands on the week ending 31 December — the dead week after "
     "Christmas, about 29% below its December baseline.", accent=BRICK,
     tsize=13, bsize=10.5)
card(s, x0, 3.50, 3.52, 1.72, "The real peak is unflagged",
     "Week 51, the pre-Christmas week, is the biggest week of every year and "
     "carries no flag at all.", accent=OCHRE, tsize=13, bsize=10.5)
card(s, x0, 5.38, 3.52, 1.62, "What to do",
     "Replace the flag with named holidays and a week-of-year index before "
     "forecasting.", accent=SAGE, tsize=13, bsize=10.5)
notes(s, "Three of the five biggest weeks on record are labelled normal. Any "
         "model trained on this flag as-is learns the wrong calendar.")

# ========================================================== 10 FINDING: FORMAT
s = slide()
head(s, "The smallest stores work the hardest floor space", "Finding 2")
pic(s, "productivity", M, 1.62, 6.3, 4.0)
text(s, "Type A takes 64% of revenue because it has most of the square "
        "footage. Per square foot the ranking reverses.", 7.15, 1.70, 5.6, 0.7,
     size=14, color=FADE, line=1.3)
bars = [("Type C", 1667, SAGE, "6 stores, ~40k sq ft"),
        ("Type B", 1163, OCHRE, "17 stores, ~101k sq ft"),
        ("Type A", 1111, BLUE, "22 stores, ~177k sq ft")]
y = 2.70
for name, val, col, sub in bars:
    text(s, name, 7.15, y, 1.1, 0.3, size=13, bold=True, color=INK)
    rect(s, 8.30, y + 0.04, 3.0 * val / 1800, 0.26, fill=col)
    text(s, "${:,}".format(val), 11.55, y - 0.01, 1.2, 0.3, size=13, bold=True,
         color=col)
    text(s, sub, 7.15, y + 0.36, 5.3, 0.26, size=10.5, color=FADE)
    y += 0.90
text(s, "Revenue per square foot. Size and productivity rank in opposite "
        "directions.", 7.15, 5.45, 5.6, 0.5, size=12, italic=True, color=BLUE,
     line=1.25)
notes(s, "This holds at median-store level too, so it is not an artefact of "
         "totalling. ANOVA across the three formats gives F of about 7,800.")

# ======================================================== 11 FINDING: MARKDOWN
s = slide()
head(s, "Markdown's effect is mostly store size", "Finding 3")
pic(s, "markdown", M, 1.70, 5.6, 3.5)
text(s, "What the raw chart suggests", 6.55, 1.72, 6.2, 0.34, size=15,
     bold=True, color=INK)
text(s, "The deepest markdown quintile averages 110% more sales than the "
        "lightest. That looks like a powerful promotion effect.", 6.55, 2.12,
     6.2, 0.72, size=12.5, color=FADE, line=1.3)
text(s, "What is actually happening", 6.55, 3.02, 6.2, 0.34, size=15,
     bold=True, color=BRICK)
text(s, "Large departments receive large markdowns and already sell more. "
        "Remove each store-department's own average and the effect nearly "
        "vanishes.", 6.55, 3.42, 6.2, 0.78, size=12.5, color=FADE, line=1.3)
rect(s, 6.55, 4.40, 6.18, 1.30, fill=DARK)
text(s, "$0.015", 6.85, 4.58, 2.1, 0.62, size=33, bold=True, font=HEAD,
     color=WHITE)
text(s, "of sales per markdown dollar, measured within store-department. It "
        "explains 0.1% of a store's own week-to-week swing.", 9.00, 4.62, 3.5,
     0.92, size=11, color=ICE, line=1.22)
text(s, "Nothing here identifies a causal promotion effect. That needs a "
        "holdout group the data does not contain.", M, 5.95, 12.1, 0.5,
     size=12.5, italic=True, color=BLUE)
notes(s, "This is the finding most likely to be read the wrong way. The "
         "cross-sectional curve is real but it is confounding, not causation.")

# ===================================================== 12 FINDING: CONCENTRATION
s = slide()
head(s, "A few departments carry the chain", "Finding 4")
pic(s, "pareto", M, 1.62, 8.3, 3.6)
x0 = 9.20
stat(s, x0, 1.90, 3.5, "29 of 81", "departments produce 80% of all revenue",
     color=BLUE, vsize=34)
stat(s, x0, 3.28, 3.5, "46%", "of revenue sits in the top ten departments",
     color=OCHRE, vsize=34)
stat(s, x0, 4.66, 3.5, "8.7%", "is all the bottom half contributes together",
     color=MIST, vsize=34)
text(s, "Protect assortment and shelf space in the top decile. Review the long "
        "tail for consolidation.", M, 5.48, 8.3, 0.5, size=13, italic=True,
     color=BLUE, line=1.25)
notes(s, "Department 92 alone carries 7.2% of all revenue.")

# ====================================================== 13 DIVIDER: DASHBOARD
divider("Part three", "The dashboard",
        "Everything above is on one screen, filterable, and public.",
        "The dashboard is the deliverable. The analysis behind it is only "
        "useful if someone can interrogate it without running any code.")

# ========================================================== 14 DASHBOARD LOOK
s = slide()
head(s, "How the dashboard is arranged", "The screen")
pic(s, "guide_layout", M, 1.50, 7.6, 5.3)
items = [("Filters down the left", "Store type, archetype, year, holiday or "
          "normal weeks, or one store."),
         ("Headline numbers on top", "They recompute when you change a filter."),
         ("A grid of charts", "Sixty panels across six pages. Almost no text."),
         ("Click to cross-filter", "Clicking a bar, dot or row filters "
          "everything else."),
         ("An honest badge", "Each panel says “filtered” or "
          "“full dataset”, so you always know.")]
y = 1.66
for t, d in items:
    rect(s, 8.45, y + 0.06, 0.15, 0.15, fill=OCHRE, shape=MSO_SHAPE.OVAL)
    text(s, t, 8.78, y, 3.95, 0.3, size=13, bold=True, color=INK)
    text(s, d, 8.78, y + 0.34, 3.95, 0.62, size=11, color=FADE, line=1.22)
    y += 1.07
notes(s, "Laid out like Power BI or Tableau: slicers, KPI strip, panel grid. "
         "The charts do the talking rather than paragraphs of text.")

# ============================================================ 15 SIX PAGES
s = slide()
head(s, "Six report pages", "What is on it")
pages = [("Overview", "Weekly sales, a calendar of every week, the split by "
          "store type, top stores and departments.", BLUE),
         ("Trend and forecast", "The yearly rhythm, the long-term direction, "
          "and a 14-week forecast with its accuracy test.", BLUE),
         ("Stores", "All 45 stores on one scale, size against productivity, "
          "the archetypes, a sortable scorecard.", OCHRE),
         ("Departments", "Rankings, a block chart sized by sales, holiday "
          "performance, each store's mix.", OCHRE),
         ("EDA profile", "Missing values, the shape of every column, the data "
          "quality checks.", SAGE),
         ("Statistics", "Regression, sampling, distribution fitting and the "
          "significance tests.", SAGE)]
cw, ch, gap = 3.92, 1.92, 0.22
for i, (t, d, col) in enumerate(pages):
    r, c = divmod(i, 3)
    x, y = M + c * (cw + gap), 1.66 + r * (ch + gap)
    rect(s, x, y, cw, ch, fill=PALE)
    rect(s, x + 0.26, y + 0.30, 0.42, 0.42, fill=col, shape=MSO_SHAPE.OVAL)
    text(s, str(i + 1), x + 0.26, y + 0.37, 0.42, 0.3, size=14, bold=True,
         color=WHITE, align=PP_ALIGN.CENTER, font=HEAD)
    text(s, t, x + 0.84, y + 0.34, cw - 1.1, 0.34, size=15, bold=True,
         color=INK)
    text(s, d, x + 0.28, y + 0.92, cw - 0.56, 0.9, size=11, color=FADE,
         line=1.25)
notes(s, "Each page answers one kind of question. The EDA page is unusual for "
         "a dashboard, but it lets a reader check the data before trusting "
         "the rest.")

# ============================================================== 16 THE TOOLS
s = slide()
head(s, "How it was built", "Tools")
groups = [("Analysis", "Python, pandas, NumPy, SciPy, scikit-learn", BLUE,
           "Joining, cleaning, statistics, regression and clustering"),
          ("Charts", "D3.js, Matplotlib, Plotly", OCHRE,
           "Interactive charts on the dashboard; static ones in the reports"),
          ("Delivery", "Git, GitHub, GitHub Pages, Streamlit", SAGE,
           "Version history, free public hosting, plus a Python app version")]
y = 1.66
for t, tools, col, d in groups:
    rect(s, M, y, 12.1, 1.34, fill=PALE)
    rect(s, M + 0.3, y + 0.42, 0.5, 0.5, fill=col, shape=MSO_SHAPE.OVAL)
    text(s, t, M + 1.02, y + 0.26, 2.6, 0.34, size=16, bold=True, color=INK)
    text(s, d, M + 1.02, y + 0.70, 4.6, 0.5, size=11, color=FADE, line=1.2)
    text(s, tools, M + 6.1, y + 0.48, 5.7, 0.5, size=13, color=col, bold=True)
    y += 1.50
rect(s, M, 6.22, 12.1, 0.76, fill=DARK)
text(s, "Python does the thinking once and writes 27 small tables. The browser "
        "only draws them — about 300 KB in total, which is why the "
        "dashboard opens instantly and needs no server.", M + 0.34, 6.40, 11.4,
     0.5, size=12.5, color=WHITE, line=1.2)
notes(s, "The separation between computing and drawing is the main "
         "architectural decision in the project.")

# ============================================================ 17 LIMITATIONS
s = slide()
head(s, "What to be careful about", "Limitations")
lims = [("Discounts cannot be judged here",
         "The data has no discount-free period to compare against. Bigger "
         "discounts sit alongside bigger sales, but that is mostly store size.",
         BRICK),
        ("The holiday marker is unreliable",
         "It marks a quiet week and misses the busiest week of the year. We "
         "found this during the analysis and worked around it.", BRICK),
        ("The headroom figure is a ceiling",
         "$1.69B assumes every store reaches top-quartile productivity. "
         "Catchment and competition cap what any store can do.", OCHRE),
        ("Significance is not importance",
         "At 421,570 rows nearly every test is significant. The holiday effect "
         "is real and negligible at the same time.", OCHRE),
        ("Clustering is descriptive",
         "A silhouette of 0.265 means the four archetypes overlap. They "
         "describe, they do not partition.", MIST),
        ("Two and a half years, one chain",
         "Only two complete Christmases, and the stores are anonymous with no "
         "location data.", MIST)]
cw, ch, gap = 3.92, 1.80, 0.22
for i, (t, d, col) in enumerate(lims):
    r, c = divmod(i, 3)
    card(s, M + c * (cw + gap), 1.66 + r * (ch + gap), cw, ch, t, d,
         accent=col, tsize=12.5, bsize=10.5)
notes(s, "Stating these plainly is part of the work. A result you cannot "
         "qualify is a result nobody should act on.")

# ================================================================= 18 CLOSING
s = slide(dark=True)
text(s, "SEE IT YOURSELF", M, 1.75, 8.0, 0.32, size=13, color=OCHRE, bold=True)
text(s, "The dashboard is public", M, 2.18, 10.5, 0.9, size=42, bold=True,
     font=HEAD, color=WHITE)
text(s, "No sign-in, nothing to install. It opens in any browser.", M, 3.28,
     9.0, 0.5, size=15, color=ICE)
rect(s, M, 4.00, 5.9, 1.08, fill=BLUE)
text(s, "Dashboard", M + 0.32, 4.17, 5.2, 0.3, size=11.5, color=ICE, bold=True)
text(s, LIVE, M + 0.32, 4.50, 5.3, 0.36, size=13.5, color=WHITE, bold=True)
rect(s, 6.78, 4.00, 5.9, 1.08, fill=SAGE)
text(s, "Code, data and reports", 7.10, 4.17, 5.2, 0.3, size=11.5, color=WHITE,
     bold=True)
text(s, REPO, 7.10, 4.50, 5.4, 0.36, size=13.5, color=WHITE, bold=True)
text(s, "The repository also holds three written reports: a three-page summary, "
        "a plain-language walkthrough of the process, and the full analytical "
        "write-up.", M, 5.52, 10.8, 0.8, size=13, color=MIST, line=1.3)
notes(s, "Everything in this deck is reproducible from the repository: the "
         "scripts rebuild the tables, and the tables feed the dashboard, the "
         "reports and these slides.")

prs.core_properties.author = "jeet-1236"
prs.core_properties.title = "Walmart Sales Intelligence"
prs.save(OUT)
print("wrote " + OUT + "  (" + str(round(os.path.getsize(OUT) / 1024)) + " KB)")
print("  slides: " + str(len(prs.slides.__iter__.__self__._sldIdLst)))
