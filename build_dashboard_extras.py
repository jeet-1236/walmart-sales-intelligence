"""
Extra source files for the dashboard's visual layer.

Adds the per-store weekly series (small multiples), a store x department
revenue matrix (heatmap), and growth plus returns columns on the department
table. Run after build_dashboard_sources.py.

Usage:  python build_dashboard_extras.py
"""

import csv
import io
import os

import numpy as np
import pandas as pd

SRC = "walmart_integrated_dataset.csv"
OUT_DIR = "dashboard_sources"
MARKDOWNS = [f"MarkDown{i}" for i in range(1, 6)]

print("Loading integrated dataset ...")
df = pd.read_csv(SRC, parse_dates=["Date"])
df["IsHoliday"] = df["IsHoliday"].astype(str).str.upper().isin(["TRUE", "1"])
df = df.dropna(subset=["Weekly_Sales"])
total_rev = df["Weekly_Sales"].sum()

written = {}


def write(name, cols, rows):
    path = os.path.join(OUT_DIR, f"{name}.csv")
    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])
    written[name] = (len(rows), os.path.getsize(path))


# ------------------------------------------------- per-store weekly series
# One row per store-week: 45 stores x 143 weeks, for the small multiples.
sw = (df.groupby(["Store", "Date"], as_index=False)["Weekly_Sales"].sum()
      .sort_values(["Store", "Date"]))
store_type = df.groupby("Store")["Type"].first()
write("store_week", ["store", "type", "date", "revenue"],
      [[int(s), store_type[s], d.strftime("%Y-%m-%d"), round(float(v))]
       for s, d, v in zip(sw["Store"], sw["Date"], sw["Weekly_Sales"])])

# ------------------------------------------- store x department revenue
# The 20 largest departments, so the heatmap stays legible.
dept_rank = (df.groupby("Dept")["Weekly_Sales"].sum()
             .sort_values(ascending=False))
top20 = dept_rank.head(20).index.tolist()
mat = (df[df["Dept"].isin(top20)]
       .groupby(["Store", "Dept"], as_index=False)["Weekly_Sales"].sum())
# Share of each store's own revenue, so big and small stores compare.
store_tot = df.groupby("Store")["Weekly_Sales"].sum()
rows = []
for s, dp, v in zip(mat["Store"], mat["Dept"], mat["Weekly_Sales"]):
    rows.append([int(s), int(dp), store_type[s], round(float(v)),
                 round(float(v) / store_tot[s] * 100, 3),
                 top20.index(int(dp)) + 1])
rows.sort(key=lambda r: (r[0], r[5]))
write("store_dept", ["store", "dept", "type", "revenue", "pct_of_store",
                     "dept_rank"], rows)

# -------------------------------- department growth and returns, appended
# depts.csv already exists; add two columns rather than a new source.
dpath = os.path.join(OUT_DIR, "depts.csv")
with io.open(dpath, encoding="utf-8") as f:
    dept_rows = list(csv.DictReader(f))
    dept_cols = list(dept_rows[0].keys())

df["Year"] = df["Date"].dt.year
dy = df.groupby(["Dept", "Year"])["Weekly_Sales"].sum().unstack()
growth = {}
if 2010 in dy.columns and 2011 in dy.columns:
    g = ((dy[2011] / dy[2010] - 1) * 100).replace([np.inf, -np.inf], np.nan)
    growth = {int(k): (None if pd.isna(v) else round(float(v), 2))
              for k, v in g.items()}

neg = df[df["Weekly_Sales"] < 0]
ret = neg.groupby("Dept")["Weekly_Sales"].sum()
returns = {int(k): round(float(v)) for k, v in ret.items()}

for r in dept_rows:
    d = int(r["dept"])
    r["growth_pct"] = growth.get(d, "")
    r["returns_value"] = returns.get(d, 0)
write("depts", dept_cols + ["growth_pct", "returns_value"],
      [[r[c] for c in dept_cols + ["growth_pct", "returns_value"]]
       for r in dept_rows])

print()
for n, (rows_n, size) in sorted(written.items()):
    print(f"  {n:<13} {rows_n:>6,} rows   {size / 1024:>7.1f} KB")
print(f"\n  stores x depts covers {len(top20)} departments "
      f"({dept_rank.head(20).sum() / total_rev * 100:.0f}% of revenue)")
print(f"  departments with growth: {sum(1 for v in growth.values() if v is not None)}")
print(f"  departments with returns: {len(returns)}")
