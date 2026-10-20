"""
dashboard_sources/*.csv -> report_figures/*.png

Figures for the Word report. They read the same tables the dashboard reads, so
a number in the document and the same number on the dashboard cannot drift.

Usage:  python build_report_figures.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

SRC = "dashboard_sources"
OUT = "report_figures"
os.makedirs(OUT, exist_ok=True)

BLUE, OCHRE, SAGE, PLUM = "#2F6D9E", "#C87F3D", "#5B8C6A", "#9B5B7D"
MUTED, BRICK = "#9AA3AB", "#B5483D"
INK, FADE, GRID = "#1C2430", "#626E7B", "#E3E8ED"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 150,
    "font.size": 8.5, "font.family": "sans-serif",
    "axes.edgecolor": "#BFC8D1", "axes.labelcolor": INK, "axes.titlesize": 9.5,
    "axes.titleweight": "medium", "axes.titlelocation": "left",
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": FADE, "ytick.color": FADE, "text.color": INK,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "legend.frameon": False, "legend.fontsize": 8,
})

L = lambda n: pd.read_csv(os.path.join(SRC, f"{n}.csv"))
money = FuncFormatter(lambda v, p: (f"${v/1e9:.1f}B" if abs(v) >= 1e9
                                    else f"${v/1e6:.0f}M" if abs(v) >= 1e6
                                    else f"${v/1e3:.0f}k" if abs(v) >= 1e3
                                    else f"${v:.0f}"))
made = []


def save(fig, name, h=None):
    path = os.path.join(OUT, f"{name}.png")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    made.append((name, os.path.getsize(path)))


# ------------------------------------------------------------ 1. weekly trend
w = L("weekly")
w["date"] = pd.to_datetime(w["date"])
fig, ax = plt.subplots(figsize=(7.2, 2.6))
ax.fill_between(w["date"], w["sales"], color=BLUE, alpha=0.13)
ax.plot(w["date"], w["sales"], color=BLUE, lw=1.4, label="Weekly revenue")
ax.plot(w["date"], w["trend"], color=PLUM, lw=1.3, ls="--", label="52-week trend")
h = w[w["holiday"] == "yes"]
ax.scatter(h["date"], h["sales"], s=16, color=BRICK, zorder=5,
           label="Flagged holiday week")
ax.yaxis.set_major_formatter(money)
ax.set_title("Chain revenue, every week")
ax.legend(loc="upper left", ncol=3)
save(fig, "trend")

# ------------------------------------------------------- 2. seasonal index
s = L("seasonality")
wk = s[s["kind"] == "week"].sort_values("sort")
fig, ax = plt.subplots(figsize=(7.2, 2.3))
cols = [BLUE if v >= 1.15 else BRICK if v <= 0.9 else MUTED for v in wk["index"]]
ax.bar(wk["sort"], wk["index"], color=cols, width=0.78)
ax.axhline(1, color=FADE, lw=0.9, ls="--")
ax.set_title("Seasonal index by calendar week (1.00 = an average week)")
ax.set_xlabel("calendar week")
for _, r in wk.nlargest(2, "index").iterrows():
    ax.annotate(f"wk {int(r['sort'])}\n{r['index']:.2f}",
                (r["sort"], r["index"]), textcoords="offset points",
                xytext=(0, 4), ha="center", fontsize=7.5, color=INK)
save(fig, "seasonal")

# --------------------------------------------------------- 3. store formats
seg = L("segments")
fm = seg[seg["kind"] == "format"]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.4))
axes[0].bar(fm["group"], fm["revenue"], color=[BLUE, OCHRE, SAGE], width=0.55)
axes[0].yaxis.set_major_formatter(money)
axes[0].set_title("Total revenue by format")
axes[1].bar(fm["group"], fm["rev_per_sqft"], color=[BLUE, OCHRE, SAGE], width=0.55)
axes[1].yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"${v:,.0f}"))
axes[1].set_title("Revenue per square foot")
for ax_, col in zip(axes, ["revenue", "rev_per_sqft"]):
    for i, v in enumerate(fm[col]):
        ax_.annotate(f"${v/1e9:.2f}B" if col == "revenue" else f"${v:,.0f}",
                     (i, v), textcoords="offset points", xytext=(0, 3),
                     ha="center", fontsize=8)
save(fig, "formats")

# ------------------------------------------------------- 4. department pareto
d = L("depts").sort_values("revenue", ascending=False).head(25)
fig, ax = plt.subplots(figsize=(7.2, 2.6))
ax.bar(range(len(d)), d["revenue"], color=BLUE, width=0.72)
ax.set_xticks(range(0, len(d), 2))
ax.set_xticklabels([f"D{int(x)}" for x in d["dept"]][::2], fontsize=7.5)
ax.yaxis.set_major_formatter(money)
ax.set_title("Top 25 departments by revenue, with cumulative share")
ax2 = ax.twinx()
ax2.plot(range(len(d)), d["cum_pct"], color=PLUM, lw=1.6, marker="o", ms=2.6)
ax2.set_ylim(0, 100)
ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.0f}%"))
ax2.grid(False)
save(fig, "pareto")

# -------------------------------------------------- 5. store x dept heatmap
sd = L("store_dept")
piv = sd.pivot_table(index="store", columns="dept", values="pct_of_store")
order = sd.sort_values("dept_rank")["dept"].drop_duplicates().tolist()
piv = piv[order]
fig, ax = plt.subplots(figsize=(7.2, 4.4))
im = ax.imshow(piv.values, aspect="auto", cmap="Blues", vmin=0,
               vmax=np.nanpercentile(piv.values, 98))
ax.set_xticks(range(len(order)))
ax.set_xticklabels([int(c) for c in order], fontsize=6.5, rotation=90)
ax.set_yticks(range(0, len(piv), 2))
ax.set_yticklabels([int(i) for i in piv.index][::2], fontsize=6.5)
ax.set_xlabel("department, largest first")
ax.set_ylabel("store")
ax.grid(False)
ax.set_title("Each store's revenue mix across the 20 largest departments")
fig.colorbar(im, ax=ax, shrink=0.6, label="% of that store")
save(fig, "heatmap")

# ---------------------------------------------------------- 6. missingness
p = L("eda_profile")
miss = p[p["missing_pct"] > 0].sort_values("missing_pct")
fig, ax = plt.subplots(figsize=(3.5, 2.0))
ax.barh(miss["column"], miss["missing_pct"], color=BRICK, height=0.6)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p_: f"{v:.0f}%"))
ax.set_title("Missing values by column")
for i, v in enumerate(miss["missing_pct"]):
    ax.annotate(f"{v:.0f}%", (v, i), textcoords="offset points", xytext=(3, 0),
                va="center", fontsize=7.5)
save(fig, "missing")

# ------------------------------------------------- 7. missingness over time
m = L("eda_missing")
m["month"] = pd.to_datetime(m["month"])
fig, ax = plt.subplots(figsize=(3.5, 2.0))
for i, c in enumerate([f"MarkDown{k}" for k in range(1, 6)]):
    sub = m[m["column"] == c].sort_values("month")
    ax.plot(sub["month"], sub["missing_pct"],
            color=[BLUE, OCHRE, SAGE, PLUM, MUTED][i], lw=1.2,
            label=c.replace("MarkDown", "MD"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p_: f"{v:.0f}%"))
ax.set_title("Markdown columns, % missing by month")
ax.legend(ncol=3, fontsize=6.5)
save(fig, "missing_time")

# ------------------------------------------------ 8. distribution of sales
hh = L("eda_hist")
hs = hh[hh["column"] == "Weekly_Sales"]
kp = L("kpis").set_index("metric")["value"]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.3))
axes[0].bar(hs["bin_lo"], hs["count"],
            width=(hs["bin_hi"] - hs["bin_lo"]).mean() * 0.95, color=BLUE)
axes[0].axvline(float(kp["e1_fence_hi"]), color=BRICK, ls="--", lw=1,
                label="upper Tukey fence")
axes[0].xaxis.set_major_formatter(money)
axes[0].set_title("Weekly sales per store-department")
axes[0].legend()
cur = L("curves")
qq = cur[cur["series"] == "qq"]
lo = min(qq["x"].min(), qq["y"].min())
hi = max(qq["x"].max(), qq["y"].max())
axes[1].plot([lo, hi], [lo, hi], color=FADE, ls="--", lw=1)
axes[1].scatter(qq["x"], qq["y"], s=7, color=BLUE, alpha=0.7)
axes[1].xaxis.set_major_formatter(money)
axes[1].yaxis.set_major_formatter(money)
axes[1].set_title("Normal Q-Q plot")
axes[1].set_xlabel("normal quantile")
axes[1].set_ylabel("observed")
save(fig, "distribution")

# ------------------------------------------------------- 9. density overlay
fig, ax = plt.subplots(figsize=(3.5, 2.1))
for name, series, col, lw in [("Observed", "empirical_density", BLUE, 1.6),
                              ("Log-normal", "lognormal_density", PLUM, 1.3),
                              ("Normal", "normal_density", MUTED, 1.3)]:
    sub = cur[cur["series"] == series].sort_values("x")
    ax.plot(sub["x"], sub["y"], color=col, lw=lw, label=name)
ax.xaxis.set_major_formatter(money)
ax.set_yticks([])
ax.set_title("Observed density against two fits")
ax.legend()
save(fig, "density")

# ------------------------------------------------------- 10. correlation
c = L("correlation")
sub = c[c["level"] == "store_week"]
order = ["Weekly_Sales", "Size", "Temperature", "Fuel_Price", "CPI",
         "Unemployment", "TotalMarkDown"]
piv = sub.pivot(index="var1", columns="var2", values="r").loc[order, order]
SHORT = {"Weekly_Sales": "Sales", "Temperature": "Temp", "Fuel_Price": "Fuel",
         "Unemployment": "Unemp", "TotalMarkDown": "Markdown"}
lab = [SHORT.get(v, v) for v in order]
fig, ax = plt.subplots(figsize=(3.6, 3.1))
im = ax.imshow(piv.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(lab)), lab, rotation=45, ha="right", fontsize=7)
ax.set_yticks(range(len(lab)), lab, fontsize=7)
ax.grid(False)
for i in range(len(lab)):
    for j in range(len(lab)):
        v = piv.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.4,
                color="white" if abs(v) > 0.55 else INK)
ax.set_title("Correlation, store-week level")
save(fig, "correlation")

# --------------------------------------------------------- 11. clustering
st = L("stores")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
names = list(dict.fromkeys(st["cluster"]))
for i, n in enumerate(names):
    g = st[st["cluster"] == n]
    axes[0].scatter(g["pca_x"], g["pca_y"], s=np.sqrt(g["size"]) / 3.2,
                    color=[BLUE, OCHRE, SAGE, PLUM][i % 4], alpha=0.75, label=n)
axes[0].set_title("Store archetypes, principal components")
axes[0].set_xlabel("PC1")
axes[0].set_ylabel("PC2")
axes[0].legend(fontsize=6.5)
el = cur[cur["series"] == "elbow"].sort_values("x")
axes[1].plot(el["x"], el["y"], color=BLUE, lw=1.5, marker="o", ms=3,
             label="Inertia")
axes[1].set_xlabel("clusters (k)")
axes[1].yaxis.set_major_formatter(FuncFormatter(lambda v, p_: f"{v:,.0f}"))
ax2 = axes[1].twinx()
sil = el.dropna(subset=["y2"])
ax2.plot(sil["x"], sil["y2"], color=PLUM, lw=1.5, marker="s", ms=3,
         label="Silhouette")
ax2.grid(False)
axes[1].axvline(4, color=FADE, ls="--", lw=0.9)
axes[1].set_title("Choosing k: inertia and silhouette")
save(fig, "clusters")

# ------------------------------------------------------- 12. productivity
fig, ax = plt.subplots(figsize=(3.6, 2.4))
TC = {"A": BLUE, "B": OCHRE, "C": SAGE}
for t, g in st.groupby("type"):
    ax.scatter(g["size"], g["rev_per_sqft"], s=g["total_rev"] / 4e6,
               color=TC[t], alpha=0.6, label=f"Type {t}")
ax.axhline(float(kp["b_topq_rps"]), color=FADE, ls="--", lw=1)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p_: f"{v/1000:.0f}k"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p_: f"${v:,.0f}"))
ax.set_xlabel("floor space (sq ft)")
ax.set_ylabel("revenue per sq ft")
ax.set_title("Size against productivity")
ax.legend(fontsize=7)
save(fig, "productivity")

# ---------------------------------------------------------- 13. forecast
fc = L("forecast")
fc["date"] = pd.to_datetime(fc["date"])
fut = fc[fc["kind"] == "forecast"].sort_values("date")
bt = fc[fc["kind"] == "backtest"].sort_values("date")
hist = w.tail(60)
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.4))
axes[0].plot(hist["date"], hist["sales"], color=BLUE, lw=1.4, label="Actual")
axes[0].fill_between(fut["date"], fut["lo"], fut["hi"], color=BLUE, alpha=0.15,
                     label="95% band")
axes[0].plot(fut["date"], fut["value"], color=BLUE, lw=1.4, ls="--",
             label="Forecast")
axes[0].yaxis.set_major_formatter(money)
axes[0].set_title("14-week forecast")
axes[0].legend(fontsize=7)
axes[1].plot(bt["date"], bt["value"], color=BLUE, lw=1.4, marker="o", ms=2.6,
             label="Actual")
axes[1].plot(bt["date"], bt["predicted"], color=PLUM, lw=1.4, ls="--",
             marker="s", ms=2.6, label="Predicted")
axes[1].yaxis.set_major_formatter(money)
axes[1].set_title(f"Backtest, 13 held-out weeks ({float(kp['e8_mape']):.2f}% MAPE)")
axes[1].legend(fontsize=7)
for ax_ in axes:
    ax_.tick_params(axis="x", labelsize=7, rotation=20)
save(fig, "forecast")

# ----------------------------------------------------------- 14. holidays
hol = L("holidays").sort_values("lift_pct", ascending=False)
fig, ax = plt.subplots(figsize=(3.5, 2.1))
cols = [BLUE if v >= 0 else BRICK for v in hol["lift_pct"]]
ax.bar(hol["holiday"], hol["lift_pct"], color=cols, width=0.58)
ax.axhline(0, color=FADE, lw=0.9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p_: f"{v:.0f}%"))
ax.set_title("Holiday lift against a same-month baseline")
ax.tick_params(axis="x", labelsize=7.5, rotation=18)
for i, v in enumerate(hol["lift_pct"]):
    ax.annotate(f"{v:+.0f}%", (i, v), textcoords="offset points",
                xytext=(0, 3 if v >= 0 else -11), ha="center", fontsize=7.5)
save(fig, "holidays")

# ------------------------------------------------- 15. markdown confound
md = L("markdown")
band = md[md["kind"] == "band"]
fig, ax = plt.subplots(figsize=(3.5, 2.1))
ax.bar(band["label"], band["avg_sales"], color=BLUE, width=0.6)
ax.yaxis.set_major_formatter(money)
ax.set_title("Average sales by markdown depth quintile")
ax.tick_params(axis="x", labelsize=7, rotation=20)
save(fig, "markdown")

print(f"{len(made)} figures in {OUT}/")
for n, s_ in made:
    print(f"  {n:<16} {s_/1024:>7.0f} KB")
