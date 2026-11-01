"""
Diagrams for the plain-language guide -> report_figures/guide_*.png

Two drawings do most of the explaining: how the data flows from four raw files
to three finished outputs, and how the dashboard screen is laid out.

Usage:  python build_guide_figures.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = "report_figures"
os.makedirs(OUT, exist_ok=True)

BLUE, OCHRE, SAGE, PLUM = "#2F6D9E", "#C87F3D", "#5B8C6A", "#9B5B7D"
MUTED, BRICK = "#9AA3AB", "#B5483D"
INK, FADE, PALE = "#1C2430", "#626E7B", "#EEF3F8"

plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 150,
                     "font.family": "sans-serif", "text.color": INK})


def box(ax, x, y, w, h, title, sub=None, fill=PALE, edge=BLUE, ts=8.2, ss=7.0):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor=fill, edgecolor=edge, linewidth=1.1))
    ax.text(x + w / 2, y + h / 2 + (0.016 if sub else 0), title, ha="center",
            va="center", fontsize=ts, weight="bold", color=INK)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.018, sub, ha="center", va="center",
                fontsize=ss, color=FADE)


def arrow(ax, x1, y1, x2, y2, color=MUTED):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
        color=color, linewidth=1.1, shrinkA=0, shrinkB=0))


# ============================================================ 1. the pipeline
# Vertical order within each stage is: box, gap, step label, arrow, next box.
# Arrows therefore never cross a label.
fig, ax = plt.subplots(figsize=(7.2, 7.1))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.text(0.5, 0.982, "From four spreadsheets to one dashboard",
        ha="center", fontsize=11.5, weight="bold", color=INK)


def step(y, n, text):
    ax.text(0.5, y, "STEP " + str(n) + "   " + text, ha="center", va="center",
            fontsize=7.8, color=BLUE, weight="bold")


# --- stage 1: the raw files
step(0.942, 1, "·  what we were given")
raw = [("train.csv", "weekly sales\n421,570 rows"),
       ("stores.csv", "45 stores\ntype and size"),
       ("features.csv", "weather, fuel\nCPI, markdowns"),
       ("test.csv", "no sales column\nnot used here")]
for i, (t, sub) in enumerate(raw):
    x = 0.035 + i * 0.242
    grey = t == "test.csv"
    ax.add_patch(FancyBboxPatch(
        (x, 0.845), 0.207, 0.078,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor="white", edgecolor=MUTED if grey else BLUE, linewidth=1.1))
    ax.text(x + 0.1035, 0.903, t, ha="center", fontsize=8.0, weight="bold",
            color=FADE if grey else INK)
    ax.text(x + 0.1035, 0.868, sub, ha="center", va="center", fontsize=6.6,
            color=FADE, linespacing=1.45)
for i in range(3):
    x = 0.1385 + i * 0.242
    ax.plot([x, x], [0.845, 0.822], color=MUTED, linewidth=1.0)
ax.plot([0.1385, 0.6225], [0.822, 0.822], color=MUTED, linewidth=1.0)
arrow(ax, 0.3805, 0.822, 0.3805, 0.800)

# --- stage 2: the join
step(0.782, 2, "·  join them into one table")
box(ax, 0.155, 0.690, 0.69, 0.072, "walmart_integrated_dataset.csv",
    "421,570 rows × 16 columns   ·   joined on Store, then on Store + Date",
    fill=PALE, edge=BLUE, ts=8.4, ss=6.9)
arrow(ax, 0.5, 0.690, 0.5, 0.668)

# --- stage 3: the scripts
step(0.650, 3, "·  Python scripts do the analysis")
scripts = [("build_dashboard_data.py", "runs the 8 experiments"),
           ("build_dashboard_extras.py", "per-store detail tables"),
           ("build_eda.py", "checks the data health"),
           ("build_dashboard_sources.py", "tidies results into CSVs")]
for i, (t, sub) in enumerate(scripts):
    r, c = divmod(i, 2)
    box(ax, 0.075 + c * 0.44, 0.528 - r * 0.079, 0.41, 0.066, t, sub,
        fill="white", edge=OCHRE, ts=7.5, ss=6.6)
arrow(ax, 0.5, 0.449, 0.5, 0.427)

# --- stage 4: the result tables
step(0.409, 4, "·  save every result as a small table")
box(ax, 0.155, 0.317, 0.69, 0.072,
    "dashboard_sources/   —   27 CSV files",
    "every number on the dashboard is read from here, never recalculated live",
    fill=PALE, edge=SAGE, ts=8.4, ss=6.9)
ax.plot([0.5, 0.5], [0.317, 0.296], color=MUTED, linewidth=1.0)
ax.plot([0.1925, 0.8075], [0.296, 0.296], color=MUTED, linewidth=1.0)

# --- stage 5: the outputs
step(0.271, 5, "·  three ways to read the results")
outs = [("Web dashboard", "on GitHub Pages\nanyone can open it", SAGE),
        ("Streamlit app", "the same charts\nas a Python app", OCHRE),
        ("Word report", "the findings\nwritten up", PLUM)]
for i, (t, sub, col) in enumerate(outs):
    x = 0.055 + i * 0.315
    cx = x + 0.1375
    ax.plot([cx, cx], [0.296, 0.252], color=MUTED, linewidth=1.0)
    arrow(ax, cx, 0.252, cx, 0.240)
    ax.add_patch(FancyBboxPatch(
        (x, 0.112), 0.275, 0.126,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        facecolor="white", edgecolor=col, linewidth=1.3))
    ax.text(cx, 0.206, t, ha="center", fontsize=8.6, weight="bold", color=INK)
    ax.text(cx, 0.157, sub, ha="center", va="center", fontsize=7.0,
            color=FADE, linespacing=1.5)

ax.text(0.5, 0.045,
        "The raw files are only needed to rebuild the 27 tables.\n"
        "The dashboard runs on those tables alone, which is why it opens "
        "instantly and needs no database.",
        ha="center", va="center", fontsize=7.5, color=FADE, linespacing=1.7)
fig.savefig(os.path.join(OUT, "guide_pipeline.png"), bbox_inches="tight",
            facecolor="white")
plt.close(fig)

# ========================================================= 2. dashboard layout
fig, ax = plt.subplots(figsize=(7.2, 4.6))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.text(0.5, 0.975, "How the dashboard screen is arranged", ha="center",
        fontsize=11, weight="bold", color=INK)

ax.add_patch(FancyBboxPatch((0.035, 0.085), 0.60, 0.845,
                            boxstyle="round,pad=0.008,rounding_size=0.015",
                            facecolor="white", edgecolor=MUTED, linewidth=1.2))
box(ax, 0.050, 0.858, 0.570, 0.055, "Walmart Sales Intelligence",
    fill=PALE, edge=BLUE, ts=8.0)

tabs = ["Overview", "Trend", "Stores", "Depts", "EDA", "Stats"]
for i, t in enumerate(tabs):
    ax.add_patch(FancyBboxPatch(
        (0.053 + i * 0.095, 0.800), 0.088, 0.040,
        boxstyle="round,pad=0.004,rounding_size=0.01",
        facecolor=BLUE if i == 0 else "white",
        edgecolor=BLUE if i == 0 else MUTED, linewidth=0.9))
    ax.text(0.097 + i * 0.095, 0.820, t, ha="center", va="center",
            fontsize=6.2, color="white" if i == 0 else FADE)

# slicer rail
ax.add_patch(FancyBboxPatch((0.050, 0.355), 0.135, 0.425,
                            boxstyle="round,pad=0.006,rounding_size=0.012",
                            facecolor=PALE, edgecolor=OCHRE, linewidth=1.1))
ax.text(0.1175, 0.755, "Filters", ha="center", fontsize=7.2, weight="bold")
for i, t in enumerate(["Format", "Archetype", "Year", "Week type", "Store"]):
    ax.text(0.062, 0.712 - i * 0.070, t, fontsize=6.3, color=FADE)
    for j in range(3):
        ax.add_patch(FancyBboxPatch(
            (0.062 + j * 0.037, 0.675 - i * 0.070), 0.031, 0.024,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            facecolor=OCHRE if (i + j) % 4 == 0 else "white",
            edgecolor=MUTED, linewidth=0.6))

# KPI strip
for i in range(6):
    x = 0.196 + i * 0.0715
    ax.add_patch(FancyBboxPatch(
        (x, 0.700), 0.065, 0.080,
        boxstyle="round,pad=0.004,rounding_size=0.01",
        facecolor="white", edgecolor=SAGE, linewidth=0.9))
    ax.text(x + 0.0325, 0.755, "label", ha="center", fontsize=5.0, color=FADE)
    ax.text(x + 0.0325, 0.726, "$0.0B", ha="center", fontsize=6.6, color=INK,
            weight="bold")

# panel grid
panels = [(0.196, 0.470, 0.280, 0.210), (0.486, 0.470, 0.134, 0.210),
          (0.196, 0.355, 0.135, 0.100), (0.341, 0.355, 0.135, 0.100),
          (0.486, 0.355, 0.134, 0.100),
          (0.196, 0.170, 0.207, 0.170), (0.413, 0.170, 0.207, 0.170)]
for i, (x, y, w, h) in enumerate(panels):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.004,rounding_size=0.01",
        facecolor="white", edgecolor=MUTED, linewidth=0.9))
    ax.text(x + 0.008, y + h - 0.022, "chart title", fontsize=5.4, color=INK)
    ax.text(x + w - 0.008, y + h - 0.022, "filtered" if i % 2 == 0 else "full",
            fontsize=4.7, color=FADE, ha="right")
    ax.plot([x + 0.012, x + w * 0.35, x + w * 0.6, x + w - 0.012],
            [y + h * 0.30, y + h * 0.58, y + h * 0.36, y + h * 0.70],
            color=BLUE, linewidth=1.0)

# callouts, all to the right of the screen so nothing overlaps it
calls = [
    (0.900, 1, 0.620, 0.885, "Six report pages,\none subject each."),
    (0.740, 1, 0.620, 0.740, "Headline numbers.\nThese move when you\nchange a filter."),
    (0.570, 1, 0.185, 0.590, "Filters. Pick a format,\na year or one store and\n"
                             "the whole screen redraws."),
    (0.410, 1, 0.620, 0.430, "Each panel says whether it\nreacts to filters or always\n"
                             "shows the full dataset."),
    (0.215, 1, 0.620, 0.250, "Hover a chart for exact\nnumbers. Click a bar or a\n"
                             "row to filter everything else."),
]
for ty, _, axp, ayp, text in calls:
    ax.annotate(text, xy=(axp, ayp), xytext=(0.655, ty),
                fontsize=6.5, color=INK, va="center", ha="left",
                linespacing=1.6,
                arrowprops=dict(arrowstyle="-", color=OCHRE, linewidth=0.9,
                                connectionstyle="arc3,rad=0.10"))

fig.savefig(os.path.join(OUT, "guide_layout.png"), bbox_inches="tight",
            facecolor="white")
plt.close(fig)

for n in ("guide_pipeline", "guide_layout"):
    p = os.path.join(OUT, n + ".png")
    print("  " + n.ljust(16) + str(round(os.path.getsize(p) / 1024)) + " KB")
