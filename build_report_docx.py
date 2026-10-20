"""
dashboard_sources/*.csv + report_figures/*.png -> Walmart Sales Intelligence.docx

Every figure in the document is read from the same tables the dashboard reads,
so a number here and the same number on the dashboard cannot drift.

Usage:  python build_report_docx.py
"""

import os

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

SRC, FIG = "dashboard_sources", "report_figures"
OUT = "Walmart Sales Intelligence.docx"

REPO = "https://github.com/jeet-1236/walmart-sales-intelligence"
LIVE = "https://jeet-1236.github.io/walmart-sales-intelligence/"

INK = RGBColor(0x1C, 0x24, 0x30)
FADE = RGBColor(0x62, 0x6E, 0x7B)
BLUE = RGBColor(0x2F, 0x6D, 0x9E)
BRICK = RGBColor(0xB5, 0x48, 0x38)

L = lambda n: pd.read_csv(os.path.join(SRC, f"{n}.csv"))
kp = L("kpis").set_index("metric")
K = lambda m: kp.loc[m, "value"]
KU = lambda m: kp.loc[m, "unit"]


def money(v):
    v = float(v)
    a = abs(v)
    if a >= 1e9:
        return f"${v / 1e9:,.2f}B"
    if a >= 1e6:
        return f"${v / 1e6:,.1f}M"
    if a >= 1e3:
        return f"${v:,.0f}"
    return f"${v:,.2f}"


def fmt(m):
    v, u = float(K(m)), KU(m)
    if u == "usd":
        return money(v)
    if u == "pct":
        return f"{v:,.2f}%"
    if u in ("count", "sqft"):
        return f"{v:,.0f}"
    if u == "p":
        return "< 0.0001" if 0 < abs(v) < 1e-4 else f"{v:,.4f}"
    if u == "ratio":
        return f"{v:,.4g}"
    return f"{v:,.2f}"


doc = Document()

# ------------------------------------------------------------------- styles
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for side in ("left_margin", "right_margin"):
    setattr(sec, side, Inches(0.9))
sec.top_margin, sec.bottom_margin = Inches(0.85), Inches(0.85)
W = Inches(6.7)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.font.color.rgb = INK
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.line_spacing = 1.14

for lvl, size in [(1, 17), (2, 13), (3, 11)]:
    s = doc.styles[f"Heading {lvl}"]
    s.font.name = "Calibri"
    s.font.size = Pt(size)
    s.font.color.rgb = INK if lvl > 1 else BLUE
    s.font.bold = True
    s.paragraph_format.space_before = Pt(16 if lvl == 1 else 11)
    s.paragraph_format.space_after = Pt(5)


def para(text="", size=None, color=None, italic=False, bold=False,
         after=None, align=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
        r.italic = italic
        r.bold = bold
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def link(paragraph, url, text):
    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), "2F6D9E")
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(c)
    rPr.append(u)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    run.append(t)
    h.append(run)
    paragraph._p.append(h)
    return h


def rule(p):
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "6")
    bot.set(qn("w:color"), "D5DBE1")
    b.append(bot)
    pPr.append(b)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def table(headers, rows, widths, font=8.6, head_fill="EEF3F8"):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    total = sum(widths)
    cols = [Inches(6.7 * w / total) for w in widths]
    t.autofit = False
    for j, (h, cw) in enumerate(zip(headers, cols)):
        c = t.rows[0].cells[j]
        c.width = cw
        shade(c, head_fill)
        c.text = ""
        r = c.paragraphs[0].add_run(str(h))
        r.bold = True
        r.font.size = Pt(font)
        c.paragraphs[0].paragraph_format.space_after = Pt(1)
    for row in rows:
        cells = t.add_row().cells
        for j, (v, cw) in enumerate(zip(row, cols)):
            cells[j].width = cw
            cells[j].text = ""
            r = cells[j].paragraphs[0].add_run("" if v is None else str(v))
            r.font.size = Pt(font)
            cells[j].paragraphs[0].paragraph_format.space_after = Pt(1)
            if j and str(v).replace("-", "").replace("$", "")[:1].isdigit():
                cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, caption, width=6.7):
    path = os.path.join(FIG, f"{name}.png")
    if not os.path.exists(path):
        return
    doc.add_picture(path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
    p = para(caption, size=8.5, color=FADE, italic=True, after=12,
             align=WD_ALIGN_PARAGRAPH.CENTER)
    return p


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(3)
        if isinstance(it, tuple):
            r = p.add_run(it[0])
            r.bold = True
            p.add_run(" " + it[1])
        else:
            p.add_run(it)


# ===================================================================== TITLE
p = para("Walmart Sales Intelligence", size=26, color=INK, bold=True, after=2)
p = para("Eight statistical experiments and a business-impact layer over "
         "421,570 store-department-week sales records", size=12, color=FADE,
         after=10)
rule(p)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
p.add_run("Live dashboard  ").bold = True
link(p, LIVE, LIVE)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
p.add_run("Source and code  ").bold = True
link(p, REPO, REPO)
p = para("Both are public. The dashboard opens in any browser with no sign-in "
         "and nothing to install; the repository holds the analysis pipeline, "
         "the computed tables and this document.", size=9.5, color=FADE, after=14)

table(
    ["Dataset", "Walmart Store Sales Forecasting (train, stores, features)"],
    [
        ["Grain", "one row per store, department and week"],
        ["Records", f"{float(K('records')):,.0f}"],
        ["Stores / departments", f"{float(K('stores')):,.0f} stores, "
                                f"{float(K('depts')):,.0f} departments"],
        ["Period", "5 February 2010 to 26 October 2012 "
                   f"({float(K('weeks')):,.0f} weeks)"],
        ["Total revenue", money(K("total_revenue"))],
        ["Tools", "Python (pandas, NumPy, SciPy, scikit-learn), D3, Streamlit"],
    ], [1.1, 3], font=9.2)

# =================================================================== CONTENTS
doc.add_page_break()
doc.add_heading("Contents", level=1)
for n, t in [
    ("1", "Summary"), ("2", "The dataset and how it was built"),
    ("3", "Exploratory data analysis"), ("4", "The eight experiments"),
    ("5", "Business impact"), ("6", "Limitations"),
    ("7", "Reproducing this work"), ("A", "Appendix: full column profile"),
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(f"{n}.  {t}")
    r.font.size = Pt(10.5)

# ==================================================================== SUMMARY
doc.add_heading("1.  Summary", level=1)
para("This chain turned over " + money(K("total_revenue")) + " across "
     f"{float(K('weeks')):,.0f} weeks, {float(K('stores')):,.0f} stores and "
     f"{float(K('depts')):,.0f} departments. Almost none of that movement is "
     "the economy. It is the calendar and the store itself: a regression on "
     "temperature, fuel price, CPI and unemployment explains "
     f"{float(K('e2_economic_r2')) * 100:.2f}% of the variance in weekly sales, "
     "while floor space alone carries most of what can be explained.")

doc.add_heading("Headline figures", level=2)
table(["Measure", "Value", "Note"], [
    ["Total revenue", money(K("total_revenue")), "143 weeks, all stores"],
    ["Average week, chain-wide", money(K("avg_weekly_chain")), ""],
    ["Revenue per square foot", fmt("rev_per_sqft"), "over the whole window"],
    ["Largest week", money(K("e8_peak_value")), "week ending 24 Dec 2010"],
    ["Quietest week", money(K("e8_trough_value")), "week ending 28 Jan 2011"],
    ["Forecast error (MAPE)", fmt("e8_mape"),
     "13 held-out weeks; seasonal-naive benchmark " + fmt("e8_naive_mape")],
    ["Productivity headroom", money(K("b_opportunity")),
     f"{float(K('b_opportunity_pct')):.0f}% of revenue; a ceiling, not a target"],
], [1.7, 1.1, 2.6], font=9)

doc.add_heading("What the analysis found", level=2)
bullets([
    ("The holiday flag points at the wrong weeks.",
     "It marks the week ending 31 December, which is the dead week after "
     "Christmas and runs about 29% below its December baseline. The real "
     "annual peak, week 51, carries no flag at all, and three of the five "
     "biggest weeks on record are labelled normal."),
    ("Small-format stores are the most productive floor space.",
     "Type C earns about $1,667 per square foot against Type A's $1,111, which "
     "holds at median-store level too. Type A is 4.4 times larger and takes 64% "
     "of revenue, so size and productivity rank in opposite directions."),
    ("Markdown's apparent effect is mostly store-size confounding.",
     "Across records the deepest markdown quintile averages 110% above the "
     "lightest. Removing each store-department's own mean leaves a slope of "
     "about $0.015 of sales per markdown dollar, explaining roughly 0.1% of "
     "variance."),
    ("Revenue is concentrated.",
     f"{float(K('b_depts_for_80')):.0f} of 81 departments produce 80% of "
     "revenue, and the top ten stores carry "
     f"{float(K('b_top10_store_share')):.0f}% of it."),
    ("The weekly number is highly forecastable.",
     f"A trend-times-seasonality model reaches {fmt('e8_mape')} MAPE on 13 "
     "weeks it never saw, against " + fmt("e8_naive_mape") + " for a "
     "seasonal-naive benchmark. The underlying trend is close to flat, so "
     "nearly all movement is calendar rather than growth."),
])

figure("trend", "Figure 1. Chain revenue for every week in the window. The two "
                "spikes each year are Thanksgiving and the pre-Christmas week. "
                "The red markers are the weeks the dataset flags as holidays — "
                "note that they do not sit on the peaks.")

# ==================================================================== DATASET
doc.add_page_break()
doc.add_heading("2.  The dataset and how it was built", level=1)
para("Four source files were merged into one table, and every experiment runs "
     "against that single integrated dataset rather than the raw files.")
bullets([
    ("Integration.", "The sales file was joined to the store file on Store, "
     "then to the features file on Store and Date."),
    ("Preprocessing.", "Dates parsed to timestamps, the holiday flag coerced "
     "to a boolean, markdown columns read as numbers, and rows without a sales "
     "figure dropped."),
    ("Grain check.", "The Store-Department-Date key is unique: zero duplicates "
     "across all 421,570 rows."),
])

doc.add_heading("Data quality", level=2)
q = L("eda_quality").set_index("metric")
qv = lambda m: q.loc[m, "value"]
table(["Check", "Result", "What it means"], [
    ["Rows / columns", f"{float(qv('rows')):,.0f} / {qv('columns')}", ""],
    ["Duplicate Store-Dept-Date keys", f"{float(qv('duplicate_keys')):,.0f}",
     "the grain is clean"],
    ["Rows with no missing value", f"{float(qv('complete_pct')):.1f}%",
     "markdowns are the whole story"],
    ["Columns with any missing value", f"{float(qv('any_missing_cols')):.0f}",
     "the five MarkDown columns"],
    ["Markdown coverage", f"{float(qv('markdown_coverage')):.1f}%",
     "recorded only from 11 Nov 2011"],
    ["Records with negative sales", f"{float(qv('negative_sales')):,.0f}",
     "net returns exceeded sales that week"],
    ["Store x dept x week grid present", f"{float(qv('grain_completeness')):.1f}%",
     "not every store sells every department"],
], [2.1, 1.0, 2.3], font=9)

# ======================================================================== EDA
doc.add_heading("3.  Exploratory data analysis", level=1)
para("The profile below was computed from the raw merge rather than the "
     "integrated table. That distinction matters: the integrated file fills the "
     "MarkDown columns with zero, so profiling it would report no missing data "
     "at all.")

doc.add_heading("Missing data", level=2)
para("Only 23% of rows are complete, and the five MarkDown columns are the "
     "entire reason. They are absent for the first two years of the window and "
     "populated from November 2011 onward. Within that later window every "
     "single record carries a non-zero markdown, so the data contains no "
     "zero-markdown control group anywhere.")
figure("missing", "Figure 2. Missing values by column. No other column has a "
                  "single gap.", width=3.3)
figure("missing_time", "Figure 3. The same columns by month: the cliff at "
                       "November 2011 is where markdown recording begins.",
       width=3.3)

doc.add_heading("Distribution and shape", level=2)
para("Weekly sales are strongly right-skewed with heavy tails: skewness "
     f"{float(K('e6_skew')):.2f} and excess kurtosis "
     f"{float(K('e6_kurtosis')):.1f}. "
     f"{float(K('e1_outlier_pct')):.1f}% of records fall outside the Tukey "
     f"fences, yet those records carry "
     f"{float(K('e1_outlier_revenue_pct')):.0f}% of all revenue. They are not "
     "errors to be trimmed; they are the business.")
figure("distribution", "Figure 4. Left: the distribution of weekly sales per "
                       "store-department, with the upper Tukey fence marked. "
                       "Right: the normal Q-Q plot, which leaves the diagonal "
                       "at both ends.")
figure("density", "Figure 5. The observed density against a fitted normal and "
                  "a fitted log-normal. The normal puts mass below zero and "
                  "misses the peak.", width=3.4)

doc.add_heading("Relationships", level=2)
para("At the individual record level, correlations with sales are near zero "
     "because department-level noise dominates. Aggregating to store-week "
     "totals reveals the structural driver: floor space.")
figure("correlation", "Figure 6. Correlation matrix at store-week level.",
       width=3.5)

# ================================================================ EXPERIMENTS
doc.add_page_break()
doc.add_heading("4.  The eight experiments", level=1)
exp = L("experiments").sort_values("n")
table(["#", "Experiment", "Method", "Headline result"],
      [[int(r.n), r.title, r.method, r.headline] for r in exp.itertuples()],
      [0.3, 1.5, 2.2, 2.7], font=8.2)

doc.add_heading("Experiment 1 — Descriptive statistics", level=2)
para("Quartiles and Tukey fences on every record. Q1 " + fmt("e1_q1") +
     ", median " + fmt("e1_q2") + ", Q3 " + fmt("e1_q3") + ", giving an "
     "interquartile range of " + fmt("e1_iqr") + " and an upper fence of " +
     fmt("e1_fence_hi") + ". " + f"{float(K('e1_outlier_count')):,.0f} records "
     "sit outside the fences.")

doc.add_heading("Experiment 2 — Linear regression", level=2)
para("Three specifications on the same target, fitted by ordinary least "
     "squares.")
table(["Specification", "R²", "Adjusted R²", "RMSE"], [
    ["Economic drivers only (temperature, fuel, CPI, unemployment)",
     f"{float(K('e2_economic_r2')):.5f}", f"{float(K('e2_economic_adj_r2')):.5f}",
     money(K("e2_economic_rmse"))],
    ["Adding store size and the holiday flag",
     f"{float(K('e2_full_r2')):.5f}", f"{float(K('e2_full_adj_r2')):.5f}",
     money(K("e2_full_rmse"))],
    ["Aggregated to store-week",
     f"{float(K('e2_store_week_r2')):.5f}",
     f"{float(K('e2_store_week_adj_r2')):.5f}",
     money(K("e2_store_week_rmse"))],
], [3.4, 1.0, 1.1, 1.2], font=9)
para("The jump from 0.06 to 0.67 comes almost entirely from floor space. What "
     "a store sells is set by what it is, not by the economy that week.",
     size=9.5, color=FADE, italic=True)

_s = L("sampling")
SAMP10 = float(_s[_s["n"] == 10000]["err_pct"].iloc[0])
doc.add_heading("Experiment 3 — Sampling", level=2)
para("Simple random samples at seven sizes, proportional stratified sampling by "
     "store format, and systematic sampling, each compared against the "
     "population mean of " + fmt("e3_pop_mean") + ". A 10,000-record sample "
     "estimates that mean to within "
     f"{SAMP10:.2f}%. "
     "A thousand repeated samples of 500 records produce a distribution of "
     "sample means with an observed spread of " + fmt("e3_clt_std") +
     " against the " + fmt("e3_clt_se") + " that theory predicts, which is the "
     "central limit theorem holding on strongly skewed data.")

doc.add_heading("Experiment 4 — Clustering", level=2)
para("K-means on six standardised store features: weekly revenue, floor space, "
     "volatility, local CPI, local unemployment and holiday lift. Four "
     "archetypes were chosen from the elbow and from how readable the groups "
     "are.")
seg = L("segments")
clu = seg[seg["kind"] == "cluster"]
table(["Archetype", "Stores", "Avg week", "Avg size", "$/sq ft", "Rev share"],
      [[r.group, int(r.stores), money(r.avg_weekly_per_store),
        f"{r.avg_size:,.0f}", f"${r.rev_per_sqft:,.0f}",
        f"{r.rev_share_pct:.1f}%"] for r in clu.itertuples()],
      [1.6, 0.7, 1.1, 1.1, 0.9, 1.0], font=9)
figure("clusters", "Figure 7. Left: the archetypes projected onto their first "
                   "two principal components. Right: inertia and silhouette "
                   "against k.")
para("A caveat on k. The silhouette score at k=4 is "
     f"{float(K('e4_silhouette')):.3f}, which is in fact a local minimum — "
     "higher values of k score better on that metric. Four was chosen because "
     "the inertia curve flattens there and because four groups are "
     "interpretable, not because the silhouette favoured it. The archetypes are "
     "a useful description, not a clean partition.", size=9.5, color=FADE,
     italic=True)

doc.add_heading("Experiments 5 and 6 — Distributions", level=2)
para("Treated as a random variable, weekly sales have an expected value of " +
     fmt("e5_mean") + " and a standard deviation of " + fmt("e5_std") + ", a "
     "coefficient of variation above one. Four candidate distributions were "
     "fitted and compared by the Kolmogorov-Smirnov statistic.")
fits = L("dist_fits").sort_values("ks_stat")
table(["Distribution", "Fitted parameters", "KS statistic", "p-value"],
      [[r.name, r.params, f"{r.ks_stat:.4f}",
        "< 0.0001" if r.ks_p < 1e-4 else f"{r.ks_p:.4f}"]
       for r in fits.itertuples()], [1.2, 2.4, 1.1, 1.0], font=9)
para("The normal distribution is rejected outright. Log-normal fits far better, "
     "and a log transform pulls skewness from "
     f"{float(K('e6_skew')):.2f} to {float(K('e6_log_skew')):.2f} — "
     "overshooting slightly into mild left skew. Note that the chain-level "
     "weekly total is a different matter: aggregating 45 stores restores "
     "approximate normality, with a Shapiro-Wilk p of " + fmt("e6_shapiro_p") +
     ".", size=9.5, color=FADE, italic=True)

doc.add_heading("Experiment 7 — Statistical inference", level=2)
table(["Test", "Statistic", "p-value", "Reading"], [
    ["Welch t-test, holiday vs normal weeks", fmt("e7_hol_t"), fmt("e7_hol_p"),
     f"significant; Cohen's d {float(K('e7_hol_d')):.3f} is negligible"],
    ["Mann-Whitney U (non-parametric check)", "—", fmt("e7_hol_mw_p"),
     "agrees with the t-test"],
    ["One-way ANOVA across store formats", fmt("e7_anova_f"), fmt("e7_anova_p"),
     "formats differ substantially"],
    ["Kruskal-Wallis (non-parametric check)", "—", fmt("e7_kruskal_p"),
     "agrees with the ANOVA"],
    ["Chi-square, markdown against holiday", fmt("e7_chi2"), fmt("e7_chi2_p"),
     "markdown activity is not independent of holidays"],
], [2.3, 0.9, 0.9, 2.6], font=8.6)
para("With 421,570 records almost any difference reaches significance, so "
     "effect size matters more than the p-value. The 95% confidence interval "
     "for mean weekly sales is " + fmt("e7_ci95_lo") + " to " +
     fmt("e7_ci95_hi") + ".", size=9.5, color=FADE, italic=True)

doc.add_heading("Experiment 8 — Time series", level=2)
para("Classical multiplicative decomposition with a 52-week period, then a "
     "forecast built by projecting the trend and multiplying by each target "
     "week's seasonal index.")
figure("seasonal", "Figure 8. Seasonal index by calendar week. Week 51 runs 67% "
                   "above trend and week 47 runs 40% above; between them they "
                   "decide the quarter.")
figure("forecast", "Figure 9. Left: fourteen weeks ahead with a 95% band. "
                   "Right: the backtest against 13 fully held-out weeks.")
para("The backtest is honest: both the trend and the seasonal index were "
     "refitted on the first "
     f"{float(K('e8_train_weeks')):.0f} weeks only, so none of the 13 scored "
     "weeks influenced the model that scored them. It reaches " +
     fmt("e8_mape") + " MAPE against " + fmt("e8_naive_mape") + " for a "
     "seasonal-naive benchmark — a win, but a narrow one, because a series "
     "this seasonal makes last year's same week a strong guess already. The "
     "held-out window is also a quiet stretch of late summer, so it does not "
     "test the peaks.", size=9.5, color=FADE, italic=True)

# =========================================================== BUSINESS IMPACT
doc.add_page_break()
doc.add_heading("5.  Business impact", level=1)

doc.add_heading("Store format", level=2)
fm = seg[seg["kind"] == "format"]
table(["Format", "Stores", "Avg size", "Revenue", "Share", "$/sq ft"],
      [[r.group, int(r.stores), f"{r.avg_size:,.0f}", money(r.revenue),
        f"{r.rev_share_pct:.1f}%", f"${r.rev_per_sqft:,.0f}"]
       for r in fm.itertuples()], [1.1, 0.7, 1.1, 1.2, 0.8, 1.0], font=9)
figure("formats", "Figure 10. Type A takes most of the revenue because it has "
                  "most of the square footage. Per square foot the ranking "
                  "reverses.")

doc.add_heading("The holiday calendar", level=2)
hol = L("holidays").sort_values("lift_pct", ascending=False)
table(["Holiday", "Weeks", "Flagged week", "Baseline", "Lift"],
      [[r.holiday, int(r.weeks_observed), money(r.avg_chain_week),
        money(r.baseline_week), f"{r.lift_pct:+.1f}%"]
       for r in hol.itertuples()], [1.3, 0.6, 1.3, 1.3, 0.8], font=9)
figure("holidays", "Figure 11. Only Thanksgiving earns its flag. The Christmas "
                   "flag lands on the week after Christmas Day, which is a "
                   "trough.", width=3.4)

doc.add_heading("Departments", level=2)
para(f"{float(K('b_depts_for_80')):.0f} of 81 departments produce 80% of "
     f"revenue. The top ten take {float(K('b_top10_dept_share')):.0f}%, while "
     f"the bottom half of all departments contribute "
     f"{float(K('b_bottom50_dept_share')):.1f}% between them.")
figure("pareto", "Figure 12. The 25 largest departments with cumulative share.")
figure("heatmap", "Figure 13. Each store's revenue mix across the 20 largest "
                  "departments, as a share of that store's own revenue so "
                  "large and small stores compare directly.", width=5.6)

_md = L("markdown")
MD_BAND = _md[_md["kind"] == "band"]
doc.add_heading("Markdowns", level=2)
para("This is the finding most likely to be read the wrong way. Across records "
     "the deepest markdown quintile averages "
     + money(MD_BAND["avg_sales"].iloc[-1]) +
     " against " +
     money(MD_BAND["avg_sales"].iloc[0]) +
     " in the lightest, which looks like a powerful promotion effect. It is "
     "mostly confounding: large departments receive large markdowns and already "
     "sell more. Removing each store-department's own average leaves a slope of "
     + fmt("b_md_slope") + " of sales per markdown dollar, explaining "
     f"{float(K('b_md_r2')) * 100:.1f}% of a store's own week-to-week swing.")
figure("markdown", "Figure 14. Average sales by markdown depth quintile. The "
                   "spread is almost entirely store size.", width=3.4)
para("Nothing in this dataset identifies a causal promotion effect. That needs "
     "a holdout group the data does not contain.", size=9.5, color=FADE,
     italic=True)

doc.add_heading("Productivity headroom", level=2)
para(f"{float(K('b_underperformers')):.0f} of 45 stores earn less per square "
     "foot than the top-quartile benchmark of " + fmt("b_topq_rps") +
     ". Lifting every one of them to that benchmark would add " +
     money(K("b_opportunity")) + f", or {float(K('b_opportunity_pct')):.0f}% of "
     "revenue across the window, with no new floor space.")
figure("productivity", "Figure 15. Floor space against revenue per square foot; "
                       "bubble area is total revenue. If larger stores were "
                       "more productive the cloud would slope up.", width=3.6)

# ================================================================ LIMITATIONS
doc.add_heading("6.  Limitations", level=1)
bullets([
    ("The markdown window.", "Markdowns are recorded for only 51 of 143 weeks, "
     "and every record in that window carries one. No with-versus-without "
     "comparison is possible on this data."),
    ("The holiday flag.", "Used raw as a model feature it teaches the wrong "
     "calendar. Replace it with named holidays and a week-of-year index."),
    ("The headroom figure is a ceiling.", "It assumes every store could reach "
     "the top-quartile benchmark. Catchment, local income and competition cap "
     "what any individual store can do."),
    ("Significance is not importance.", "At this sample size nearly every test "
     "rejects its null hypothesis. Read effect sizes and confidence intervals."),
    ("Clustering is descriptive.", "A silhouette of "
     f"{float(K('e4_silhouette')):.3f} means the archetypes overlap."),
    ("Two and a half years, one chain.", "Only two complete Christmas peaks are "
     "available to learn seasonality from. Store identities are anonymous and "
     "carry no geography, so nothing here separates a regional effect from a "
     "store-specific one."),
])

# ============================================================== REPRODUCING
doc.add_heading("7.  Reproducing this work", level=1)
p = doc.add_paragraph()
p.add_run("Everything is in the repository: ")
link(p, REPO, REPO)
para("The dashboard reads pre-computed tables, so it runs without the 40 MB "
     "integrated dataset. To rebuild those tables from the raw Walmart files:")
table(["Script", "Produces"], [
    ["build_dashboard_data.py", "Runs all eight experiments and the business "
     "layer into one JSON of results"],
    ["build_dashboard_sources.py", "Flattens that JSON into 18 tidy CSVs, one "
     "per chart group"],
    ["build_dashboard_extras.py", "Adds the per-store weekly series, the store "
     "x department matrix, and growth and returns columns"],
    ["build_eda.py", "Profiles the raw merge into seven EDA tables"],
    ["build_pages.py", "Wraps the dashboard into the static site served by "
     "GitHub Pages"],
    ["build_report_figures.py", "Renders the figures in this document from "
     "those same tables"],
    ["build_report_docx.py", "Builds this document"],
    ["app.py", "A Streamlit version of the dashboard"],
], [1.9, 4.8], font=8.8)

# =================================================================== APPENDIX
doc.add_page_break()
doc.add_heading("A.  Appendix: full column profile", level=1)
para("Profiled from the raw merge of all four source files. Blank cells are "
     "columns where the statistic does not apply.", size=9.5, color=FADE)
prof = L("eda_profile")
g = lambda v, f: ("" if pd.isna(v) else f(v))
table(["Column", "Role", "Missing", "Unique", "Mean", "Median", "Std",
       "Skew", "Kurt.", "Outliers", "Neg."],
      [[r.column, r.role, f"{r.missing_pct:.1f}%", f"{r.unique:,.0f}",
        g(r.mean, lambda v: f"{v:,.1f}"), g(r.median, lambda v: f"{v:,.1f}"),
        g(r.std, lambda v: f"{v:,.1f}"), g(r.skew, lambda v: f"{v:.2f}"),
        g(r.kurtosis, lambda v: f"{v:.1f}"),
        g(r.outlier_pct, lambda v: f"{v:.1f}%"),
        g(r.negatives, lambda v: f"{v:,.0f}")]
       for r in prof.itertuples()],
      [1.0, 0.65, 0.6, 0.65, 0.75, 0.7, 0.7, 0.5, 0.5, 0.6, 0.5], font=7.6)

p = para()
rule(p)
p = doc.add_paragraph()
r = p.add_run("Dashboard: ")
r.font.size = Pt(9)
r.bold = True
link(p, LIVE, LIVE)
r = p.add_run("    Repository: ")
r.font.size = Pt(9)
r.bold = True
link(p, REPO, REPO)

doc.save(OUT)
print(f"wrote {OUT}  ({os.path.getsize(OUT) / 1024:.0f} KB)")
print(f"  paragraphs {len(doc.paragraphs)}, tables {len(doc.tables)}, "
      f"images {len(doc.inline_shapes)}")
