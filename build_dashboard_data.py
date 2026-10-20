"""
Walmart Sales Analysis -> dashboard_data.json

Runs the 8 DAL experiments plus a business-impact layer on the integrated
Walmart dataset (421,570 store-dept-week records, Feb 2010 - Oct 2012) and
emits a single compact JSON the dashboard reads.

Usage:  python build_dashboard_data.py
"""

import json
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
rng = np.random.default_rng(42)

SRC = "walmart_integrated_dataset.csv"
OUT = "dashboard_data.json"

MARKDOWNS = ["MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5"]

# The four holiday weeks Walmart flags in this dataset, by their week-ending date.
HOLIDAY_WEEKS = {
    "Super Bowl": ["2010-02-12", "2011-02-11", "2012-02-10"],
    "Labor Day": ["2010-09-10", "2011-09-09", "2012-09-07"],
    "Thanksgiving": ["2010-11-26", "2011-11-25"],
    "Christmas": ["2010-12-31", "2011-12-30"],
}


def r(x, nd=2):
    """Round for JSON, turning NaN/inf into None."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(f):
        return None
    return round(f, nd)


def rl(seq, nd=2):
    return [r(v, nd) for v in seq]


print("Loading integrated dataset ...")
df = pd.read_csv(SRC, parse_dates=["Date"])
df["IsHoliday"] = df["IsHoliday"].astype(str).str.upper().isin(["TRUE", "1"])
for c in MARKDOWNS:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
df["CPI"] = pd.to_numeric(df["CPI"], errors="coerce")
df["Unemployment"] = pd.to_numeric(df["Unemployment"], errors="coerce")
df = df.dropna(subset=["Weekly_Sales"])
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
df["TotalMarkDown"] = df[MARKDOWNS].sum(axis=1)
df["HasMarkDown"] = df["TotalMarkDown"] > 0

sales = df["Weekly_Sales"]
N = len(df)
print(f"  {N:,} records | {df['Store'].nunique()} stores | {df['Dept'].nunique()} depts")

D = {}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------------------------------------------------------- meta / KPIs
total_rev = sales.sum()
weeks = df["Date"].nunique()
store_meta = df.groupby("Store").agg(Type=("Type", "first"), Size=("Size", "first"))

weekly_total = df.groupby("Date", as_index=False)["Weekly_Sales"].sum()
weekly_total = weekly_total.sort_values("Date").reset_index(drop=True)

hol = df[df["IsHoliday"]]
non = df[~df["IsHoliday"]]
hol_mean, non_mean = hol["Weekly_Sales"].mean(), non["Weekly_Sales"].mean()

D["meta"] = {
    "records": int(N),
    "stores": int(df["Store"].nunique()),
    "depts": int(df["Dept"].nunique()),
    "weeks": int(weeks),
    "date_start": df["Date"].min().strftime("%Y-%m-%d"),
    "date_end": df["Date"].max().strftime("%Y-%m-%d"),
    "total_revenue": r(total_rev, 0),
    "avg_weekly_chain": r(weekly_total["Weekly_Sales"].mean(), 0),
    "total_sqft": int(store_meta["Size"].sum()),
    "rev_per_sqft": r(total_rev / store_meta["Size"].sum(), 2),
    "holiday_lift_pct": r((hol_mean / non_mean - 1) * 100, 2),
    "negative_records": int((sales < 0).sum()),
    "negative_value": r(sales[sales < 0].sum(), 0),
    "markdown_coverage_pct": r(df["HasMarkDown"].mean() * 100, 1),
}

# ======================================================== EXP 1 — DESCRIPTIVE
print("Exp 1: descriptive statistics ...")
q1, q2, q3 = sales.quantile([0.25, 0.5, 0.75])
iqr = q3 - q1
lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
out_mask = (sales < lo) | (sales > hi)
outliers = sales[out_mask]


def describe(s):
    qq1, qq2, qq3 = s.quantile([0.25, 0.5, 0.75])
    return {
        "count": int(s.count()), "mean": r(s.mean()), "std": r(s.std()),
        "min": r(s.min()), "q1": r(qq1), "median": r(qq2), "q3": r(qq3),
        "max": r(s.max()), "iqr": r(qq3 - qq1),
    }


# Box-plot five-number summary per store type, on store-week totals.
store_week = df.groupby(["Store", "Date"], as_index=False).agg(
    Weekly_Sales=("Weekly_Sales", "sum"))
store_week = store_week.merge(store_meta.reset_index(), on="Store")

box_by_type = []
for t in ["A", "B", "C"]:
    s = store_week.loc[store_week["Type"] == t, "Weekly_Sales"]
    bq1, bq2, bq3 = s.quantile([0.25, 0.5, 0.75])
    biqr = bq3 - bq1
    whisk_lo = s[s >= bq1 - 1.5 * biqr].min()
    whisk_hi = s[s <= bq3 + 1.5 * biqr].max()
    box_by_type.append({
        "type": t, "q1": r(bq1, 0), "median": r(bq2, 0), "q3": r(bq3, 0),
        "lo": r(whisk_lo, 0), "hi": r(whisk_hi, 0),
        "n": int(s.count()), "mean": r(s.mean(), 0),
    })

D["exp1"] = {
    "sales": {
        "q1": r(q1), "q2": r(q2), "q3": r(q3), "iqr": r(iqr),
        "fence_lo": r(lo), "fence_hi": r(hi),
        "mean": r(sales.mean()), "std": r(sales.std()),
        "min": r(sales.min()), "max": r(sales.max()),
        "outlier_count": int(out_mask.sum()),
        "outlier_pct": r(out_mask.mean() * 100, 2),
        "outlier_revenue": r(outliers.sum(), 0),
        "outlier_revenue_pct": r(outliers.sum() / total_rev * 100, 2),
        "outliers_high": int((sales > hi).sum()),
        "outliers_low": int((sales < lo).sum()),
    },
    "variables": {c: describe(df[c]) for c in
                  ["Weekly_Sales", "Temperature", "Fuel_Price", "CPI",
                   "Unemployment", "Size", "TotalMarkDown"]},
    "box_by_type": box_by_type,
}

# Histogram of weekly sales, clipped at the 99.5th pct so the bars stay readable.
clip = sales.quantile(0.995)
cnt, edges = np.histogram(sales.clip(upper=clip), bins=60)
D["exp1"]["histogram"] = {
    "counts": [int(c) for c in cnt],
    "edges": rl(edges, 0),
}

# ================================================== EXP 2 — LINEAR REGRESSION
print("Exp 2: linear regression ...")
reg_df = df.dropna(subset=["CPI", "Unemployment", "Temperature", "Fuel_Price"]).copy()
reg_df["IsHolidayNum"] = reg_df["IsHoliday"].astype(int)

models = {}

specs = {
    "economic": ["Temperature", "Fuel_Price", "CPI", "Unemployment"],
    "full": ["Size", "Temperature", "Fuel_Price", "CPI", "Unemployment",
             "IsHolidayNum", "TotalMarkDown"],
}
for name, cols in specs.items():
    X = reg_df[cols].to_numpy(float)
    y = reg_df["Weekly_Sales"].to_numpy(float)
    m = LinearRegression().fit(X, y)
    pred = m.predict(X)
    resid = y - pred
    n, k = X.shape
    r2 = r2_score(y, pred)
    # Standard errors -> t and p for each coefficient.
    mse = (resid ** 2).sum() / (n - k - 1)
    Xd = np.column_stack([np.ones(n), X])
    try:
        cov = mse * np.linalg.pinv(Xd.T @ Xd)
        se = np.sqrt(np.diag(cov))[1:]
        tvals = m.coef_ / se
        pvals = 2 * (1 - stats.t.cdf(np.abs(tvals), n - k - 1))
    except Exception:
        se = np.full(k, np.nan)
        tvals = pvals = np.full(k, np.nan)
    models[name] = {
        "features": cols,
        "intercept": r(m.intercept_),
        "coefficients": [
            {"name": c, "coef": r(co, 4), "se": r(s, 4),
             "t": r(t, 2), "p": r(p, 5)}
            for c, co, s, t, p in zip(cols, m.coef_, se, tvals, pvals)
        ],
        "r2": r(r2, 5),
        "adj_r2": r(1 - (1 - r2) * (n - 1) / (n - k - 1), 5),
        "rmse": r(np.sqrt((resid ** 2).mean()), 2),
        "mae": r(np.abs(resid).mean(), 2),
        "n": int(n),
    }

# Same regression at store-week level, where the economic signal is not
# drowned out by department-level noise.
sw = df.groupby(["Store", "Date"], as_index=False).agg(
    Weekly_Sales=("Weekly_Sales", "sum"),
    Temperature=("Temperature", "mean"), Fuel_Price=("Fuel_Price", "mean"),
    CPI=("CPI", "mean"), Unemployment=("Unemployment", "mean"),
    TotalMarkDown=("TotalMarkDown", "mean"), IsHoliday=("IsHoliday", "max"),
).merge(store_meta.reset_index(), on="Store").dropna()
sw["IsHolidayNum"] = sw["IsHoliday"].astype(int)

cols = ["Size", "Temperature", "Fuel_Price", "CPI", "Unemployment",
        "IsHolidayNum", "TotalMarkDown"]
Xs = sw[cols].to_numpy(float)
ys = sw["Weekly_Sales"].to_numpy(float)
ms = LinearRegression().fit(Xs, ys)
preds = ms.predict(Xs)
r2s = r2_score(ys, preds)
ns, ks = Xs.shape
models["store_week"] = {
    "features": cols,
    "intercept": r(ms.intercept_),
    "coefficients": [{"name": c, "coef": r(co, 2)}
                     for c, co in zip(cols, ms.coef_)],
    "r2": r(r2s, 5),
    "adj_r2": r(1 - (1 - r2s) * (ns - 1) / (ns - ks - 1), 5),
    "rmse": r(np.sqrt(((ys - preds) ** 2).mean()), 0),
    "n": int(ns),
}

# Scatter of actual vs predicted (sampled so the payload stays small).
idx = rng.choice(len(ys), size=min(1200, len(ys)), replace=False)
D["exp2"] = {
    "models": models,
    "scatter": [{"a": r(ys[i], 0), "p": r(preds[i], 0)} for i in idx],
    "resid_hist": None,
}
res = ys - preds
cnt, edges = np.histogram(res, bins=40)
D["exp2"]["resid_hist"] = {"counts": [int(c) for c in cnt], "edges": rl(edges, 0)}

# Simple regressions, one driver at a time, for the single-variable panel.
single = []
for c in ["Size", "Temperature", "Fuel_Price", "CPI", "Unemployment",
          "TotalMarkDown"]:
    X1 = sw[[c]].to_numpy(float)
    m1 = LinearRegression().fit(X1, ys)
    single.append({
        "name": c, "slope": r(m1.coef_[0], 2),
        "r2": r(r2_score(ys, m1.predict(X1)), 4),
        "corr": r(np.corrcoef(sw[c], ys)[0, 1], 4),
    })
D["exp2"]["single"] = single

# ========================================================== EXP 3 — SAMPLING
print("Exp 3: sampling ...")
pop_mean, pop_std, pop_med = sales.mean(), sales.std(), sales.median()
samples = []
for n in [100, 500, 1000, 5000, 10000, 50000, 100000]:
    s = sales.sample(n=n, random_state=42)
    se = s.std() / np.sqrt(n)
    samples.append({
        "n": n, "mean": r(s.mean()), "std": r(s.std()),
        "median": r(s.median()), "se": r(se),
        "ci_lo": r(s.mean() - 1.96 * se), "ci_hi": r(s.mean() + 1.96 * se),
        "err_pct": r(abs(s.mean() - pop_mean) / pop_mean * 100, 3),
        "covers": bool(s.mean() - 1.96 * se <= pop_mean <= s.mean() + 1.96 * se),
    })

# Stratified by store type, proportional allocation, n = 10,000.
strat_rows, n_strat = [], 10000
for t in ["A", "B", "C"]:
    sub = df.loc[df["Type"] == t, "Weekly_Sales"]
    share = len(sub) / N
    take = max(2, int(round(share * n_strat)))
    ss = sub.sample(n=min(take, len(sub)), random_state=42)
    strat_rows.append({
        "type": t, "pop_share_pct": r(share * 100, 2), "n": int(len(ss)),
        "pop_mean": r(sub.mean()), "sample_mean": r(ss.mean()),
        "err_pct": r(abs(ss.mean() - sub.mean()) / abs(sub.mean()) * 100, 3),
    })
strat_all = df.groupby("Type")["Weekly_Sales"].mean()
strat_est = sum(
    row["sample_mean"] * (row["pop_share_pct"] / 100) for row in strat_rows)

# Systematic sampling, every k-th record.
k_sys = N // 10000
sys_s = sales.iloc[::k_sys]

# Sampling distribution of the mean: 1,000 draws of n=500 (CLT demo).
means = [sales.sample(n=500, random_state=i).mean() for i in range(1000)]
means = np.array(means)
cnt, edges = np.histogram(means, bins=40)

D["exp3"] = {
    "population": {"mean": r(pop_mean), "std": r(pop_std),
                   "median": r(pop_med), "n": int(N)},
    "simple_random": samples,
    "stratified": {
        "rows": strat_rows, "n": n_strat,
        "estimate": r(strat_est), "pop_mean": r(pop_mean),
        "err_pct": r(abs(strat_est - pop_mean) / pop_mean * 100, 3),
    },
    "systematic": {
        "k": int(k_sys), "n": int(len(sys_s)), "mean": r(sys_s.mean()),
        "std": r(sys_s.std()),
        "err_pct": r(abs(sys_s.mean() - pop_mean) / pop_mean * 100, 3),
    },
    "clt": {
        "counts": [int(c) for c in cnt], "edges": rl(edges, 0),
        "mean_of_means": r(means.mean()), "std_of_means": r(means.std()),
        "theoretical_se": r(pop_std / np.sqrt(500)),
        "reps": 1000, "sample_size": 500,
    },
}

# ======================================================== EXP 4 — CLUSTERING
print("Exp 4: K-Means clustering ...")
# One row per store, six behavioural features.
sprof = df.groupby("Store").agg(
    avg_weekly=("Weekly_Sales", "mean"),
    total_rev=("Weekly_Sales", "sum"),
    volatility=("Weekly_Sales", "std"),
    cpi=("CPI", "mean"),
    unemployment=("Unemployment", "mean"),
    temperature=("Temperature", "mean"),
    markdown=("TotalMarkDown", "mean"),
    depts=("Dept", "nunique"),
)
sprof = sprof.join(store_meta)
sw_tot = store_week.groupby("Store")["Weekly_Sales"].agg(["mean", "std", "sum"])
sprof["store_weekly_rev"] = sw_tot["mean"]
sprof["store_weekly_std"] = sw_tot["std"]
sprof["cv"] = sprof["store_weekly_std"] / sprof["store_weekly_rev"]
sprof["rev_per_sqft"] = sw_tot["sum"] / sprof["Size"]

hol_by_store = df.groupby(["Store", "IsHoliday"])["Weekly_Sales"].mean().unstack()
sprof["hol_lift"] = (hol_by_store[True] / hol_by_store[False] - 1) * 100

feat_cols = ["store_weekly_rev", "Size", "cv", "cpi", "unemployment", "hol_lift"]
Xc = StandardScaler().fit_transform(sprof[feat_cols].fillna(0).to_numpy(float))

elbow = []
for k in range(1, 11):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Xc)
    row = {"k": k, "inertia": r(km.inertia_, 2)}
    if k > 1:
        row["silhouette"] = r(silhouette_score(Xc, km.labels_), 4)
    elbow.append(row)

K = 4
km = KMeans(n_clusters=K, n_init=25, random_state=42).fit(Xc)
sprof["cluster"] = km.labels_
pca = PCA(n_components=2).fit(Xc)
proj = pca.transform(Xc)

# Rank clusters by revenue so labels read high -> low.
order = (sprof.groupby("cluster")["store_weekly_rev"].mean()
         .sort_values(ascending=False).index.tolist())
names = ["Flagship", "Core performer", "Steady mid-tier", "Small format"]
cmap = {c: names[i] for i, c in enumerate(order)}
sprof["cluster_name"] = sprof["cluster"].map(cmap)

clusters = []
for i, c in enumerate(order):
    sub = sprof[sprof["cluster"] == c]
    clusters.append({
        "id": int(c), "name": names[i], "n": int(len(sub)),
        "avg_weekly_rev": r(sub["store_weekly_rev"].mean(), 0),
        "avg_size": r(sub["Size"].mean(), 0),
        "rev_per_sqft": r(sub["rev_per_sqft"].mean(), 2),
        "cv": r(sub["cv"].mean(), 4),
        "cpi": r(sub["cpi"].mean(), 2),
        "unemployment": r(sub["unemployment"].mean(), 3),
        "hol_lift": r(sub["hol_lift"].mean(), 2),
        "total_rev": r(sub["total_rev"].sum(), 0),
        "rev_share_pct": r(sub["total_rev"].sum() / total_rev * 100, 2),
        "types": sub["Type"].value_counts().to_dict(),
        "stores": [int(s) for s in sub.index.tolist()],
    })

D["exp4"] = {
    "features": feat_cols,
    "elbow": elbow,
    "k": K,
    "silhouette": r(silhouette_score(Xc, km.labels_), 4),
    "inertia": r(km.inertia_, 2),
    "clusters": clusters,
    "pca_var": rl(pca.explained_variance_ratio_ * 100, 2),
    "points": [
        {"store": int(s), "x": r(proj[i, 0], 3), "y": r(proj[i, 1], 3),
         "c": int(sprof["cluster"].iloc[i]), "name": sprof["cluster_name"].iloc[i],
         "type": sprof["Type"].iloc[i],
         "rev": r(sprof["store_weekly_rev"].iloc[i], 0),
         "size": int(sprof["Size"].iloc[i])}
        for i, s in enumerate(sprof.index)
    ],
}

# =========================================== EXP 5 — PROBABILITY DISTRIBUTION
print("Exp 5: probability distribution ...")
pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
thresholds = [0, 5000, 10000, 20000, 50000, 100000, 200000]
D["exp5"] = {
    "mean": r(sales.mean()), "variance": r(sales.var(), 0),
    "std": r(sales.std()), "cv": r(sales.std() / sales.mean(), 4),
    "percentiles": [{"p": p, "value": r(sales.quantile(p / 100), 0)}
                    for p in pcts],
    "exceedance": [
        {"threshold": t, "p_gt": r((sales > t).mean(), 5),
         "count": int((sales > t).sum()),
         "rev_share_pct": r(sales[sales > t].sum() / total_rev * 100, 2)}
        for t in thresholds
    ],
    "pmf_bins": None,
}
# Empirical PDF and CDF on a common grid.
grid = np.linspace(sales.quantile(0.001), sales.quantile(0.99), 80)
dens, dedges = np.histogram(sales, bins=grid, density=True)
cdf_vals = [(sales <= g).mean() for g in grid]
D["exp5"]["pdf"] = {"x": rl(dedges[:-1], 0), "y": [r(v, 10) for v in dens]}
D["exp5"]["cdf"] = {"x": rl(grid, 0), "y": [r(v, 5) for v in cdf_vals]}

# Store-week revenue is the aggregate the business actually plans against.
D["exp5"]["store_week"] = {
    "mean": r(store_week["Weekly_Sales"].mean(), 0),
    "std": r(store_week["Weekly_Sales"].std(), 0),
    "p5": r(store_week["Weekly_Sales"].quantile(0.05), 0),
    "p95": r(store_week["Weekly_Sales"].quantile(0.95), 0),
}

# ============================================ EXP 6 — THEORETICAL DISTRIBUTIONS
print("Exp 6: theoretical distributions ...")
skew, kurt = stats.skew(sales), stats.kurtosis(sales)
samp = sales.sample(n=5000, random_state=42).to_numpy(float)

fits = []
# Normal
mu, sd = stats.norm.fit(samp)
ks_n = stats.kstest(samp, stats.norm(mu, sd).cdf)
fits.append({"name": "Normal", "params": {"mu": r(mu), "sigma": r(sd)},
             "ks_stat": r(ks_n.statistic, 4), "ks_p": r(ks_n.pvalue, 6)})
# Log-normal on the positive tail (sales can be negative on returns weeks)
pos = samp[samp > 0]
sh, loc_, sc = stats.lognorm.fit(pos, floc=0)
ks_l = stats.kstest(pos, stats.lognorm(sh, loc_, sc).cdf)
fits.append({"name": "Log-normal", "params": {"shape": r(sh, 4), "scale": r(sc)},
             "ks_stat": r(ks_l.statistic, 4), "ks_p": r(ks_l.pvalue, 6),
             "note": f"fitted on {len(pos):,} positive-sales records"})
# Exponential
le, se_ = stats.expon.fit(pos)
ks_e = stats.kstest(pos, stats.expon(le, se_).cdf)
fits.append({"name": "Exponential", "params": {"loc": r(le), "scale": r(se_)},
             "ks_stat": r(ks_e.statistic, 4), "ks_p": r(ks_e.pvalue, 6)})
# Gamma
ga, gl, gsc = stats.gamma.fit(pos, floc=0)
ks_g = stats.kstest(pos, stats.gamma(ga, gl, gsc).cdf)
fits.append({"name": "Gamma", "params": {"a": r(ga, 4), "scale": r(gsc)},
             "ks_stat": r(ks_g.statistic, 4), "ks_p": r(ks_g.pvalue, 6)})

# Does the chain-level weekly total look normal? (It should, by CLT.)
wt = weekly_total["Weekly_Sales"].to_numpy(float)
sh_w = stats.shapiro(wt[:143])
log_sales = np.log1p(pos)

# Poisson check: count of above-average store-weeks per week.
thr = store_week["Weekly_Sales"].mean()
counts_per_week = (store_week[store_week["Weekly_Sales"] > thr]
                   .groupby("Date").size())
lam = counts_per_week.mean()

# Empirical vs fitted-normal overlay.
hx = np.linspace(samp.min(), np.percentile(samp, 99), 70)
hcnt, hedges = np.histogram(samp, bins=hx, density=True)

D["exp6"] = {
    "shape": {
        "skewness": r(skew, 4), "kurtosis_excess": r(kurt, 4),
        "jarque_bera_p": r(stats.jarque_bera(samp).pvalue, 8),
        "interpretation": "strong right skew, heavy tails",
    },
    "fits": fits,
    "best_fit": min(fits, key=lambda f: f["ks_stat"] or 9)["name"],
    "overlay": {
        "x": rl(hedges[:-1], 0),
        "empirical": [r(v, 10) for v in hcnt],
        "normal": [r(v, 10) for v in stats.norm.pdf(hedges[:-1], mu, sd)],
        "lognormal": [r(v, 10) for v in
                      stats.lognorm.pdf(np.maximum(hedges[:-1], 1), sh, loc_, sc)],
    },
    "qq": {
        "theoretical": rl(stats.norm.ppf(
            np.linspace(0.005, 0.995, 100), mu, sd), 0),
        "empirical": rl(np.quantile(samp, np.linspace(0.005, 0.995, 100)), 0),
    },
    "log_transform": {
        "skewness": r(stats.skew(log_sales), 4),
        "kurtosis_excess": r(stats.kurtosis(log_sales), 4),
        "note": "log1p transform brings skew close to zero",
    },
    "chain_weekly_normality": {
        "shapiro_stat": r(sh_w.statistic, 4), "shapiro_p": r(sh_w.pvalue, 6),
        "skewness": r(stats.skew(wt), 4), "n": int(len(wt)),
    },
    "poisson": {
        "lambda": r(lam, 3), "variance": r(counts_per_week.var(), 3),
        "dispersion": r(counts_per_week.var() / lam, 3),
        "threshold": r(thr, 0), "n_weeks": int(len(counts_per_week)),
    },
}

# ================================================== EXP 7 — STAT. INFERENCE
print("Exp 7: statistical inference ...")
se_mean = sales.std() / np.sqrt(N)
tt = stats.ttest_ind(hol["Weekly_Sales"], non["Weekly_Sales"], equal_var=False)
pooled = np.sqrt((hol["Weekly_Sales"].var() + non["Weekly_Sales"].var()) / 2)
cohen_d = (hol_mean - non_mean) / pooled
mw = stats.mannwhitneyu(
    hol["Weekly_Sales"].sample(n=20000, random_state=1),
    non["Weekly_Sales"].sample(n=20000, random_state=1),
    alternative="two-sided")

groups = [df.loc[df["Type"] == t, "Weekly_Sales"] for t in ["A", "B", "C"]]
anova = stats.f_oneway(*groups)
kw = stats.kruskal(*[g.sample(n=min(20000, len(g)), random_state=1)
                     for g in groups])

# Pairwise Welch t-tests between store types.
pairs = []
for a, b in [("A", "B"), ("A", "C"), ("B", "C")]:
    ga_ = df.loc[df["Type"] == a, "Weekly_Sales"]
    gb_ = df.loc[df["Type"] == b, "Weekly_Sales"]
    t_ = stats.ttest_ind(ga_, gb_, equal_var=False)
    pairs.append({"pair": f"{a} vs {b}", "t": r(t_.statistic, 3),
                  "p": r(t_.pvalue, 8), "diff": r(ga_.mean() - gb_.mean()),
                  "significant": bool(t_.pvalue < 0.05)})

corr_cols = ["Weekly_Sales", "Size", "Temperature", "Fuel_Price", "CPI",
             "Unemployment", "TotalMarkDown"]
cm = df[corr_cols].corr()
corr_matrix = [[r(cm.iloc[i, j], 3) for j in range(len(corr_cols))]
               for i in range(len(corr_cols))]

# Store-week correlations, where macro effects are visible.
cm2 = sw[["Weekly_Sales", "Size", "Temperature", "Fuel_Price", "CPI",
          "Unemployment", "TotalMarkDown"]].corr()

sig_corr = []
for c in corr_cols[1:]:
    sub = df[["Weekly_Sales", c]].dropna()
    rr, pp = stats.pearsonr(sub["Weekly_Sales"], sub[c])
    rs, ps = stats.spearmanr(sub["Weekly_Sales"], sub[c])
    sig_corr.append({"var": c, "pearson": r(rr, 4), "p": r(pp, 8),
                     "spearman": r(rs, 4), "spearman_p": r(ps, 8),
                     "significant": bool(pp < 0.05)})

# Chi-square: is a markdown week more likely to be a holiday week?
ct = pd.crosstab(df["IsHoliday"], df["HasMarkDown"])
chi2, chip, chidof, _ = stats.chi2_contingency(ct)

D["exp7"] = {
    "mean_estimate": {
        "point": r(sales.mean()), "se": r(se_mean, 3),
        "ci95_lo": r(sales.mean() - 1.96 * se_mean),
        "ci95_hi": r(sales.mean() + 1.96 * se_mean),
        "ci99_lo": r(sales.mean() - 2.576 * se_mean),
        "ci99_hi": r(sales.mean() + 2.576 * se_mean),
        "n": int(N),
    },
    "holiday_test": {
        "holiday_mean": r(hol_mean), "nonholiday_mean": r(non_mean),
        "holiday_n": int(len(hol)), "nonholiday_n": int(len(non)),
        "diff": r(hol_mean - non_mean), "lift_pct": r((hol_mean / non_mean - 1) * 100, 2),
        "t_stat": r(tt.statistic, 4), "p_value": r(tt.pvalue, 10),
        "cohen_d": r(cohen_d, 4), "effect_size": "small",
        "mannwhitney_p": r(mw.pvalue, 10),
        "reject_null": bool(tt.pvalue < 0.05),
        "conclusion": "Holiday weeks sell significantly more per store-dept",
    },
    "anova_store_type": {
        "f_stat": r(anova.statistic, 3), "p_value": r(anova.pvalue, 10),
        "kruskal_p": r(kw.pvalue, 10),
        "group_means": {t: r(df.loc[df["Type"] == t, "Weekly_Sales"].mean())
                        for t in ["A", "B", "C"]},
        "group_n": {t: int((df["Type"] == t).sum()) for t in ["A", "B", "C"]},
        "pairwise": pairs,
        "reject_null": bool(anova.pvalue < 0.05),
    },
    "correlation": {
        "labels": corr_cols, "matrix": corr_matrix,
        "store_week_matrix": [[r(cm2.iloc[i, j], 3) for j in range(len(corr_cols))]
                              for i in range(len(corr_cols))],
        "tests": sig_corr,
    },
    "chi_square": {
        "statistic": r(chi2, 2), "p_value": r(chip, 10), "dof": int(chidof),
        "significant": bool(chip < 0.05),
        "note": "Markdown activity is not independent of holiday weeks",
    },
}

# ======================================================== EXP 8 — TIME SERIES
print("Exp 8: time series ...")
ts = weekly_total.copy()
ts["ma4"] = ts["Weekly_Sales"].rolling(4, center=True).mean()
ts["ma12"] = ts["Weekly_Sales"].rolling(12, center=True).mean()
ts["ma52"] = ts["Weekly_Sales"].rolling(52, center=True).mean()
ts["Week"] = ts["Date"].dt.isocalendar().week.astype(int)
ts["Year"] = ts["Date"].dt.year
ts["Month"] = ts["Date"].dt.month

# Classical multiplicative decomposition, period = 52 weeks.
trend = ts["Weekly_Sales"].rolling(52, center=True).mean()
detr = ts["Weekly_Sales"] / trend
seas_idx = detr.groupby(ts["Week"]).mean()
seas_idx = seas_idx / seas_idx.mean()
ts["trend"] = trend
ts["seasonal"] = ts["Week"].map(seas_idx)
ts["resid"] = ts["Weekly_Sales"] / (ts["trend"] * ts["seasonal"])

series = [
    {"d": d.strftime("%Y-%m-%d"), "v": r(v, 0), "ma4": r(m4, 0),
     "ma12": r(m12, 0), "tr": r(tr, 0), "se": r(s, 4), "re": r(rz, 4),
     "h": bool(hl)}
    for d, v, m4, m12, tr, s, rz, hl in zip(
        ts["Date"], ts["Weekly_Sales"], ts["ma4"], ts["ma12"],
        ts["trend"], ts["seasonal"], ts["resid"],
        df.groupby("Date")["IsHoliday"].max().reindex(ts["Date"]).to_numpy())
]

# Holt-Winters style forecast: project the trend line forward, then multiply
# by the seasonal index for the target calendar week.
#
# The trend is a 52-week CENTRED moving average, so it stops ~26 weeks short of
# the end of the series. Projecting from the last fitted trend point therefore
# has to cover that gap as well as the forecast horizon, or every forecast sits
# a half-year of trend too low.
def fit_trend(trend_series, window=26):
    """Least-squares line through the last `window` valid trend points.

    Returns (slope, intercept, x of the last fitted point, its index label).
    """
    valid = trend_series.dropna()
    if len(valid) < 8:
        return None
    tail_ = valid.tail(window)
    xs = np.arange(len(tail_))
    sl, ic = np.polyfit(xs, tail_.to_numpy(float), 1)
    return float(sl), float(ic), len(xs) - 1, int(tail_.index[-1])


ft = fit_trend(ts["trend"])
if ft:
    slope, inter, x_last, i_last = ft
else:
    slope, inter, x_last, i_last = 0.0, ts["Weekly_Sales"].mean(), 0, len(ts) - 1

last_date = ts["Date"].max()
# Weeks between the last fitted trend point and the end of the actual series.
gap = (len(ts) - 1) - i_last

resid_sd = ts["resid"].std()
forecast = []
for h in range(1, 15):
    fd = last_date + pd.Timedelta(weeks=h)
    wk = int(pd.Timestamp(fd).isocalendar().week)
    tr_h = inter + slope * (x_last + gap + h)
    si = float(seas_idx.get(wk, 1.0))
    pt = tr_h * si
    band = 1.96 * resid_sd * pt
    forecast.append({"d": fd.strftime("%Y-%m-%d"), "v": r(pt, 0),
                     "lo": r(pt - band, 0), "hi": r(pt + band, 0),
                     "week": wk, "seasonal": r(si, 4)})

# Backtest: hold out the last 13 weeks and refit BOTH the trend and the
# seasonal index on the training window only, so the weeks being scored
# contribute nothing to the forecast that scores them.
H_BT = 13
split = len(ts) - H_BT
hist = ts.iloc[:split].copy()
hold = ts.iloc[split:].copy()

h_trend = hist["Weekly_Sales"].rolling(52, center=True).mean()
h_seas = (hist["Weekly_Sales"] / h_trend).groupby(hist["Week"]).mean()
h_seas = h_seas / h_seas.mean()

hft = fit_trend(h_trend)
if hft:
    hs, hi_, hx_last, hi_last = hft
    h_gap = (split - 1) - hi_last
    bt_pred = np.array([
        (hi_ + hs * (hx_last + h_gap + j)) * float(h_seas.get(int(w), 1.0))
        for j, w in enumerate(hold["Week"], start=1)
    ])
    bt_act = hold["Weekly_Sales"].to_numpy(float)
    mape = float(np.mean(np.abs((bt_act - bt_pred) / bt_act)) * 100)
    # Seasonal-naive benchmark: the same calendar week one year earlier.
    naive = []
    for d in hold["Date"]:
        prior = ts.loc[ts["Date"] == d - pd.Timedelta(weeks=52), "Weekly_Sales"]
        naive.append(float(prior.iloc[0]) if len(prior) else np.nan)
    naive = np.array(naive)
    ok = np.isfinite(naive)
    naive_mape = (float(np.mean(np.abs((bt_act[ok] - naive[ok]) / bt_act[ok])) * 100)
                  if ok.any() else None)
    bt = {
        "mape": r(mape, 2), "weeks": int(len(hold)),
        "rmse": r(np.sqrt(np.mean((bt_act - bt_pred) ** 2)), 0),
        "mae": r(np.mean(np.abs(bt_act - bt_pred)), 0),
        "naive_mape": r(naive_mape, 2),
        "train_weeks": int(split),
        "holdout_start": hold["Date"].min().strftime("%Y-%m-%d"),
        "holdout_end": hold["Date"].max().strftime("%Y-%m-%d"),
        "note": ("Trend and seasonal index refitted on the first "
                 f"{split} weeks only; the {len(hold)} scored weeks are "
                 "fully held out."),
        "rows": [{"d": d.strftime("%Y-%m-%d"), "a": r(a, 0), "p": r(pp, 0),
                  "n": r(nv, 0)}
                 for d, a, pp, nv in zip(hold["Date"], bt_act, bt_pred, naive)],
    }
else:
    bt = None

# Seasonality tables.
month_idx = ts.groupby("Month")["Weekly_Sales"].mean()
month_idx = (month_idx / month_idx.mean() * 100)
week_top = seas_idx.sort_values(ascending=False)

yoy = df.groupby("Year")["Weekly_Sales"].agg(["sum", "mean", "count"])
# 2010 starts in February and 2012 ends in October, so compare like weeks.
common = (df.groupby(["Year", "Week"])["Weekly_Sales"].sum()
          .unstack(0).dropna())
yoy_rows = []
years = sorted(df["Year"].unique())
for y in years:
    row = {"year": int(y), "revenue": r(yoy.loc[y, "sum"], 0),
           "avg": r(yoy.loc[y, "mean"]), "records": int(yoy.loc[y, "count"]),
           "weeks": int(df.loc[df["Year"] == y, "Date"].nunique())}
    if y in common.columns:
        row["comparable_revenue"] = r(common[y].sum(), 0)
    yoy_rows.append(row)
for i in range(1, len(yoy_rows)):
    pv = yoy_rows[i - 1].get("comparable_revenue")
    cv = yoy_rows[i].get("comparable_revenue")
    if pv and cv:
        yoy_rows[i]["growth_pct"] = r((cv / pv - 1) * 100, 2)

D["exp8"] = {
    "series": series,
    "forecast": forecast,
    "forecast_total": r(sum(f["v"] for f in forecast), 0),
    "backtest": bt,
    "trend_slope_per_week": r(slope, 0),
    "seasonal_index": [{"week": int(w), "index": r(v, 4)}
                       for w, v in seas_idx.items()],
    "month_index": [{"month": MONTH_NAMES[int(m) - 1], "index": r(v, 1),
                     "avg": r(ts.loc[ts["Month"] == m, "Weekly_Sales"].mean(), 0)}
                    for m, v in month_idx.items()],
    "peak_weeks": [{"week": int(w), "index": r(v, 4)}
                   for w, v in week_top.head(6).items()],
    "trough_weeks": [{"week": int(w), "index": r(v, 4)}
                     for w, v in week_top.tail(6).items()],
    "yoy": yoy_rows,
    "resid_std": r(resid_sd, 4),
    "peak": {"date": ts.loc[ts["Weekly_Sales"].idxmax(), "Date"].strftime("%Y-%m-%d"),
             "value": r(ts["Weekly_Sales"].max(), 0)},
    "trough": {"date": ts.loc[ts["Weekly_Sales"].idxmin(), "Date"].strftime("%Y-%m-%d"),
               "value": r(ts["Weekly_Sales"].min(), 0)},
}

# ==================================================== BUSINESS IMPACT LAYER
print("Business impact layer ...")
B = {}

# -- 1. Store type / format economics -------------------------------------
type_rows = []
for t in ["A", "B", "C"]:
    sub = df[df["Type"] == t]
    st = store_meta[store_meta["Type"] == t]
    sub_sw = store_week[store_week["Type"] == t]
    type_rows.append({
        "type": t, "stores": int(len(st)),
        "revenue": r(sub["Weekly_Sales"].sum(), 0),
        "rev_share_pct": r(sub["Weekly_Sales"].sum() / total_rev * 100, 2),
        "avg_size": r(st["Size"].mean(), 0),
        "total_sqft": int(st["Size"].sum()),
        "rev_per_sqft": r(sub["Weekly_Sales"].sum() / st["Size"].sum(), 2),
        "avg_weekly_per_store": r(sub_sw["Weekly_Sales"].mean(), 0),
        "avg_dept_week": r(sub["Weekly_Sales"].mean(), 0),
        "depts": int(sub["Dept"].nunique()),
        "cv": r(sub_sw["Weekly_Sales"].std() / sub_sw["Weekly_Sales"].mean(), 4),
    })
B["store_types"] = type_rows

# -- 2. Holiday economics, holiday by holiday ------------------------------
hol_rows = []
for name, dates in HOLIDAY_WEEKS.items():
    dts = pd.to_datetime(dates)
    sub = df[df["Date"].isin(dts)]
    if sub.empty:
        continue
    # Baseline: the non-holiday weeks of the same calendar months.
    months = sorted(set(pd.Timestamp(d).month for d in dts))
    base = df[(df["Month"].isin(months)) & (~df["IsHoliday"])]
    wk_actual = sub.groupby("Date")["Weekly_Sales"].sum()
    base_week = base.groupby("Date")["Weekly_Sales"].sum().mean()
    lift_abs = wk_actual.mean() - base_week
    hol_rows.append({
        "holiday": name,
        "weeks_observed": int(sub["Date"].nunique()),
        "avg_chain_week": r(wk_actual.mean(), 0),
        "baseline_week": r(base_week, 0),
        "lift_abs": r(lift_abs, 0),
        "lift_pct": r((wk_actual.mean() / base_week - 1) * 100, 2),
        "total_revenue": r(sub["Weekly_Sales"].sum(), 0),
        "per_dept_mean": r(sub["Weekly_Sales"].mean(), 0),
        "dates": dates,
    })
hol_rows.sort(key=lambda x: x["lift_pct"] or -999, reverse=True)

hol_weeks_n = df.loc[df["IsHoliday"], "Date"].nunique()
non_weeks_n = df.loc[~df["IsHoliday"], "Date"].nunique()
hol_week_rev = df[df["IsHoliday"]].groupby("Date")["Weekly_Sales"].sum().mean()
non_week_rev = df[~df["IsHoliday"]].groupby("Date")["Weekly_Sales"].sum().mean()
B["holidays"] = {
    "by_holiday": hol_rows,
    "flagged_weeks": int(hol_weeks_n),
    "flagged_week_share_pct": r(hol_weeks_n / weeks * 100, 1),
    "avg_holiday_week_rev": r(hol_week_rev, 0),
    "avg_normal_week_rev": r(non_week_rev, 0),
    "chain_week_lift_pct": r((hol_week_rev / non_week_rev - 1) * 100, 2),
    "chain_week_lift_abs": r(hol_week_rev - non_week_rev, 0),
    "incremental_revenue": r((hol_week_rev - non_week_rev) * hol_weeks_n, 0),
    "note": ("Thanksgiving and Christmas weeks carry the lift; the dataset's "
             "IsHoliday flag also marks Super Bowl and Labor Day, which do not."),
}

# The 4-flag average understates December: look at the real pre-Christmas weeks.
dec_weeks = ts[(ts["Month"] == 12)]
B["holidays"]["december_avg_week"] = r(dec_weeks["Weekly_Sales"].mean(), 0)
B["holidays"]["december_vs_year_pct"] = r(
    (dec_weeks["Weekly_Sales"].mean() / ts["Weekly_Sales"].mean() - 1) * 100, 2)

# -- 3. Department concentration (Pareto) ---------------------------------
dept = df.groupby("Dept").agg(
    revenue=("Weekly_Sales", "sum"), avg=("Weekly_Sales", "mean"),
    std=("Weekly_Sales", "std"), records=("Weekly_Sales", "size"),
    stores=("Store", "nunique"),
).sort_values("revenue", ascending=False)
dept["share_pct"] = dept["revenue"] / total_rev * 100
dept["cum_pct"] = dept["share_pct"].cumsum()
dept["cv"] = dept["std"] / dept["avg"]

hol_dept = df.groupby(["Dept", "IsHoliday"])["Weekly_Sales"].mean().unstack()
dept["hol_lift"] = (hol_dept[True] / hol_dept[False] - 1) * 100

n80 = int((dept["cum_pct"] <= 80).sum()) + 1
B["departments"] = {
    "total": int(len(dept)),
    "depts_for_80pct": n80,
    "top10_share_pct": r(dept["share_pct"].head(10).sum(), 2),
    "bottom50_share_pct": r(dept["share_pct"].tail(len(dept) // 2).sum(), 2),
    "rows": [
        {"dept": int(i), "revenue": r(row["revenue"], 0),
         "share_pct": r(row["share_pct"], 3), "cum_pct": r(row["cum_pct"], 2),
         "avg": r(row["avg"], 0), "cv": r(row["cv"], 3),
         "stores": int(row["stores"]), "hol_lift": r(row["hol_lift"], 1),
         "records": int(row["records"])}
        for i, row in dept.iterrows()
    ],
}

# Departmental growth: 2011 vs 2010 on comparable weeks.
dy = df.groupby(["Dept", "Year"])["Weekly_Sales"].sum().unstack()
if 2010 in dy.columns and 2011 in dy.columns:
    g = ((dy[2011] / dy[2010] - 1) * 100).replace([np.inf, -np.inf], np.nan).dropna()
    big = dept[dept["revenue"] > dept["revenue"].quantile(0.5)].index
    g = g[g.index.isin(big)]
    B["departments"]["growth_leaders"] = [
        {"dept": int(i), "growth_pct": r(v, 2), "revenue": r(dept.loc[i, "revenue"], 0)}
        for i, v in g.sort_values(ascending=False).head(8).items()]
    B["departments"]["growth_laggards"] = [
        {"dept": int(i), "growth_pct": r(v, 2), "revenue": r(dept.loc[i, "revenue"], 0)}
        for i, v in g.sort_values().head(8).items()]

# -- 4. Markdown / promotion effectiveness --------------------------------
# MarkDown1-5 are only recorded from 2011-11-11, and from that date EVERY
# store-dept-week has a non-zero markdown. The zeros before that date are
# missing data, not genuine "no promotion" weeks, so there is no clean
# zero-markdown control group. Everything below therefore measures markdown
# DEPTH within the markdown era, not markdown vs no markdown.
md_era = df[df["Date"] >= "2011-11-11"].copy()
md_total = md_era["TotalMarkDown"].sum()

md_era["band"] = pd.qcut(
    md_era["TotalMarkDown"], 5,
    labels=["Q1 lightest", "Q2", "Q3", "Q4", "Q5 deepest"])
band = md_era.groupby("band", observed=True).agg(
    avg_sales=("Weekly_Sales", "mean"), med=("Weekly_Sales", "median"),
    records=("Weekly_Sales", "size"), revenue=("Weekly_Sales", "sum"),
    avg_md=("TotalMarkDown", "mean"))
base_band = band["avg_sales"].iloc[0]

# Within store-dept fixed effects: strip each store-dept's own average from
# both series, so the slope compares a store's own heavy-promo weeks with its
# own lighter ones instead of comparing big stores with small ones.
g = md_era.groupby(["Store", "Dept"])
md_era["s_dev"] = md_era["Weekly_Sales"] - g["Weekly_Sales"].transform("mean")
md_era["m_dev"] = md_era["TotalMarkDown"] - g["TotalMarkDown"].transform("mean")

Xfe = md_era[["m_dev"]].to_numpy(float)
yfe = md_era["s_dev"].to_numpy(float)
fe = LinearRegression().fit(Xfe, yfe)
fe_slope = float(fe.coef_[0])
fe_r2 = r2_score(yfe, fe.predict(Xfe))

# Markdown spend clusters on holiday weeks, so re-fit with the holiday flag
# to separate promotion from calendar.
Xfe2 = np.column_stack([md_era["m_dev"].to_numpy(float),
                        md_era["IsHoliday"].astype(int).to_numpy()])
fe2 = LinearRegression().fit(Xfe2, yfe)

# Cross-check against the same calendar weeks a year earlier, before markdowns
# were recorded. Confounded by year-on-year growth, so it is a sanity check
# rather than a clean counterfactual.
wk_range = sorted(md_era["Week"].unique())
prev = df[(df["Year"] == 2010) & (df["Week"].isin(wk_range))]
curr = df[(df["Year"] == 2011) & (df["Week"].isin(wk_range)) &
          (df["Date"] >= "2011-11-11")]
prev_wks = prev["Date"].nunique() or 1
curr_wks = curr["Date"].nunique() or 1

B["markdowns"] = {
    "period_start": "2011-11-11",
    "records_in_period": int(len(md_era)),
    "coverage_pct": r(md_era["HasMarkDown"].mean() * 100, 2),
    "era_coverage_note": (
        "Every record from 2011-11-11 onward carries a non-zero markdown, so "
        "no zero-markdown control group exists inside the markdown era."),
    "total_markdown_spend": r(md_total, 0),
    "avg_markdown_per_record": r(md_era["TotalMarkDown"].mean(), 0),
    "median_markdown": r(md_era["TotalMarkDown"].median(), 0),
    "bands": [
        {"band": str(i), "avg_sales": r(row["avg_sales"], 0),
         "median": r(row["med"], 0), "records": int(row["records"]),
         "revenue": r(row["revenue"], 0), "avg_markdown": r(row["avg_md"], 0),
         "vs_lightest_pct": r((row["avg_sales"] / base_band - 1) * 100, 2)}
        for i, row in band.iterrows()
    ],
    "fixed_effects": {
        "slope": r(fe_slope, 4),
        "r2": r(fe_r2, 5),
        "slope_with_holiday": r(float(fe2.coef_[0]), 4),
        "holiday_coef": r(float(fe2.coef_[1]), 0),
        "r2_with_holiday": r(r2_score(yfe, fe2.predict(Xfe2)), 5),
        "n": int(len(md_era)),
        "attributable_sales": r(fe_slope * md_total, 0),
        "interpretation": (
            f"Each extra $1 of markdown inside a store-dept's own week-to-week "
            f"variation moves sales by ${fe_slope:.2f}."),
    },
    "yoy_crosscheck": {
        "weeks": [int(min(wk_range)), int(max(wk_range))],
        "avg_week_2010": r(prev["Weekly_Sales"].sum() / prev_wks, 0),
        "avg_week_2011": r(curr["Weekly_Sales"].sum() / curr_wks, 0),
        "change_pct": r((curr["Weekly_Sales"].sum() / curr_wks) /
                        (prev["Weekly_Sales"].sum() / prev_wks) * 100 - 100, 2),
        "caveat": "Confounded by year-on-year growth; not a clean control.",
    },
    "by_channel": [
        {"channel": c,
         "total": r(md_era[c].sum(), 0),
         "share_pct": r(md_era[c].sum() / md_total * 100, 1),
         "avg": r(md_era[c].mean(), 0),
         "pct_records_active": r((md_era[c] > 0).mean() * 100, 1),
         "corr_with_sales": r(md_era[[c, "Weekly_Sales"]].corr().iloc[0, 1], 4),
         "corr_within_store": r(
             np.corrcoef(md_era[c] - g[c].transform("mean"),
                         md_era["s_dev"])[0, 1], 4)}
        for c in MARKDOWNS
    ],
    "caveat": ("MarkDown columns are populated only from Nov 2011 (51 of 143 "
               "weeks). Depth effects are measured within store-dept, so they "
               "are not confounded by store size, but markdown spend also "
               "clusters on holiday weeks."),
}

# -- 5. Economic sensitivity ----------------------------------------------
def band_stats(frame, col, bins, labels):
    f = frame.copy()
    f["_b"] = pd.cut(f[col], bins=bins, labels=labels, include_lowest=True)
    g = f.groupby("_b", observed=True)["Weekly_Sales"].agg(["mean", "size"])
    base = g["mean"].iloc[0]
    return [{"band": str(i), "avg": r(row["mean"], 0), "n": int(row["size"]),
             "vs_first_pct": r((row["mean"] / base - 1) * 100, 2)}
            for i, row in g.iterrows()]


# Elasticity from the store-week model: % change in sales per 1-unit move.
mean_sw_rev = sw["Weekly_Sales"].mean()
elas = []
for c, coef in zip(cols, ms.coef_):
    if c in ("Size", "IsHolidayNum", "TotalMarkDown"):
        continue
    elas.append({
        "driver": c, "coef_per_unit": r(coef, 0),
        "pct_of_weekly_rev": r(coef / mean_sw_rev * 100, 3),
        "sd_of_driver": r(sw[c].std(), 3),
        "impact_per_sd": r(coef * sw[c].std(), 0),
        "impact_per_sd_pct": r(coef * sw[c].std() / mean_sw_rev * 100, 2),
    })

B["economics"] = {
    "elasticities": elas,
    "unemployment": band_stats(
        sw, "Unemployment", [0, 6, 7, 8, 9, 30],
        ["<6%", "6-7%", "7-8%", "8-9%", "9%+"]),
    "fuel": band_stats(
        sw, "Fuel_Price", [0, 2.8, 3.2, 3.6, 4.0, 10],
        ["<$2.80", "$2.80-3.20", "$3.20-3.60", "$3.60-4.00", "$4.00+"]),
    "temperature": band_stats(
        sw, "Temperature", [-20, 32, 50, 65, 80, 120],
        ["Freezing <32F", "Cold 32-50F", "Mild 50-65F", "Warm 65-80F", "Hot 80F+"]),
    "cpi": band_stats(
        sw, "CPI", [0, 140, 180, 200, 220, 400],
        ["<140", "140-180", "180-200", "200-220", "220+"]),
    "ranges": {
        "unemployment": [r(df["Unemployment"].min(), 2), r(df["Unemployment"].max(), 2)],
        "fuel": [r(df["Fuel_Price"].min(), 2), r(df["Fuel_Price"].max(), 2)],
        "cpi": [r(df["CPI"].min(), 1), r(df["CPI"].max(), 1)],
        "temperature": [r(df["Temperature"].min(), 1), r(df["Temperature"].max(), 1)],
    },
}

# -- 6. Store scorecard + opportunity sizing ------------------------------
store_rows = []
med_rps = sprof["rev_per_sqft"].median()
top_q_rps = sprof["rev_per_sqft"].quantile(0.75)

store_yoy = df.groupby(["Store", "Year"])["Weekly_Sales"].sum().unstack()
for s in sprof.index:
    p = sprof.loc[s]
    gap = (top_q_rps - p["rev_per_sqft"]) * p["Size"]
    growth = None
    if 2010 in store_yoy.columns and 2011 in store_yoy.columns:
        a, b = store_yoy.loc[s, 2010], store_yoy.loc[s, 2011]
        if a and np.isfinite(a) and a != 0:
            growth = (b / a - 1) * 100
    store_rows.append({
        "store": int(s), "type": p["Type"], "size": int(p["Size"]),
        "total_rev": r(p["total_rev"], 0),
        "avg_weekly": r(p["store_weekly_rev"], 0),
        "rev_per_sqft": r(p["rev_per_sqft"], 2),
        "cv": r(p["cv"], 4),
        "hol_lift": r(p["hol_lift"], 2),
        "cpi": r(p["cpi"], 1),
        "unemployment": r(p["unemployment"], 2),
        "depts": int(p["depts"]),
        "cluster": p["cluster_name"],
        "rev_share_pct": r(p["total_rev"] / total_rev * 100, 3),
        "growth_pct": r(growth, 2),
        "gap_to_top_quartile": r(max(gap, 0), 0),
    })
store_rows.sort(key=lambda x: x["total_rev"], reverse=True)
for i, row in enumerate(store_rows, 1):
    row["rank"] = i

under = [s for s in store_rows if (s["gap_to_top_quartile"] or 0) > 0]
B["stores"] = {
    "rows": store_rows,
    "median_rev_per_sqft": r(med_rps, 2),
    "top_quartile_rev_per_sqft": r(top_q_rps, 2),
    "best": store_rows[0]["store"],
    "worst": store_rows[-1]["store"],
    "top10_rev_share_pct": r(sum(s["rev_share_pct"] for s in store_rows[:10]), 2),
    "bottom10_rev_share_pct": r(sum(s["rev_share_pct"] for s in store_rows[-10:]), 2),
    "underperformers": len(under),
    "total_opportunity": r(sum(s["gap_to_top_quartile"] for s in under), 0),
    "opportunity_pct_of_rev": r(
        sum(s["gap_to_top_quartile"] for s in under) / total_rev * 100, 2),
    "spread_ratio": r(store_rows[0]["total_rev"] / store_rows[-1]["total_rev"], 1),
}

# -- 7. Volatility / risk --------------------------------------------------
vol = sorted(store_rows, key=lambda x: x["cv"] or 0)
B["risk"] = {
    "most_stable": vol[:5],
    "most_volatile": vol[-5:][::-1],
    "chain_cv": r(ts["Weekly_Sales"].std() / ts["Weekly_Sales"].mean(), 4),
    "worst_week_drop_pct": r(
        (ts["Weekly_Sales"].min() / ts["Weekly_Sales"].median() - 1) * 100, 2),
    "best_week_spike_pct": r(
        (ts["Weekly_Sales"].max() / ts["Weekly_Sales"].median() - 1) * 100, 2),
    "concentration_note": (
        f"Top 10 of 45 stores carry "
        f"{sum(s['rev_share_pct'] for s in store_rows[:10]):.1f}% of revenue"),
}

# -- 8. Returns / negative sales ------------------------------------------
neg = df[df["Weekly_Sales"] < 0]
neg_dept = (neg.groupby("Dept")["Weekly_Sales"].agg(["sum", "size"])
            .sort_values("sum").head(8))
B["returns"] = {
    "records": int(len(neg)),
    "share_of_records_pct": r(len(neg) / N * 100, 3),
    "value": r(neg["Weekly_Sales"].sum(), 0),
    "pct_of_revenue": r(abs(neg["Weekly_Sales"].sum()) / total_rev * 100, 4),
    "worst_dept": int(neg_dept.index[0]) if len(neg_dept) else None,
    "by_dept": [{"dept": int(i), "value": r(row["sum"], 0), "records": int(row["size"])}
                for i, row in neg_dept.iterrows()],
    "stores_affected": int(neg["Store"].nunique()),
}

# -- 9. Monthly + weekly revenue shape -----------------------------------
mon = df.groupby(["Year", "Month"])["Weekly_Sales"].sum().reset_index()
B["monthly"] = [
    {"label": f"{MONTH_NAMES[int(m) - 1]} {int(y)}", "year": int(y),
     "month": int(m), "revenue": r(v, 0)}
    for y, m, v in zip(mon["Year"], mon["Month"], mon["Weekly_Sales"])
]
mon_avg = df.groupby("Month")["Weekly_Sales"].sum() / df.groupby("Month")["Date"].nunique()
B["month_profile"] = [
    {"month": MONTH_NAMES[int(m) - 1], "avg_week_rev": r(v, 0),
     "index": r(v / mon_avg.mean() * 100, 1)}
    for m, v in mon_avg.items()
]

# -- 10. Holiday flag audit ----------------------------------------------
# The IsHoliday flag is worth auditing before anyone models on it. In this
# dataset the Christmas flag lands on the week ENDING 31 Dec / 30 Dec, i.e.
# the dead week after Christmas Day, while the real annual peak - the
# pre-Christmas week 51 - carries no flag at all.
hol_by_date = df.groupby("Date")["IsHoliday"].max()
top_weeks = ts.nlargest(8, "Weekly_Sales")
B["flag_audit"] = {
    "top_weeks": [
        {"date": d.strftime("%Y-%m-%d"), "week": int(d.isocalendar().week),
         "revenue": r(v, 0), "flagged": bool(hol_by_date.get(d, False)),
         "vs_median_pct": r((v / ts["Weekly_Sales"].median() - 1) * 100, 1)}
        for d, v in zip(top_weeks["Date"], top_weeks["Weekly_Sales"])
    ],
    "unflagged_in_top5": int(sum(
        1 for d in top_weeks["Date"][:5] if not hol_by_date.get(d, False))),
    "peak_week_flagged": bool(
        hol_by_date.get(ts.loc[ts["Weekly_Sales"].idxmax(), "Date"], False)),
    "christmas_flag_dates": HOLIDAY_WEEKS["Christmas"],
    "verdict": ("The single largest week of each year (week 51, pre-Christmas) "
                "is labelled a normal week, while the post-Christmas trough "
                "(week 52) is labelled a holiday. Any model using IsHoliday "
                "as-is learns the wrong calendar."),
}

# -- 11. Headline findings ------------------------------------------------
best_hol = hol_rows[0] if hol_rows else None
a_type = next(t for t in type_rows if t["type"] == "A")
b_type = next(t for t in type_rows if t["type"] == "B")
c_type = next(t for t in type_rows if t["type"] == "C")
top_dept = B["departments"]["rows"][0]

peak_wk = int(seas_idx.idxmax())
peak_si = float(seas_idx.max())
second_wk = int(seas_idx.drop(peak_wk).idxmax())
second_si = float(seas_idx.drop(peak_wk).max())
peak_row = B["flag_audit"]["top_weeks"][0]
md_bands = B["markdowns"]["bands"]
xmas = next((h for h in hol_rows if h["holiday"] == "Christmas"), None)

B["findings"] = [
    {"title": f"One unflagged week, week {peak_wk}, decides the year",
     "metric": f"Week {peak_wk} runs {(peak_si - 1) * 100:+.0f}% above trend",
     "detail": (f"The pre-Christmas week is the largest week of every year: "
                f"${peak_row['revenue'] / 1e6:.1f}M chain-wide on "
                f"{peak_row['date']}, {peak_row['vs_median_pct']:.0f}% above the "
                f"median week. Thanksgiving week {second_wk} is second at "
                f"{(second_si - 1) * 100:+.0f}%. Between them these two weeks "
                f"decide Q4, and the chain swings from a "
                f"${ts['Weekly_Sales'].min() / 1e6:.0f}M trough to an "
                f"${ts['Weekly_Sales'].max() / 1e6:.0f}M peak inside one year."),
     "action": (f"Plan labour, inventory and promotion against weeks "
                f"{peak_wk - 4}-52 specifically, not a generic Q4."),
     "tag": "Seasonality"},

    {"title": "The IsHoliday flag points at the wrong weeks",
     "metric": f"{B['flag_audit']['unflagged_in_top5']} of the 5 biggest weeks are flagged as normal",
     "detail": ((f"The Christmas flag falls on the week ending 31 Dec, which is "
                 f"the dead week after Christmas Day: those weeks average "
                 f"${xmas['avg_chain_week'] / 1e6:.1f}M against a December "
                 f"baseline of ${xmas['baseline_week'] / 1e6:.1f}M, a "
                 f"{xmas['lift_pct']:.0f}% shortfall. Meanwhile week {peak_wk} "
                 f"carries no flag at all. Thanksgiving is the one flag that "
                 f"works, at {best_hol['lift_pct']:+.0f}%; Super Bowl and Labor "
                 f"Day sit inside normal weekly noise.")
                if xmas and best_hol else ""),
     "action": ("Replace the binary flag with named holiday features and a "
                "week-of-year index before forecasting."),
     "tag": "Data quality"},

    {"title": "Small-format stores are the most productive floor space",
     "metric": f"Type C earns ${c_type['rev_per_sqft']:,.0f}/sq ft vs ${a_type['rev_per_sqft']:,.0f} for Type A",
     "detail": (f"Type A stores are {a_type['avg_size'] / c_type['avg_size']:.1f}x "
                f"larger and take {a_type['rev_share_pct']:.0f}% of revenue, but "
                f"Type C extracts "
                f"{(c_type['rev_per_sqft'] / a_type['rev_per_sqft'] - 1) * 100:.0f}% "
                f"more revenue from every square foot "
                f"(${c_type['rev_per_sqft']:,.0f} vs "
                f"${a_type['rev_per_sqft']:,.0f}; Type B sits between at "
                f"${b_type['rev_per_sqft']:,.0f}). The ranking by size and the "
                f"ranking by productivity run in opposite directions, and ANOVA "
                f"across formats is decisive (F={anova.statistic:,.0f}, "
                f"p<0.001)."),
     "action": ("Judge each format on revenue per square foot, and test "
                "small-format expansion rather than assuming bigger is better."),
     "tag": "Format"},

    {"title": "Macro conditions barely move the weekly till",
     "metric": f"Temperature, fuel, CPI and unemployment explain {models['economic']['r2'] * 100:.2f}% of variance",
     "detail": (f"A regression on the four economic indicators alone reaches "
                f"R2={models['economic']['r2']:.4f} - effectively nothing. "
                f"Adding store size and the holiday flag lifts it to "
                f"{models['full']['r2'] * 100:.1f}%, and aggregating to "
                f"store-week reaches {models['store_week']['r2'] * 100:.1f}%, "
                f"almost all of it from floor space. Structure beats sentiment: "
                f"what a store sells is set by what it is, not by the economy "
                f"that week."),
     "action": ("Forecast from store, department and calendar; carry macro "
                "series only as a slow-moving overlay."),
     "tag": "Drivers"},

    {"title": "Markdown depth looks powerful until you control for store size",
     "metric": f"${fe_slope:.2f} of sales per $1 of markdown, within store-dept",
     "detail": (f"Across records, the deepest markdown quintile averages "
                f"${md_bands[-1]['avg_sales']:,.0f} against "
                f"${md_bands[0]['avg_sales']:,.0f} in the lightest, a "
                f"{md_bands[-1]['vs_lightest_pct']:.0f}% gap that looks like a "
                f"strong promotion effect. It is mostly confounding: large "
                f"departments receive large markdowns and already sell more. "
                f"Removing each store-dept's own average leaves a slope of "
                f"${fe_slope:.3f} per markdown dollar, explaining "
                f"{fe_r2 * 100:.1f}% of a store's own week-to-week swing. "
                f"${md_total / 1e9:.2f}B of recorded markdown maps to roughly "
                f"${fe_slope * md_total / 1e6:.0f}M of measurable movement, and "
                f"the top quintile spends "
                f"{md_bands[-1]['avg_markdown'] / md_bands[-2]['avg_markdown']:.1f}x "
                f"the fourth for only "
                f"{md_bands[-1]['vs_lightest_pct'] - md_bands[-2]['vs_lightest_pct']:.0f}pp "
                f"more sales."),
     "action": ("Stop reading the raw markdown-vs-sales curve as ROI; rebuild "
                "measurement with a holdout group before committing more spend."),
     "tag": "Promotion"},

    {"title": "Revenue is concentrated in a handful of departments",
     "metric": f"{n80} of {len(dept)} departments produce 80% of revenue",
     "detail": (f"Department {top_dept['dept']} alone carries "
                f"{top_dept['share_pct']:.1f}% of revenue "
                f"(${top_dept['revenue'] / 1e6:,.0f}M), and the top ten take "
                f"{B['departments']['top10_share_pct']:.0f}%. The bottom half of "
                f"all departments contribute "
                f"{B['departments']['bottom50_share_pct']:.1f}% between them."),
     "action": ("Protect assortment and space in the top decile; review the "
                "long tail for delisting or consolidation."),
     "tag": "Mix"},

    {"title": "Closing the productivity gap is the largest single prize",
     "metric": f"${B['stores']['total_opportunity'] / 1e9:.2f}B of theoretical headroom",
     "detail": (f"{B['stores']['underperformers']} of 45 stores earn less per "
                f"square foot than the top-quartile benchmark of "
                f"${top_q_rps:,.0f}. Lifting every one of them to that "
                f"benchmark would add "
                f"{B['stores']['opportunity_pct_of_rev']:.0f}% of revenue across "
                f"the 143-week window with no new floor space. This is a "
                f"ceiling rather than a plan: it assumes the benchmark is "
                f"reachable everywhere, which location and catchment will "
                f"limit."),
     "action": ("Run a per-store productivity programme benchmarked on revenue "
                "per square foot, starting with the largest absolute gaps."),
     "tag": "Opportunity"},

    {"title": "Sales are far from normal, which breaks naive models",
     "metric": f"Skewness {skew:.1f}, excess kurtosis {kurt:.0f}",
     "detail": (f"Weekly sales are strongly right-skewed with heavy tails. The "
                f"Normal fit is rejected (KS={ks_n.statistic:.3f}, p<0.001) "
                f"while log-normal fits far better (KS={ks_l.statistic:.3f}); a "
                f"log transform pulls skew from {skew:.1f} to "
                f"{stats.skew(log_sales):.2f}. "
                f"{out_mask.mean() * 100:.1f}% of records fall outside the Tukey "
                f"fences, yet they carry "
                f"{outliers.sum() / total_rev * 100:.0f}% of all revenue."),
     "action": ("Model log sales or quantile targets, and never trim the high "
                "outliers - they are the business."),
     "tag": "Distribution"},

    {"title": "The chain is predictable week to week, and barely growing",
     "metric": (f"{bt['mape']:.1f}% MAPE on 13 held-out weeks" if bt else ""),
     "detail": ((f"A trend-times-seasonality model refitted on the first "
                 f"{bt['train_weeks']} weeks predicts the held-out "
                 f"{bt['weeks']} weeks to within {bt['mape']:.2f}%, against "
                 f"{bt['naive_mape']:.2f}% for a seasonal-naive benchmark. The "
                 f"underlying trend is close to flat at "
                 f"${slope / 1e3:,.0f}k per week on a "
                 f"${ts['Weekly_Sales'].mean() / 1e6:.0f}M weekly base, so "
                 f"nearly all movement is calendar, not growth.")
                if bt else ""),
     "action": ("Treat the weekly number as highly forecastable and spend "
                "planning debate on the seasonal peaks and the store-mix "
                "question."),
     "tag": "Forecast"},
]

D["business"] = B

# Experiment catalogue for the method tab.
D["experiments"] = [
    {"id": "exp1", "n": 1, "title": "Descriptive Statistics",
     "method": "Quartiles, IQR, Tukey fences, boxplots by store format",
     "headline": f"{out_mask.mean() * 100:.1f}% of records are outliers but carry {outliers.sum() / total_rev * 100:.1f}% of revenue"},
    {"id": "exp2", "n": 2, "title": "Linear Regression",
     "method": "OLS on economic and structural drivers, three specifications",
     "headline": f"R² rises from {models['economic']['r2']:.4f} (macro only) to {models['store_week']['r2']:.3f} at store-week level"},
    {"id": "exp3", "n": 3, "title": "Sampling",
     "method": "Simple random, stratified and systematic sampling vs population",
     "headline": f"A 10,000-record sample estimates the mean within {samples[4]['err_pct']:.2f}%"},
    {"id": "exp4", "n": 4, "title": "Clustering (K-Means)",
     "method": "Elbow + silhouette on six store features, PCA projection",
     "headline": f"Four store archetypes, silhouette {D['exp4']['silhouette']:.3f}"},
    {"id": "exp5", "n": 5, "title": "Probability Distribution",
     "method": "Weekly sales as a random variable: PDF, CDF, exceedance",
     "headline": f"P(sales > $50k) = {(sales > 50000).mean():.3f}, carrying {sales[sales > 50000].sum() / total_rev * 100:.0f}% of revenue"},
    {"id": "exp6", "n": 6, "title": "Theoretical Distributions",
     "method": "Normal, log-normal, gamma and exponential fits with KS tests",
     "headline": f"Log-normal fits best (KS {ks_l.statistic:.3f}); Normal is rejected"},
    {"id": "exp7", "n": 7, "title": "Statistical Inference",
     "method": "Welch t-test, ANOVA, Mann-Whitney, chi-square, correlations",
     "headline": f"Holiday lift of {(hol_mean / non_mean - 1) * 100:.1f}% is significant (p<0.001) but small (d={cohen_d:.3f})"},
    {"id": "exp8", "n": 8, "title": "Time Series Analysis",
     "method": "Moving averages, multiplicative decomposition, 14-week forecast",
     "headline": f"Backtest MAPE {bt['mape']:.1f}% over 13 held-out weeks" if bt else "Seasonal decomposition with 52-week period"},
]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(D, f, separators=(",", ":"), allow_nan=False)

import os
print(f"\nWrote {OUT} ({os.path.getsize(OUT) / 1024:.0f} KB)")
print(f"Total revenue       ${total_rev:,.0f}")
print(f"Holiday lift        {(hol_mean / non_mean - 1) * 100:+.2f}%  (p={tt.pvalue:.2e})")
print(f"Store-week model R² {models['store_week']['r2']:.4f}")
print(f"Clusters            k={K}, silhouette={D['exp4']['silhouette']:.3f}")
if bt:
    print(f"Forecast MAPE       {bt['mape']:.2f}%")
print(f"Revenue headroom    ${B['stores']['total_opportunity']:,.0f}")
