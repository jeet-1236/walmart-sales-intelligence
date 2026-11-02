"""
Builds "Project Summary.docx" - a short version: what we did, which dataset,
what preprocessing, and what the dashboard looks like.

Usage:  python build_summary_docx.py
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
OUT = "Project Summary.docx"
REPO = "https://github.com/jeet-1236/walmart-sales-intelligence"
LIVE = "https://jeet-1236.github.io/walmart-sales-intelligence/"

INK, FADE = RGBColor(0x1C, 0x24, 0x30), RGBColor(0x62, 0x6E, 0x7B)
BLUE = RGBColor(0x2F, 0x6D, 0x9E)

L = lambda n: pd.read_csv(os.path.join(SRC, n + ".csv"))
kp = L("kpis").set_index("metric")
K = lambda m: float(kp.loc[m, "value"])
q = L("eda_quality").set_index("metric")
Q = lambda m: q.loc[m, "value"]

doc = Document()
s = doc.sections[0]
s.page_width, s.page_height = Inches(8.5), Inches(11)
s.left_margin = s.right_margin = Inches(0.95)
s.top_margin = s.bottom_margin = Inches(0.8)

n = doc.styles["Normal"]
n.font.name = "Calibri"
n.font.size = Pt(10.5)
n.font.color.rgb = INK
n.paragraph_format.space_after = Pt(7)
n.paragraph_format.line_spacing = 1.15

for lvl, size, col in [(1, 14, BLUE), (2, 11.5, INK)]:
    st = doc.styles["Heading " + str(lvl)]
    st.font.name = "Calibri"
    st.font.size = Pt(size)
    st.font.color.rgb = col
    st.font.bold = True
    st.paragraph_format.space_before = Pt(13 if lvl == 1 else 9)
    st.paragraph_format.space_after = Pt(4)


def para(text="", size=None, color=None, italic=False, bold=False, after=None,
         align=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
        r.italic, r.bold = italic, bold
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def link(paragraph, url, text):
    rid = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
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


def rule(p):
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "6")
    bot.set(qn("w:color"), "D5DBE1")
    b.append(bot)
    pPr.append(b)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), fill)
    tcPr.append(sh)


def table(headers, rows, widths, font=8.8):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    total = sum(widths)
    cols = [Inches(6.6 * w / total) for w in widths]
    for j, (h, cw) in enumerate(zip(headers, cols)):
        c = t.rows[0].cells[j]
        c.width = cw
        shade(c, "EEF3F8")
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
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def figure(name, caption, width=6.6):
    path = os.path.join(FIG, name + ".png")
    if not os.path.exists(path):
        return
    doc.add_picture(path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_after = Pt(2)
    para(caption, size=8.5, color=FADE, italic=True, after=9,
         align=WD_ALIGN_PARAGRAPH.CENTER)


def bullets(items, after=4):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(after)
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(" " + it[1])
        else:
            p.add_run(it)


# ======================================================================= HEAD
para("Walmart Sales Dashboard", size=21, bold=True, after=1)
p = para("A short summary: what we did, the dataset, the preprocessing, and "
         "the dashboard", size=10.5, color=FADE, after=8)
rule(p)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
p.add_run("Dashboard  ").bold = True
link(p, LIVE, LIVE)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(11)
p.add_run("Code  ").bold = True
link(p, REPO, REPO)

# ================================================================== WHAT/WHY
doc.add_heading("What we did", level=1)
para("We took four Walmart sales spreadsheets, joined them into one table, "
     "cleaned it, ran eight pieces of statistical analysis on it, and built an "
     "interactive dashboard that anyone can open in a browser. The whole "
     "pipeline is five steps:")
bullets([
    ("Collect.", "Four CSV files covering sales, stores and weekly conditions."),
    ("Join.", "Merge them into one table where each row is one department, in "
     "one store, in one week."),
    ("Clean.", "Fix data types, handle the missing values, and add the extra "
     "columns the analysis needs."),
    ("Analyse.", "Eight experiments: descriptive statistics, regression, "
     "sampling, clustering, probability, distribution fitting, hypothesis "
     "testing and time series forecasting."),
    ("Publish.", "Save every result as a small table, then draw those tables "
     "as an interactive dashboard hosted free on GitHub Pages."),
])

# ==================================================================== DATASET
doc.add_heading("The dataset", level=1)
para("Walmart Store Sales Forecasting, a public dataset of weekly sales from "
     "45 stores. It comes as four files.")
table(["File", "What it holds", "Used?"], [
    ["train.csv", "Weekly sales per store and department "
     "(" + format(int(K("records")), ",") + " rows). The main file.", "Yes"],
    ["stores.csv", "One row per store: type (A, B or C) and size in square "
     "feet.", "Yes"],
    ["features.csv", "Per store per week: temperature, fuel price, CPI, "
     "unemployment and five markdown columns.", "Yes"],
    ["test.csv", "Same shape as train but with no sales column.",
     "No — nothing to analyse"],
], [0.9, 4.2, 1.1])

table(["After joining", ""], [
    ["Rows × columns",
     format(int(K("records")), ",") + " × 16"],
    ["Stores / departments",
     format(int(K("stores")), ",") + " stores, "
     + format(int(K("depts")), ",") + " departments"],
    ["Time span", "5 Feb 2010 to 26 Oct 2012 ("
     + format(int(K("weeks")), ",") + " weeks)"],
    ["One row means", "one department, in one store, in one week"],
    ["Total sales covered", "$" + "{:.2f}".format(K("total_revenue") / 1e9)
     + " billion"],
], [1.5, 5.1], font=9)

# ============================================================== PREPROCESSING
doc.add_heading("Preprocessing we applied", level=1)
para("These are the actual techniques used, and why each was needed.")
table(["Technique", "What we did", "Why"], [
    ["Merging / joining",
     "Joined sales to stores on Store, then to features on Store + Date.",
     "To get everything in one table. The second join needs both keys because "
     "conditions change every week."],
    ["Type conversion",
     "Dates from text to datetime; the holiday flag from TRUE/FALSE text to "
     "boolean; markdown columns from text to numbers.",
     "So dates can be sorted and compared, and numbers can be calculated with."],
    ["Missing value handling",
     "Dropped rows with no sales figure. Left markdown gaps as missing for the "
     "data profile, and filled them with 0 in the analysis table.",
     "Markdowns are " + "{:.0f}".format(100 - float(Q("markdown_coverage")))
     + "% missing before Nov 2011. We kept both views so the gap stays visible."],
    ["Feature engineering",
     "Added Year, Month, Week-of-year, TotalMarkDown (the five markdown "
     "columns summed) and a yes/no HasMarkDown flag.",
     "The calendar columns drive the seasonal analysis; the totals simplify "
     "the promotion analysis."],
    ["Duplicate check",
     "Verified the Store + Department + Date key appears exactly once.",
     "A bad join silently duplicates rows and inflates every total."],
    ["Aggregation",
     "Built store-week, store-department and chain-week summary tables.",
     "Different questions need different levels of detail."],
    ["Outlier detection",
     "Flagged values outside the Tukey fences (1.5 × the interquartile "
     "range). We kept them.",
     "{:.1f}".format(K("e1_outlier_pct")) + "% of rows are outliers but they "
     "carry " + "{:.0f}".format(K("e1_outlier_revenue_pct")) + "% of the "
     "money. Removing them would delete Christmas."],
    ["Standardisation",
     "Rescaled the six clustering features to a common scale before K-Means.",
     "Store size is in the hundreds of thousands and unemployment is single "
     "digits. Without rescaling, size would decide every cluster."],
    ["Dimensionality reduction",
     "Used PCA to squeeze six features into two for plotting.",
     "You cannot draw six dimensions. Two can be shown as a scatter plot."],
    ["Sampling",
     "Drew random, stratified and systematic samples of several sizes.",
     "To check whether a sample gives the same answer as the full dataset."],
    ["Log transform",
     "Tested log of sales as an alternative to raw sales.",
     "Sales are heavily lopsided; the log makes the spread more even."],
    ["Within-group centring",
     "Subtracted each store-department's own average before measuring the "
     "markdown effect.",
     "Otherwise you are just comparing big departments with small ones."],
    ["Train / holdout split",
     "Hid the final 13 weeks and rebuilt the forecast on the earlier weeks "
     "only.",
     "Testing a forecast on data it already learned from gives a false result."],
], [1.3, 2.7, 2.6], font=8.3)

# ================================================================== DASHBOARD
doc.add_page_break()
doc.add_heading("How the dashboard looks", level=1)
para("It is laid out like Power BI or Tableau: filters down the left, headline "
     "numbers across the top, and a grid of charts filling the rest. There is "
     "almost no text on it — the charts do the talking.")
figure("guide_layout", "The parts of the screen.")

doc.add_heading("Six pages", level=2)
table(["Page", "Shows"], [
    ["Overview", "Weekly sales, a calendar of every week, the split by store "
     "type, top stores and departments, and the main findings."],
    ["Trend and forecast", "The yearly rhythm, the long-term direction, and a "
     "14-week forecast with its accuracy test."],
    ["Stores", "All 45 stores as small charts on one scale, size against "
     "productivity, the store groups, and a sortable table."],
    ["Departments", "Rankings, a block chart sized by sales, holiday "
     "performance, and each store's department mix."],
    ["EDA profile", "Missing values, the shape of every column, and the data "
     "quality checks."],
    ["Statistics", "The regression, sampling, distribution fitting and "
     "significance tests."],
], [1.3, 5.3], font=9)

doc.add_heading("What you can do on it", level=2)
bullets([
    ("Filter.", "Pick a store type, a store group, a year, holiday or normal "
     "weeks, or one single store. The headline numbers and charts redraw "
     "immediately."),
    ("Hover.", "Point at any chart for the exact figures."),
    ("Click to filter.", "Clicking a bar, a dot or a table row filters the "
     "rest of the screen."),
    ("Check the badge.", "Each chart is labelled " + chr(8220) + "filtered"
     + chr(8221) + " or " + chr(8220) + "full dataset" + chr(8221) + ", so you "
     "always know whether your filter applies to it."),
], after=3)

doc.add_heading("Tools used", level=2)
para("Python with pandas, NumPy, SciPy and scikit-learn for the analysis; "
     "Matplotlib for the report charts; D3.js for the interactive dashboard; "
     "Streamlit and Plotly for a second Python version; Git, GitHub and GitHub "
     "Pages for storing and publishing it.", after=10)

p = para()
rule(p)
para("A longer walkthrough of the process is in " + chr(8220)
     + "From Dataset to Dashboard" + chr(8221) + ", and the full results are "
     "in " + chr(8220) + "Walmart Sales Intelligence" + chr(8221)
     + ". Both are in the repository.", size=9, color=FADE, italic=True)

cp = doc.core_properties
cp.author = "jeet-1236"
cp.last_modified_by = "jeet-1236"
cp.title = OUT.replace(".docx", "")

doc.save(OUT)
print("wrote " + OUT + "  (" + str(round(os.path.getsize(OUT) / 1024)) + " KB)")
print("  paragraphs " + str(len(doc.paragraphs)) + ", tables "
      + str(len(doc.tables)) + ", images " + str(len(doc.inline_shapes)))
