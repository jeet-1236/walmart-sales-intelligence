"""
Builds "From Dataset to Dashboard.docx" - a plain-language walkthrough of how
the project was built, for a reader who has not seen the code.

Usage:  python build_guide_docx.py
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
OUT = "From Dataset to Dashboard.docx"
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
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.95)
sec.top_margin = sec.bottom_margin = Inches(0.85)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.font.color.rgb = INK
normal.paragraph_format.space_after = Pt(8)
normal.paragraph_format.line_spacing = 1.18

for lvl, size, col in [(1, 16, BLUE), (2, 12.5, INK), (3, 11, INK)]:
    s = doc.styles["Heading " + str(lvl)]
    s.font.name = "Calibri"
    s.font.size = Pt(size)
    s.font.color.rgb = col
    s.font.bold = True
    s.paragraph_format.space_before = Pt(15 if lvl == 1 else 11)
    s.paragraph_format.space_after = Pt(5)


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


def table(headers, rows, widths, font=9):
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
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, caption, width=6.6):
    path = os.path.join(FIG, name + ".png")
    if not os.path.exists(path):
        return
    doc.add_picture(path, width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[-1].paragraph_format.space_after = Pt(3)
    para(caption, size=9, color=FADE, italic=True, after=12,
         align=WD_ALIGN_PARAGRAPH.CENTER)


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(4)
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(" " + it[1])
        else:
            p.add_run(it)


def steps(items):
    for it in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(4)
        if isinstance(it, tuple):
            p.add_run(it[0]).bold = True
            p.add_run(" " + it[1])
        else:
            p.add_run(it)


# ===================================================================== TITLE
para("From Dataset to Dashboard", size=25, bold=True, after=2)
p = para("A plain-language walkthrough of what we did, how we did it, and what "
         "ended up on the screen", size=12, color=FADE, after=10)
rule(p)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
p.add_run("See the dashboard  ").bold = True
link(p, LIVE, LIVE)
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(14)
p.add_run("See the code  ").bold = True
link(p, REPO, REPO)

# =================================================================== OVERVIEW
doc.add_heading("1.  What this project is", level=1)
para("We were given four spreadsheets of Walmart sales data. We joined them "
     "into one table, checked the data for problems, ran eight pieces of "
     "analysis on it, and turned the results into a dashboard that anyone can "
     "open in a web browser.")
para("This document explains that journey in plain words. It is about the "
     "process. If you want the findings themselves, read the companion "
     "document, " + chr(8220) + "Walmart Sales Intelligence" + chr(8221) + ".")
para("The short version: the data covers "
     + format(int(K("stores")), ",") + " stores and "
     + format(int(K("depts")), ",") + " departments over "
     + format(int(K("weeks")), ",") + " weeks, which is "
     + format(int(K("records")), ",") + " rows in total. Every number on the "
     "dashboard traces back to one of those rows.")
figure("guide_pipeline",
       "Figure 1. The whole project on one page. Each step is explained below.")

# =================================================================== THE DATA
doc.add_page_break()
doc.add_heading("2.  What we started with", level=1)
para("Four files. Here is what each one holds and whether we used it.")
table(["File", "What is inside", "Did we use it?"], [
    ["train.csv", "Weekly sales for each store and each department. This is "
     "the thing we are trying to understand.", "Yes, this is the main file"],
    ["stores.csv", "One row per store: which of the three types it is "
     "(A, B or C) and how big it is in square feet.", "Yes"],
    ["features.csv", "One row per store per week: temperature, fuel price, "
     "the local cost-of-living index, unemployment, and five markdown "
     "(discount) columns.", "Yes"],
    ["test.csv", "The same shape as train.csv but with the sales column "
     "removed. It exists for a prediction competition.",
     "No. With no sales figures there is nothing to analyse."],
], [1.0, 3.3, 1.8])

doc.add_heading("A note on the word " + chr(8220) + "department" + chr(8221),
                level=2)
para("A department is a section of the shop, like groceries or electronics. "
     "They are only given as numbers, not names, so throughout this project a "
     "department is referred to as " + chr(8220) + "Department 92" + chr(8221)
     + " and so on. We have no way to know what it sells.")

doc.add_heading("3.  Joining the files into one table", level=1)
para("Analysis is much easier when everything sits in one table, so that was "
     "the first job. We did it in two steps.")
steps([
    ("Add the store information.", "Each sales row says which store it came "
     "from, and the store file has one row per store. We matched them on the "
     "store number. Now every sales row also knows its store type and size."),
    ("Add the weekly conditions.", "The features file has one row per store "
     "per week. We matched on the store number and the date together, because "
     "we need the right week as well as the right store. Now every sales row "
     "also knows that week's temperature, fuel price and so on."),
])
para("The result is walmart_integrated_dataset.csv: "
     + format(int(K("records")), ",") + " rows and 16 columns. One row is "
     + chr(8220) + "one department, in one store, in one week" + chr(8221)
     + ". That sentence is worth remembering, because it explains a lot of "
     "what follows.")
para("We checked that the join did not accidentally duplicate anything. The "
     "combination of store, department and date appears exactly once across "
     "all " + format(int(K("records")), ",") + " rows, so the table is clean.",
     size=10, color=FADE, italic=True)

# ================================================================== CLEANING
doc.add_heading("4.  Cleaning it up", level=1)
para("Four small fixes, each for a reason.")
bullets([
    ("Dates.", "They arrived as plain text like " + chr(8220) + "2010-02-05"
     + chr(8221) + ". We converted them into real dates so the computer can "
     "sort them, work out which week of the year they fall in, and put them "
     "on a timeline."),
    ("The holiday marker.", "It arrived as the words TRUE and FALSE. We turned "
     "it into a proper yes/no value."),
    ("The discount columns.", "They arrived as text with gaps. We turned them "
     "into numbers. The gaps matter a great deal and we come back to them in "
     "the next section."),
    ("Rows with no sales figure.", "Dropped, because there is nothing to "
     "analyse in them."),
])

# ======================================================================= EDA
doc.add_heading("5.  Checking the data before trusting it", level=1)
para("Before running any analysis we looked at the data itself. In statistics "
     "this is called exploratory data analysis, or EDA. The point is to find "
     "problems early, so that you do not build a conclusion on top of a fault.")
para("We wrote a script that goes through every column and reports: how many "
     "values are missing, how many different values there are, the average, "
     "the middle value, the smallest and largest, and how lopsided the spread "
     "is. Here is what it found.")

doc.add_heading("Finding 1: most rows are incomplete, and it is all discounts",
                level=2)
para("Only " + "{:.0f}".format(float(Q("complete_pct"))) + "% of rows have a value in every "
     "column. That sounds alarming until you see which columns are to blame: "
     "all five discount columns and nothing else. They are empty for the first "
     "two years and only start being recorded in November 2011.")
para("This matters for one specific reason. Inside the period where discounts "
     "are recorded, every single row has one. So the data never shows us a "
     "week with no discount to compare against. Any claim of the form "
     + chr(8220) + "sales with a discount versus sales without one" + chr(8221)
     + " cannot be made from this data, because the " + chr(8220) + "without"
     + chr(8221) + " group does not exist.")
para("We only discovered this because we profiled the original files. The "
     "joined file fills those gaps with zeros, and a zero looks like "
     + chr(8220) + "we discounted nothing" + chr(8221) + " when the truth is "
     + chr(8220) + "nobody wrote it down" + chr(8221) + ". Those are very "
     "different things.", size=10, color=FADE, italic=True)

doc.add_heading("Finding 2: a few impossible values", level=2)
para("Two of the discount columns contain negative numbers, 1,311 rows in one "
     "and 257 in the other. A discount cannot be negative, so these are errors "
     "in the source data rather than something to explain. We left them in "
     "place and noted them rather than quietly deleting them.")

doc.add_heading("Finding 3: sales are very lopsided", level=2)
para("Most weeks are small and a few are enormous. The average weekly sale per "
     "department is about $" + format(int(K("e5_mean")), ",") + ", but the "
     "middle value is only $" + format(int(K("e1_q2")), ",") + ". When the "
     "average is twice the middle value, a small number of very large weeks "
     "are pulling it up.")
para("By the standard statistical rule for spotting unusual values, "
     + "{:.1f}".format(K("e1_outlier_pct")) + "% of rows count as outliers. "
     "Normally you might remove outliers. Here you must not: those rows carry "
     + "{:.0f}".format(K("e1_outlier_revenue_pct")) + "% of all the money. "
     "They are not mistakes, they are the Christmas rush.")

doc.add_heading("Finding 4: the grid has gaps", level=2)
para("If every store sold every department every week there would be far more "
     "rows than we have. About " + "{:.0f}".format(float(Q("grain_completeness"))) + "% of that "
     "full grid is present. That is normal - not every shop carries every "
     "department - but it is worth knowing before comparing stores.")

# =============================================================== EXPERIMENTS
doc.add_page_break()
doc.add_heading("6.  The eight pieces of analysis", level=1)
para("The project brief asked for eight specific experiments. Here is each one "
     "in plain words: what we asked, how we answered it, and what came back.")

exp = L("experiments").sort_values("n")
PLAIN = {
    1: ("Describe the data. We worked out the middle value, the spread, and "
        "which weeks count as unusually big or small."),
    2: ("Find what predicts sales. We fitted a straight-line relationship "
        "between sales and things like temperature, fuel price and store size, "
        "to see which of them actually matter."),
    3: ("Check whether a sample is enough. Instead of using all "
        + format(int(K("records")), ",") + " rows, can you take a few thousand "
        "at random and still get the right answer? We tested several sample "
        "sizes against the true figure."),
    4: ("Group the stores. We let the computer sort the 45 stores into groups "
        "based on how they behave, rather than telling it the groups in "
        "advance. This is called clustering."),
    5: ("Treat sales as a random quantity. We worked out the chance of a "
        "department clearing a given sales figure in a week."),
    6: ("Find which standard distribution fits. Statisticians have a library "
        "of standard shapes for data. We tested four of them against the real "
        "shape of our sales."),
    7: ("Test whether differences are real. When holiday weeks look better "
        "than normal weeks, is that a genuine difference or just luck? There "
        "are formal tests for this and we ran several."),
    8: ("Look at the sales over time. We split the timeline into its long-term "
        "direction, its yearly rhythm, and the leftover noise, then used that "
        "to forecast the next 14 weeks."),
}
rows = []
for r in exp.itertuples():
    rows.append([int(r.n), r.title, PLAIN.get(int(r.n), ""), r.headline])
table(["#", "Name", "What we actually asked", "What came back"],
      rows, [0.3, 1.4, 2.6, 2.3], font=8.3)

doc.add_heading("A word on two of them", level=2)
para("Experiment 4, grouping the stores, has a judgement call in it. The "
     "computer will happily make any number of groups you ask for, so you have "
     "to choose. We chose four, partly from a standard chart that shows where "
     "adding more groups stops helping, and partly because four groups are "
     "easy to describe. A second measure of group quality actually prefers "
     "other numbers, so these groups are a useful description rather than a "
     "hard rule.")
para("Experiment 8, the forecast, is easy to fool yourself with. If you test a "
     "forecast on weeks the model already learned from, it will look "
     "brilliant. So we hid the last 13 weeks completely, rebuilt the model on "
     "the earlier weeks only, and then asked it to predict the hidden ones. It "
     "was off by " + "{:.2f}".format(K("e8_mape")) + "% on average. For "
     "comparison, simply guessing " + chr(8220) + "the same week last year"
     + chr(8221) + " is off by " + "{:.2f}".format(K("e8_naive_mape")) + "%, so "
     "our model wins, but not by a wide margin.")

# ============================================================ TO THE SCREEN
doc.add_heading("7.  Getting the results onto a screen", level=1)
para("Here is the part that often gets skipped, and it is the reason the "
     "dashboard is fast.")
para("We could have built a dashboard that loads the whole "
     + format(int(K("records")), ",") + "-row file and does the maths in the "
     "browser every time someone opens it. That would be slow and would need a "
     "server. Instead, the Python scripts do all the heavy work once and write "
     "their answers into 27 small CSV tables. The dashboard then just reads "
     "those tables and draws them.")
para("So the split is: Python does the thinking, the browser does the drawing. "
     "The 27 tables come to about 300 kilobytes in total, which is smaller "
     "than a photograph.")
table(["Script", "What it does, in plain words"], [
    ["build_dashboard_data.py",
     "Runs all eight experiments and writes every result into one file."],
    ["build_dashboard_sources.py",
     "Takes that file and splits it into tidy tables, one per chart."],
    ["build_dashboard_extras.py",
     "Adds two bigger tables: week-by-week sales for each store, and each "
     "store broken down by department."],
    ["build_eda.py",
     "Does the data health check described in section 5."],
    ["build_pages.py",
     "Packages the dashboard into a plain web page that can be hosted for "
     "free."],
    ["build_report_figures.py",
     "Draws the charts used in the written reports."],
    ["app.py",
     "A second version of the dashboard, written as a Python app."],
], [2.0, 4.6])

# ================================================================ DASHBOARD
doc.add_page_break()
doc.add_heading("8.  What the dashboard looks like", level=1)
para("The dashboard is laid out the way a business intelligence tool like "
     "Power BI or Tableau is laid out: filters down the left, headline numbers "
     "across the top, and a grid of charts filling the rest. There is almost "
     "no writing on it, because the charts are meant to do the talking.")
figure("guide_layout", "Figure 2. The parts of the screen.")

doc.add_heading("The six pages", level=2)
table(["Page", "What it answers"], [
    ["Overview", "How is the business doing overall? Weekly sales, a calendar "
     "view of every week, the split by store type, the biggest stores and "
     "departments, and a short list of the main findings."],
    ["Trend and forecast", "How do sales move through the year, and what "
     "happens next? The yearly rhythm, the long-term direction, and the "
     "14-week forecast with its accuracy test."],
    ["Stores", "How do the 45 stores compare? A small chart for every store on "
     "the same scale, size against productivity, the store groups, and a "
     "sortable table of every store."],
    ["Departments", "Which departments carry the business? A ranking, a "
     "block chart sized by sales, which departments do well at holidays, and "
     "a grid showing each store's mix."],
    ["EDA profile", "Can the data be trusted? Missing values, the shape of "
     "every column, the data quality checks from section 5."],
    ["Statistics", "The formal results. The regression, the sampling tests, "
     "the distribution fitting, and the significance tests."],
], [1.4, 5.2])

doc.add_heading("How to use it", level=2)
bullets([
    ("Filters on the left.", "Pick a store type, a store group, a year, "
     "holiday or normal weeks, or a single store. The headline numbers and "
     "many of the charts redraw straight away."),
    ("Hover any chart.", "A small box appears with the exact figures for the "
     "point you are pointing at."),
    ("Click to filter.", "Clicking a bar, a dot, a small store chart or a "
     "table row sets that as a filter for the rest of the screen."),
    ("The badge on each panel.", "Every chart says either " + chr(8220)
     + "filtered" + chr(8221) + " or " + chr(8220) + "full dataset" + chr(8221)
     + " in its top corner. This is an honest label, not decoration: charts "
     "fed by the pre-calculated tables cannot narrow down, so rather than let "
     "them silently ignore your filter, they say so."),
])

doc.add_heading("9.  The tools, and why each one", level=1)
table(["Tool", "What it is", "What we used it for"], [
    ["Python", "A programming language", "Everything in the analysis"],
    ["pandas", "A Python library for tables",
     "Opening the CSV files, joining them, grouping and summarising"],
    ["NumPy", "A Python library for arithmetic",
     "The number-crunching underneath almost everything else"],
    ["SciPy", "A Python library for statistics",
     "The significance tests and the distribution fitting"],
    ["scikit-learn", "A Python library for machine learning",
     "The regression and the store grouping"],
    ["Matplotlib", "A Python library for charts",
     "The charts printed in the written reports"],
    ["D3.js", "A JavaScript charting library",
     "The interactive charts on the web dashboard"],
    ["Streamlit and Plotly", "Tools for building data apps in Python",
     "A second version of the dashboard, for running on a computer"],
    ["Git and GitHub", "Version control and code hosting",
     "Keeping the history of the work and sharing it"],
    ["GitHub Pages", "Free website hosting", "Making the dashboard public"],
    ["python-docx", "A Python library for Word files", "Building this document"],
], [1.3, 2.0, 3.3], font=8.6)

doc.add_heading("10.  Running it yourself", level=1)
para("Everything is in the repository. The dashboard itself needs nothing "
     "installed - it is a web page. To rebuild the analysis from the raw "
     "files, you need Python with the libraries listed above, then run the "
     "scripts in this order:")
p = doc.add_paragraph()
p.paragraph_format.left_indent = Inches(0.25)
p.paragraph_format.space_after = Pt(10)
r = p.add_run("python build_dashboard_data.py\n"
              "python build_dashboard_sources.py\n"
              "python build_dashboard_extras.py\n"
              "python build_eda.py\n"
              "python build_pages.py")
r.font.name = "Consolas"
r.font.size = Pt(9.5)
para("The order matters: the second script reads what the first one writes.")

doc.add_heading("11.  Things to keep in mind", level=1)
para("Three honest limits, in plain words.")
bullets([
    ("We cannot judge whether discounts work.", "As explained in section 5, "
     "the data has no discount-free period to compare against. The charts show "
     "that bigger discounts go alongside bigger sales, but that is mostly "
     "because big departments get big discounts and already sell a lot. It is "
     "not evidence that discounting causes sales."),
    ("The holiday marker in the data is unreliable.", "It marks the week after "
     "Christmas, which is actually a quiet week, and it does not mark the week "
     "before Christmas, which is the busiest week of the year. We found this "
     "during the analysis and worked around it."),
    ("Two and a half years is not very long.", "The data holds only two "
     "complete Christmases. That is enough to see the pattern but not enough "
     "to be confident it will repeat. The stores are also anonymous with no "
     "location, so we cannot tell a regional effect from a single-store one."),
])

p = para()
rule(p)
p = doc.add_paragraph()
r = p.add_run("Dashboard: ")
r.bold = True
r.font.size = Pt(9.5)
link(p, LIVE, LIVE)
p = doc.add_paragraph()
r = p.add_run("Code and data: ")
r.bold = True
r.font.size = Pt(9.5)
link(p, REPO, REPO)

cp = doc.core_properties
cp.author = "jeet-1236"
cp.last_modified_by = "jeet-1236"
cp.title = OUT.replace(".docx", "")

doc.save(OUT)
print("wrote " + OUT + "  (" + str(round(os.path.getsize(OUT) / 1024)) + " KB)")
print("  paragraphs " + str(len(doc.paragraphs)) + ", tables "
      + str(len(doc.tables)) + ", images " + str(len(doc.inline_shapes)))
