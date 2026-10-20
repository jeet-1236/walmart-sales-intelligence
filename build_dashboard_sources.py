"""
dashboard_data.json -> dashboard_sources/*.csv

The dashboard attributes every figure to a source file, so each table below
becomes one dataset on the page. Long/tidy shapes are used wherever a single
row has to be addressable by name (metric=..., series=...).

Usage:  python build_dashboard_sources.py
"""

import csv
import json
import os

IN = "dashboard_data.json"
OUT_DIR = "dashboard_sources"

D = json.load(open(IN, encoding="utf-8"))
os.makedirs(OUT_DIR, exist_ok=True)

M = D["meta"]
B = D["business"]
E1, E2, E3 = D["exp1"], D["exp2"], D["exp3"]
E4, E5, E6 = D["exp4"], D["exp5"], D["exp6"]
E7, E8 = D["exp7"], D["exp8"]

written = {}


def write(name, cols, rows):
    path = os.path.join(OUT_DIR, f"{name}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])
    written[name] = (len(rows), os.path.getsize(path))
    return path


# ---------------------------------------------------------------- 1. kpis
# Every scalar the page shows, addressable as data-where="metric=<id>".
K = []


def kpi(metric, label, value, unit="", group="", note=""):
    K.append([metric, label, value, unit, group, note])


# Overview
kpi("total_revenue", "Total revenue", M["total_revenue"], "usd", "overview",
    "Sum of Weekly_Sales across all store-dept-weeks")
kpi("records", "Store-dept-week records", M["records"], "count", "overview")
kpi("stores", "Stores", M["stores"], "count", "overview")
kpi("depts", "Departments", M["depts"], "count", "overview")
kpi("weeks", "Weeks observed", M["weeks"], "count", "overview")
kpi("avg_weekly_chain", "Average week, chain-wide", M["avg_weekly_chain"],
    "usd", "overview")
kpi("total_sqft", "Total floor space", M["total_sqft"], "sqft", "overview")
kpi("rev_per_sqft", "Revenue per sq ft", M["rev_per_sqft"], "usd", "overview",
    "Total revenue over total floor space, across 143 weeks")
kpi("holiday_lift_pct", "Holiday lift, per store-dept", M["holiday_lift_pct"],
    "pct", "overview")
kpi("negative_records", "Records with negative sales", M["negative_records"],
    "count", "overview")
kpi("negative_value", "Value of negative sales", M["negative_value"], "usd",
    "overview")
kpi("date_span", "Weeks from first to last", M["weeks"], "count", "overview",
    f"{M['date_start']} to {M['date_end']}")

# Exp 1 - descriptive
s = E1["sales"]
for k, lab, unit in [
    ("q1", "Q1 (25th percentile)", "usd"), ("q2", "Median (Q2)", "usd"),
    ("q3", "Q3 (75th percentile)", "usd"), ("iqr", "Interquartile range", "usd"),
    ("fence_lo", "Lower Tukey fence", "usd"), ("fence_hi", "Upper Tukey fence", "usd"),
    ("mean", "Mean weekly sales", "usd"), ("std", "Standard deviation", "usd"),
    ("min", "Minimum", "usd"), ("max", "Maximum", "usd"),
    ("outlier_count", "Outlier records", "count"),
    ("outlier_pct", "Outlier share of records", "pct"),
    ("outlier_revenue", "Revenue inside outliers", "usd"),
    ("outlier_revenue_pct", "Outlier share of revenue", "pct"),
    ("outliers_high", "Outliers above upper fence", "count"),
    ("outliers_low", "Outliers below lower fence", "count"),
]:
    kpi(f"e1_{k}", lab, s[k], unit, "exp1")

# Exp 2 - regression
for mid, m in E2["models"].items():
    kpi(f"e2_{mid}_r2", f"R-squared, {mid} model", m["r2"], "ratio", "exp2")
    kpi(f"e2_{mid}_adj_r2", f"Adjusted R-squared, {mid} model", m["adj_r2"],
        "ratio", "exp2")
    kpi(f"e2_{mid}_rmse", f"RMSE, {mid} model", m["rmse"], "usd", "exp2")
    kpi(f"e2_{mid}_n", f"Observations, {mid} model", m["n"], "count", "exp2")
kpi("e2_full_mae", "MAE, full model", E2["models"]["full"]["mae"], "usd", "exp2")

# Exp 3 - sampling
p = E3["population"]
kpi("e3_pop_mean", "Population mean", p["mean"], "usd", "exp3")
kpi("e3_pop_std", "Population std dev", p["std"], "usd", "exp3")
kpi("e3_pop_median", "Population median", p["median"], "usd", "exp3")
kpi("e3_pop_n", "Population size", p["n"], "count", "exp3")
c = E3["clt"]
kpi("e3_clt_reps", "Repeated samples drawn", c["reps"], "count", "exp3")
kpi("e3_clt_size", "Size of each sample", c["sample_size"], "count", "exp3")
kpi("e3_clt_mean", "Mean of sample means", c["mean_of_means"], "usd", "exp3")
kpi("e3_clt_std", "Observed spread of sample means", c["std_of_means"], "usd",
    "exp3")
kpi("e3_clt_se", "Standard error predicted by theory", c["theoretical_se"],
    "usd", "exp3")
st = E3["stratified"]
kpi("e3_strat_estimate", "Stratified estimate of the mean", st["estimate"],
    "usd", "exp3")
kpi("e3_strat_err", "Stratified estimate error", st["err_pct"], "pct", "exp3")
sy = E3["systematic"]
kpi("e3_sys_mean", "Systematic sample mean", sy["mean"], "usd", "exp3")
kpi("e3_sys_err", "Systematic sample error", sy["err_pct"], "pct", "exp3")
kpi("e3_sys_k", "Systematic sampling interval", sy["k"], "count", "exp3")

# Exp 4 - clustering
kpi("e4_k", "Clusters chosen", E4["k"], "count", "exp4")
kpi("e4_silhouette", "Silhouette score", E4["silhouette"], "ratio", "exp4")
kpi("e4_inertia", "Inertia at chosen k", E4["inertia"], "ratio", "exp4")
kpi("e4_pca1", "Variance explained by PC1", E4["pca_var"][0], "pct", "exp4")
kpi("e4_pca2", "Variance explained by PC2", E4["pca_var"][1], "pct", "exp4")

# Exp 5 - probability
kpi("e5_mean", "Expected weekly sales", E5["mean"], "usd", "exp5")
kpi("e5_variance", "Variance", E5["variance"], "usd2", "exp5")
kpi("e5_std", "Standard deviation", E5["std"], "usd", "exp5")
kpi("e5_cv", "Coefficient of variation", E5["cv"], "ratio", "exp5")
for row in E5["percentiles"]:
    kpi(f"e5_p{row['p']}", f"{row['p']}th percentile", row["value"], "usd",
        "exp5")
sw5 = E5["store_week"]
kpi("e5_sw_mean", "Average store-week revenue", sw5["mean"], "usd", "exp5")
kpi("e5_sw_std", "Store-week std dev", sw5["std"], "usd", "exp5")
kpi("e5_sw_p5", "Store-week 5th percentile", sw5["p5"], "usd", "exp5")
kpi("e5_sw_p95", "Store-week 95th percentile", sw5["p95"], "usd", "exp5")

# Exp 6 - theoretical distributions
sh = E6["shape"]
kpi("e6_skew", "Skewness", sh["skewness"], "ratio", "exp6")
kpi("e6_kurtosis", "Excess kurtosis", sh["kurtosis_excess"], "ratio", "exp6")
kpi("e6_jb_p", "Jarque-Bera p-value", sh["jarque_bera_p"], "p", "exp6")
kpi("e6_log_skew", "Skewness after log transform",
    E6["log_transform"]["skewness"], "ratio", "exp6")
kpi("e6_log_kurtosis", "Excess kurtosis after log transform",
    E6["log_transform"]["kurtosis_excess"], "ratio", "exp6")
cw = E6["chain_weekly_normality"]
kpi("e6_shapiro_stat", "Shapiro-Wilk statistic, chain weekly total",
    cw["shapiro_stat"], "ratio", "exp6")
kpi("e6_shapiro_p", "Shapiro-Wilk p-value, chain weekly total",
    cw["shapiro_p"], "p", "exp6")
kpi("e6_chain_skew", "Skewness of chain weekly total", cw["skewness"], "ratio",
    "exp6")
po = E6["poisson"]
kpi("e6_lambda", "Lambda, above-average store-weeks per week", po["lambda"],
    "count", "exp6")
kpi("e6_dispersion", "Variance-to-mean ratio", po["dispersion"], "ratio",
    "exp6")

# Exp 7 - inference
me = E7["mean_estimate"]
kpi("e7_mean", "Estimated mean weekly sales", me["point"], "usd", "exp7")
kpi("e7_se", "Standard error of the mean", me["se"], "usd", "exp7")
kpi("e7_ci95_lo", "95% CI lower bound", me["ci95_lo"], "usd", "exp7")
kpi("e7_ci95_hi", "95% CI upper bound", me["ci95_hi"], "usd", "exp7")
kpi("e7_ci99_lo", "99% CI lower bound", me["ci99_lo"], "usd", "exp7")
kpi("e7_ci99_hi", "99% CI upper bound", me["ci99_hi"], "usd", "exp7")
ht = E7["holiday_test"]
kpi("e7_hol_mean", "Mean on holiday weeks", ht["holiday_mean"], "usd", "exp7")
kpi("e7_non_mean", "Mean on normal weeks", ht["nonholiday_mean"], "usd", "exp7")
kpi("e7_hol_diff", "Difference in means", ht["diff"], "usd", "exp7")
kpi("e7_hol_lift", "Holiday lift", ht["lift_pct"], "pct", "exp7")
kpi("e7_hol_t", "Welch t statistic", ht["t_stat"], "ratio", "exp7")
kpi("e7_hol_p", "Welch t p-value", ht["p_value"], "p", "exp7")
kpi("e7_hol_d", "Cohen's d", ht["cohen_d"], "ratio", "exp7")
kpi("e7_hol_mw_p", "Mann-Whitney p-value", ht["mannwhitney_p"], "p", "exp7")
kpi("e7_hol_n", "Holiday records", ht["holiday_n"], "count", "exp7")
kpi("e7_non_n", "Normal-week records", ht["nonholiday_n"], "count", "exp7")
an = E7["anova_store_type"]
kpi("e7_anova_f", "ANOVA F statistic across formats", an["f_stat"], "ratio",
    "exp7")
kpi("e7_anova_p", "ANOVA p-value", an["p_value"], "p", "exp7")
kpi("e7_kruskal_p", "Kruskal-Wallis p-value", an["kruskal_p"], "p", "exp7")
cs = E7["chi_square"]
kpi("e7_chi2", "Chi-square statistic", cs["statistic"], "ratio", "exp7")
kpi("e7_chi2_p", "Chi-square p-value", cs["p_value"], "p", "exp7")
kpi("e7_chi2_dof", "Chi-square degrees of freedom", cs["dof"], "count", "exp7")

# Exp 8 - time series
bt = E8["backtest"]
kpi("e8_mape", "Backtest MAPE", bt["mape"], "pct", "exp8")
kpi("e8_naive_mape", "Seasonal-naive MAPE", bt["naive_mape"], "pct", "exp8")
kpi("e8_rmse", "Backtest RMSE", bt["rmse"], "usd", "exp8")
kpi("e8_mae", "Backtest MAE", bt["mae"], "usd", "exp8")
kpi("e8_train_weeks", "Weeks used to fit", bt["train_weeks"], "count", "exp8")
kpi("e8_holdout_weeks", "Weeks held out", bt["weeks"], "count", "exp8")
kpi("e8_trend_slope", "Trend slope per week", E8["trend_slope_per_week"], "usd",
    "exp8")
kpi("e8_forecast_total", "Next 14 weeks forecast", E8["forecast_total"], "usd",
    "exp8")
kpi("e8_peak_value", "Largest week on record", E8["peak"]["value"], "usd",
    "exp8", E8["peak"]["date"])
kpi("e8_trough_value", "Smallest week on record", E8["trough"]["value"], "usd",
    "exp8", E8["trough"]["date"])
kpi("e8_resid_std", "Residual spread of the decomposition", E8["resid_std"],
    "ratio", "exp8")
kpi("e8_peak_week_index", "Seasonal index, peak week",
    E8["peak_weeks"][0]["index"], "ratio", "exp8",
    f"week {E8['peak_weeks'][0]['week']}")
kpi("e8_peak_week", "Peak week of the year", E8["peak_weeks"][0]["week"],
    "count", "exp8")

# Business
hol = B["holidays"]
kpi("b_hol_week_rev", "Average flagged-holiday week", hol["avg_holiday_week_rev"],
    "usd", "business")
kpi("b_normal_week_rev", "Average normal week", hol["avg_normal_week_rev"],
    "usd", "business")
kpi("b_hol_lift_pct", "Chain lift on flagged holiday weeks",
    hol["chain_week_lift_pct"], "pct", "business")
kpi("b_hol_incremental", "Revenue attributed to flagged holiday weeks",
    hol["incremental_revenue"], "usd", "business")
kpi("b_december_week", "Average December week", hol["december_avg_week"], "usd",
    "business")
kpi("b_december_vs_year", "December week vs the average week",
    hol["december_vs_year_pct"], "pct", "business")
dp = B["departments"]
kpi("b_depts_for_80", "Departments producing 80% of revenue",
    dp["depts_for_80pct"], "count", "business")
kpi("b_top10_dept_share", "Revenue share of the top 10 departments",
    dp["top10_share_pct"], "pct", "business")
kpi("b_bottom50_dept_share", "Revenue share of the bottom half of departments",
    dp["bottom50_share_pct"], "pct", "business")
sr = B["stores"]
kpi("b_median_rps", "Median store revenue per sq ft", sr["median_rev_per_sqft"],
    "usd", "business")
kpi("b_topq_rps", "Top-quartile revenue per sq ft",
    sr["top_quartile_rev_per_sqft"], "usd", "business")
kpi("b_underperformers", "Stores below the top-quartile benchmark",
    sr["underperformers"], "count", "business")
kpi("b_opportunity", "Revenue headroom to the benchmark", sr["total_opportunity"],
    "usd", "business",
    "Theoretical ceiling: every store lifted to top-quartile productivity")
kpi("b_opportunity_pct", "Headroom as a share of revenue",
    sr["opportunity_pct_of_rev"], "pct", "business")
kpi("b_top10_store_share", "Revenue share of the top 10 stores",
    sr["top10_rev_share_pct"], "pct", "business")
kpi("b_bottom10_store_share", "Revenue share of the bottom 10 stores",
    sr["bottom10_rev_share_pct"], "pct", "business")
kpi("b_spread_ratio", "Largest store over smallest, by revenue",
    sr["spread_ratio"], "ratio", "business")
rk = B["risk"]
kpi("b_chain_cv", "Chain-level coefficient of variation", rk["chain_cv"],
    "ratio", "business")
kpi("b_best_spike", "Best week against the median week",
    rk["best_week_spike_pct"], "pct", "business")
kpi("b_worst_drop", "Worst week against the median week",
    rk["worst_week_drop_pct"], "pct", "business")
md = B["markdowns"]
kpi("b_md_spend", "Recorded markdown spend", md["total_markdown_spend"], "usd",
    "business")
kpi("b_md_records", "Records in the markdown window", md["records_in_period"],
    "count", "business")
kpi("b_md_coverage", "Markdown coverage inside that window", md["coverage_pct"],
    "pct", "business")
fe = md["fixed_effects"]
kpi("b_md_slope", "Sales per markdown dollar, within store-dept", fe["slope"],
    "usd", "business")
kpi("b_md_r2", "Variance explained by markdown depth", fe["r2"], "ratio",
    "business")
kpi("b_md_slope_hol", "Sales per markdown dollar, holiday controlled",
    fe["slope_with_holiday"], "usd", "business")
kpi("b_md_attributable", "Sales movement attributable to markdown",
    fe["attributable_sales"], "usd", "business")
rt = B["returns"]
kpi("b_returns_records", "Records with net returns", rt["records"], "count",
    "business")
kpi("b_returns_value", "Net value of those records", rt["value"], "usd",
    "business")
kpi("b_returns_pct", "Returns as a share of revenue", rt["pct_of_revenue"],
    "pct", "business")
kpi("b_returns_stores", "Stores affected", rt["stores_affected"], "count",
    "business")
fa = B["flag_audit"]
kpi("b_unflagged_top5", "Of the 5 biggest weeks, flagged as normal",
    fa["unflagged_in_top5"], "count", "business")

write("kpis", ["metric", "label", "value", "unit", "group", "note"], K)

# ---------------------------------------------------------------- 2. weekly
write("weekly",
      ["date", "sales", "ma4", "ma12", "trend", "seasonal", "resid", "holiday"],
      [[r["d"], r["v"], r["ma4"], r["ma12"], r["tr"], r["se"], r["re"],
        "yes" if r["h"] else "no"] for r in E8["series"]])

# -------------------------------------------------------------- 3. forecast
F = [["forecast", f["d"], f["week"], f["v"], f["lo"], f["hi"], None]
     for f in E8["forecast"]]
F += [["backtest", b["d"], None, b["a"], None, None, b["p"]]
      for b in bt["rows"]]
write("forecast", ["kind", "date", "week", "value", "lo", "hi", "predicted"], F)

# ---------------------------------------------------------------- 4. stores
pts = {p["store"]: p for p in E4["points"]}
write("stores",
      ["store", "rank", "type", "cluster", "size", "total_rev", "avg_weekly",
       "rev_per_sqft", "cv", "hol_lift", "growth_pct", "cpi", "unemployment",
       "depts", "rev_share_pct", "gap_to_benchmark", "pca_x", "pca_y"],
      [[r["store"], r["rank"], r["type"], r["cluster"], r["size"],
        r["total_rev"], r["avg_weekly"], r["rev_per_sqft"], r["cv"],
        r["hol_lift"], r["growth_pct"], r["cpi"], r["unemployment"],
        r["depts"], r["rev_share_pct"], r["gap_to_top_quartile"],
        pts[r["store"]]["x"], pts[r["store"]]["y"]]
       for r in B["stores"]["rows"]])

# ----------------------------------------------------------------- 5. depts
write("depts",
      ["dept", "revenue", "share_pct", "cum_pct", "avg", "cv", "stores",
       "hol_lift", "records"],
      [[r["dept"], r["revenue"], r["share_pct"], r["cum_pct"], r["avg"],
        r["cv"], r["stores"], r["hol_lift"], r["records"]]
       for r in dp["rows"]])

# -------------------------------------------------------------- 6. segments
# Store formats and k-means clusters share one shape: a group of stores.
box = {b["type"]: b for b in E1["box_by_type"]}
S = []
for t in B["store_types"]:
    b = box[t["type"]]
    S.append(["format", f"Type {t['type']}", t["stores"], t["revenue"],
              t["rev_share_pct"], t["avg_size"], t["rev_per_sqft"],
              t["avg_weekly_per_store"], t["cv"], None, None, None,
              b["lo"], b["q1"], b["median"], b["q3"], b["hi"]])
for c in E4["clusters"]:
    S.append(["cluster", c["name"], c["n"], c["total_rev"], c["rev_share_pct"],
              c["avg_size"], c["rev_per_sqft"], c["avg_weekly_rev"], c["cv"],
              c["hol_lift"], c["cpi"], c["unemployment"],
              None, None, None, None, None])
write("segments",
      ["kind", "group", "stores", "revenue", "rev_share_pct", "avg_size",
       "rev_per_sqft", "avg_weekly_per_store", "cv", "hol_lift", "cpi",
       "unemployment", "box_lo", "box_q1", "box_median", "box_q3", "box_hi"],
      S)

# -------------------------------------------------------------- 7. holidays
write("holidays",
      ["holiday", "weeks_observed", "avg_chain_week", "baseline_week",
       "lift_abs", "lift_pct", "total_revenue", "dates"],
      [[h["holiday"], h["weeks_observed"], h["avg_chain_week"],
        h["baseline_week"], h["lift_abs"], h["lift_pct"], h["total_revenue"],
        " / ".join(h["dates"])] for h in hol["by_holiday"]])

# -------------------------------------------------------------- 8. findings
write("findings", ["n", "tag", "title", "metric", "detail", "action"],
      [[i, f["tag"], f["title"], f["metric"], f["detail"], f["action"]]
       for i, f in enumerate(B["findings"], 1)])

# ---------------------------------------------------------------- 9. curves
# Every x/y curve the page draws, one series per name.
C = []


def curve(series, xs, ys, y2=None):
    for i, (x, y) in enumerate(zip(xs, ys)):
        C.append([series, x, y, None if y2 is None else y2[i]])


h = E1["histogram"]
curve("sales_hist", h["edges"][:-1], h["counts"])
curve("pdf", E5["pdf"]["x"], E5["pdf"]["y"])
curve("cdf", E5["cdf"]["x"], E5["cdf"]["y"])
ov = E6["overlay"]
curve("empirical_density", ov["x"], ov["empirical"])
curve("normal_density", ov["x"], ov["normal"])
curve("lognormal_density", ov["x"], ov["lognormal"])
curve("qq", E6["qq"]["theoretical"], E6["qq"]["empirical"])
clt = E3["clt"]
curve("clt_hist", clt["edges"][:-1], clt["counts"])
for row in E4["elbow"]:
    C.append(["elbow", row["k"], row["inertia"], row.get("silhouette")])
for row in E5["exceedance"]:
    C.append(["exceedance", row["threshold"], row["p_gt"], row["rev_share_pct"]])
for row in E2["scatter"]:
    C.append(["fit_scatter", row["p"], row["a"], None])
rh = E2["resid_hist"]
curve("resid_hist", rh["edges"][:-1], rh["counts"])
# fit_scatter repeats x values, so the page keys this table on a row id
C = [[i] + row for i, row in enumerate(C, 1)]
write("curves", ["id", "series", "x", "y", "y2"], C)

# -------------------------------------------------------------- 10. sampling
SA = [["simple random", f"n = {r['n']:,}", r["n"], r["mean"], r["std"],
       r["median"], r["se"], r["ci_lo"], r["ci_hi"], r["err_pct"]]
      for r in E3["simple_random"]]
for r in st["rows"]:
    SA.append(["stratified", f"Type {r['type']}", r["n"], r["sample_mean"],
               None, None, None, None, None, r["err_pct"]])
SA.append(["systematic", f"every {sy['k']}th record", sy["n"], sy["mean"],
           sy["std"], None, None, None, None, sy["err_pct"]])
write("sampling",
      ["method", "label", "n", "mean", "std", "median", "se", "ci_lo", "ci_hi",
       "err_pct"], SA)

# ----------------------------------------------------------------- 11. model
MO = []
for mid, m in E2["models"].items():
    for c in m["coefficients"]:
        MO.append([mid, c["name"], c["coef"], c.get("se"), c.get("t"),
                   c.get("p"), None])
for sv in E2["single"]:
    MO.append(["single", sv["name"], sv["slope"], None, None, None, sv["r2"]])
for el in B["economics"]["elasticities"]:
    MO.append(["elasticity", el["driver"], el["impact_per_sd"], None, None,
               None, el["impact_per_sd_pct"]])
write("model", ["model", "feature", "coef", "se", "t", "p", "r2"], MO)

# ----------------------------------------------------------- 12. correlation
CO = []
lab = E7["correlation"]["labels"]
for level, key in [("record", "matrix"), ("store_week", "store_week_matrix")]:
    mat = E7["correlation"][key]
    for i, a in enumerate(lab):
        for j, b in enumerate(lab):
            CO.append([level, a, b, mat[i][j]])
write("correlation", ["level", "var1", "var2", "r"], CO)

# ---------------------------------------------------------- 13. seasonality
SE = [["week", str(r["week"]), r["week"], r["index"], None]
      for r in E8["seasonal_index"]]
SE += [["month", r["month"], i + 1, r["index"], r["avg"]]
       for i, r in enumerate(E8["month_index"])]
SE += [["month_series", r["label"], r["year"] * 100 + r["month"], None,
        r["revenue"]] for r in B["monthly"]]
SE += [["year", str(r["year"]), r["year"], r.get("growth_pct"), r["revenue"]]
       for r in E8["yoy"]]
write("seasonality", ["kind", "label", "sort", "index", "value"], SE)

# ------------------------------------------------------------- 14. markdown
MD = [["band", r["band"], r["avg_sales"], r["records"], r["avg_markdown"],
       r["vs_lightest_pct"], None] for r in md["bands"]]
MD += [["channel", r["channel"], r["avg"], r["total"], r["share_pct"],
        r["pct_records_active"], r["corr_within_store"]]
       for r in md["by_channel"]]
write("markdown",
      ["kind", "label", "avg_sales", "records_or_total", "markdown_or_share",
       "vs_lightest_or_active", "corr_within_store"], MD)

# ----------------------------------------------------------- 15. econ_bands
EB = []
for driver, key in [("Unemployment", "unemployment"), ("Fuel price", "fuel"),
                    ("Temperature", "temperature"), ("CPI", "cpi")]:
    for i, r in enumerate(B["economics"][key]):
        EB.append([driver, r["band"], i, r["avg"], r["n"], r["vs_first_pct"]])
write("econ_bands", ["driver", "band", "sort", "avg", "n", "vs_first_pct"], EB)

# ----------------------------------------------------------- 16. dist_fits
def pstr(d):
    return ", ".join(f"{k}={v}" for k, v in d.items())


write("dist_fits", ["name", "params", "ks_stat", "ks_p", "note"],
      [[f["name"], pstr(f["params"]), f["ks_stat"], f["ks_p"],
        f.get("note", "")] for f in E6["fits"]])

# --------------------------------------------------------- 17. experiments
write("experiments", ["n", "id", "title", "method", "headline"],
      [[e["n"], e["id"], e["title"], e["method"], e["headline"]]
       for e in D["experiments"]])

# ------------------------------------------------------------ 18. top_weeks
write("top_weeks", ["date", "week", "revenue", "flagged", "vs_median_pct"],
      [[w["date"], w["week"], w["revenue"], "yes" if w["flagged"] else "no",
        w["vs_median_pct"]] for w in fa["top_weeks"]])

print(f"{len(written)} source files in {OUT_DIR}/\n")
total = 0
for n, (rows, size) in sorted(written.items()):
    print(f"  {n:<14} {rows:>6,} rows   {size / 1024:>7.1f} KB")
    total += size
print(f"\n  total {total / 1024:.0f} KB")
