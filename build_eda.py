"""
Exploratory data analysis -> dashboard_sources/eda_*.csv

Profiles the RAW merged data rather than walmart_integrated_dataset.csv, because
that file fills the MarkDown columns with 0.0 and so reports no missing values at
all. Markdowns are genuinely absent before Nov 2011; this script shows that.

Usage:  python build_eda.py
"""

import csv
import io
import os

import numpy as np
import pandas as pd
from scipy import stats

OUT_DIR = "dashboard_sources"
MD = [f"MarkDown{i}" for i in range(1, 6)]

print("Loading raw files ...")
train = pd.read_csv("train - Walmart Sales Forecast.csv", parse_dates=["Date"])
stores = pd.read_csv("stores - Walmart Sales Forecast.csv")
feats = pd.read_csv("features - Walmart Sales Forecast.csv", parse_dates=["Date"],
                    na_values=["NA"])

df = train.merge(stores, on="Store", how="left")
df = df.merge(feats.drop(columns=["IsHoliday"]), on=["Store", "Date"], how="left")
df["IsHoliday"] = df["IsHoliday"].astype(str).str.upper().isin(["TRUE", "1"])
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
print(f"  merged: {len(df):,} rows x {df.shape[1]} columns")

written = {}


def write(name, cols, rows):
    path = os.path.join(OUT_DIR, f"{name}.csv")
    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if v is None or (isinstance(v, float) and not np.isfinite(v))
                        else v for v in r])
    written[name] = (len(rows), os.path.getsize(path))


def r(x, nd=4):
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return round(f, nd) if np.isfinite(f) else None


# ------------------------------------------------------------ 1. column profile
NUMERIC = ["Weekly_Sales", "Size", "Temperature", "Fuel_Price", "CPI",
           "Unemployment"] + MD
ROLE = {
    "Store": "key", "Dept": "key", "Date": "key", "Weekly_Sales": "target",
    "IsHoliday": "flag", "Type": "attribute", "Size": "attribute",
    "Temperature": "driver", "Fuel_Price": "driver", "CPI": "driver",
    "Unemployment": "driver",
    **{m: "promotion" for m in MD},
}

prof = []
n = len(df)
for c in ["Store", "Dept", "Date", "Weekly_Sales", "IsHoliday", "Type", "Size",
          "Temperature", "Fuel_Price", "CPI", "Unemployment"] + MD:
    s = df[c]
    miss = int(s.isna().sum())
    row = {
        "column": c,
        "role": ROLE.get(c, ""),
        "dtype": ("datetime" if pd.api.types.is_datetime64_any_dtype(s)
                  else "boolean" if pd.api.types.is_bool_dtype(s)
                  else "numeric" if pd.api.types.is_numeric_dtype(s)
                  else "text"),
        "non_null": n - miss,
        "missing": miss,
        "missing_pct": r(miss / n * 100, 3),
        "unique": int(s.nunique(dropna=True)),
        "unique_pct": r(s.nunique(dropna=True) / n * 100, 4),
    }
    if c in NUMERIC:
        v = pd.to_numeric(s, errors="coerce").dropna()
        q1, q2, q3 = v.quantile([0.25, 0.5, 0.75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out = ((v < lo) | (v > hi)).sum()
        row.update({
            "mean": r(v.mean(), 3), "std": r(v.std(), 3),
            "min": r(v.min(), 3), "q1": r(q1, 3), "median": r(q2, 3),
            "q3": r(q3, 3), "max": r(v.max(), 3), "iqr": r(iqr, 3),
            "skew": r(stats.skew(v), 4), "kurtosis": r(stats.kurtosis(v), 4),
            "zeros": int((v == 0).sum()), "negatives": int((v < 0).sum()),
            "outliers_iqr": int(out), "outlier_pct": r(out / len(v) * 100, 3),
            "cv": r(v.std() / v.mean(), 4) if v.mean() else None,
        })
    prof.append(row)

COLS = ["column", "role", "dtype", "non_null", "missing", "missing_pct", "unique",
        "unique_pct", "mean", "std", "min", "q1", "median", "q3", "max", "iqr",
        "skew", "kurtosis", "zeros", "negatives", "outliers_iqr", "outlier_pct",
        "cv"]
write("eda_profile", COLS, [[p.get(c) for c in COLS] for p in prof])

# -------------------------------------------------------------- 2. histograms
# A fixed 40-bin histogram per numeric column, clipped at the 99.5th percentile
# so a long tail does not collapse every bar into the first bin.
hist = []
for c in NUMERIC:
    v = pd.to_numeric(df[c], errors="coerce").dropna()
    if v.empty:
        continue
    hi = v.quantile(0.995)
    lo = v.min()
    if not np.isfinite(hi) or hi <= lo:
        hi = v.max()
    cnt, edges = np.histogram(v.clip(upper=hi), bins=40, range=(lo, hi))
    for k in range(len(cnt)):
        hist.append([c, r(edges[k], 4), r(edges[k + 1], 4), int(cnt[k])])
write("eda_hist", ["column", "bin_lo", "bin_hi", "count"], hist)

# ------------------------------------------------------- 3. box-plot summaries
box = []
for c in NUMERIC:
    v = pd.to_numeric(df[c], errors="coerce").dropna()
    if v.empty:
        continue
    q1, q2, q3 = v.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    inside = v[(v >= q1 - 1.5 * iqr) & (v <= q3 + 1.5 * iqr)]
    box.append([c, r(inside.min(), 3), r(q1, 3), r(q2, 3), r(q3, 3),
                r(inside.max(), 3), r(v.mean(), 3), int(len(v))])
write("eda_box", ["column", "whisker_lo", "q1", "median", "q3", "whisker_hi",
                  "mean", "n"], box)

# ----------------------------------------------------- 4. categorical frequency
cat = []
for c, label in [("Type", "Store format"), ("IsHoliday", "Holiday week"),
                 ("Year", "Year"), ("Month", "Month")]:
    vc = df[c].value_counts(dropna=False).sort_index()
    rev = df.groupby(c, dropna=False)["Weekly_Sales"].sum()
    for k, v in vc.items():
        cat.append([c, label, str(k), int(v), r(v / n * 100, 3),
                    r(float(rev.get(k, np.nan)), 0)])
# Store and Dept are high-cardinality: report the shape, not every level.
for c in ["Store", "Dept"]:
    cat.append([c + "_cardinality", c + " levels", "distinct",
                int(df[c].nunique()), r(df[c].nunique() / n * 100, 4), None])
write("eda_cat", ["column", "label", "value", "count", "pct", "revenue"], cat)

# --------------------------------------------- 5. missingness over time
# The markdown columns are the whole missing-data story, so show when.
miss_t = []
by_month = df.groupby(df["Date"].dt.to_period("M"))
for per, grp in by_month:
    label = str(per)
    for c in MD + ["CPI", "Unemployment"]:
        m = int(grp[c].isna().sum())
        miss_t.append([label, c, m, len(grp), r(m / len(grp) * 100, 2)])
write("eda_missing", ["month", "column", "missing", "rows", "missing_pct"], miss_t)

# ------------------------------------------------- 6. bivariate against sales
# Decile bands of each driver, with mean sales inside each band.
bivar = []
for c in ["Size", "Temperature", "Fuel_Price", "CPI", "Unemployment"]:
    sub = df[[c, "Weekly_Sales"]].dropna()
    if sub.empty:
        continue
    try:
        sub = sub.assign(band=pd.qcut(sub[c], 10, duplicates="drop"))
    except ValueError:
        continue
    g = sub.groupby("band", observed=True).agg(
        mean_sales=("Weekly_Sales", "mean"),
        median_sales=("Weekly_Sales", "median"),
        n=("Weekly_Sales", "size"), lo=(c, "min"), hi=(c, "max"))
    base = g["mean_sales"].iloc[0]
    for i, (_, row) in enumerate(g.iterrows()):
        bivar.append([c, i + 1, r(row["lo"], 3), r(row["hi"], 3),
                      r(row["mean_sales"], 0), r(row["median_sales"], 0),
                      int(row["n"]), r((row["mean_sales"] / base - 1) * 100, 2)])
    pear, pp = stats.pearsonr(sub[c], sub["Weekly_Sales"])
    spear, sp = stats.spearmanr(sub[c], sub["Weekly_Sales"])
    bivar.append([c, 0, None, None, None, None, None, None])
    bivar[-1] = [c, 0, r(pear, 4), r(pp, 8), r(spear, 4), r(sp, 8), None, None]
write("eda_bivar", ["driver", "decile", "lo_or_pearson", "hi_or_p",
                    "mean_sales_or_spearman", "median_sales_or_sp",
                    "n", "vs_first_pct"], bivar)

# ------------------------------------------------------------ 7. data quality
dq = []
dq.append(["rows", "Rows in the merged table", n, ""])
dq.append(["columns", "Columns", df.shape[1], ""])
dq.append(["duplicate_keys", "Duplicate Store-Dept-Date keys",
           int(df.duplicated(["Store", "Dept", "Date"]).sum()),
           "a value above zero would break the grain"])
dq.append(["complete_rows", "Rows with no missing value at all",
           int(df.notna().all(axis=1).sum()), ""])
dq.append(["complete_pct", "Share of rows fully complete",
           r(df.notna().all(axis=1).mean() * 100, 2), "percent"])
dq.append(["any_missing_cols", "Columns with at least one missing value",
           int(df.isna().any().sum()), ""])
dq.append(["negative_sales", "Records with negative weekly sales",
           int((df["Weekly_Sales"] < 0).sum()), "net returns exceeded sales"])
dq.append(["zero_sales", "Records with exactly zero sales",
           int((df["Weekly_Sales"] == 0).sum()), ""])
dq.append(["markdown_first", "First date any markdown is recorded",
           str(df.loc[df[MD].notna().any(axis=1), "Date"].min().date()), ""])
dq.append(["markdown_coverage", "Share of rows with any markdown recorded",
           r(df[MD].notna().any(axis=1).mean() * 100, 2), "percent"])
dq.append(["date_min", "First week", str(df["Date"].min().date()), ""])
dq.append(["date_max", "Last week", str(df["Date"].max().date()), ""])
dq.append(["weeks", "Distinct weeks", int(df["Date"].nunique()), ""])
dq.append(["stores", "Distinct stores", int(df["Store"].nunique()), ""])
dq.append(["depts", "Distinct departments", int(df["Dept"].nunique()), ""])
dq.append(["store_dept_pairs", "Distinct store-department pairs",
           int(df.groupby(["Store", "Dept"]).ngroups), ""])
dq.append(["grain_completeness", "Share of the full store x dept x week grid present",
           r(n / (df["Store"].nunique() * df["Dept"].nunique()
                  * df["Date"].nunique()) * 100, 2), "percent"])
write("eda_quality", ["metric", "label", "value", "note"], dq)

print()
for k, (rows_n, size) in sorted(written.items()):
    print(f"  {k:<14} {rows_n:>6,} rows   {size / 1024:>7.1f} KB")

print(f"\n  rows fully complete : {df.notna().all(axis=1).mean() * 100:.1f}%")
print(f"  markdown coverage   : {df[MD].notna().any(axis=1).mean() * 100:.1f}%")
print(f"  duplicate keys      : {df.duplicated(['Store', 'Dept', 'Date']).sum()}")
print(f"  grid completeness   : "
      f"{n / (df['Store'].nunique() * df['Dept'].nunique() * df['Date'].nunique()) * 100:.1f}%")
