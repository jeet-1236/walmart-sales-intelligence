# Walmart Sales Intelligence

An interactive dashboard over 421,570 Walmart store-department-week sales records
(45 stores, 81 departments, 143 weeks from 5 Feb 2010 to 26 Oct 2012). It covers
eight statistical experiments and a business-impact layer, and every figure on the
page is read from a pre-computed table rather than recalculated in the browser.

**Live dashboard:** <https://jeet-1236.github.io/walmart-sales-intelligence/> — no sign-in, nothing to install.

That page is the static build in [`docs/`](docs/). The same dashboard also exists as a Streamlit app ([`app.py`](app.py)) if you would rather run it as a Python service; see *Deploying to Streamlit Community Cloud* below.

![tabs: Overview, Business impact, Stores, Statistics, Forecast, Method](https://img.shields.io/badge/tabs-6-informational)

## What it shows

| Tab | Contents |
| --- | --- |
| **Overview** | Headline KPIs, chain revenue across all 143 weeks, a calendar heatmap of every week, and nine written findings |
| **Business impact** | Holiday lift per holiday, department Pareto and treemap, revenue concentration, a store × department heatmap, markdown effectiveness, economic sensitivity, productivity headroom |
| **Stores** | 45 sparklines on one shared scale, a sortable scorecard, k-means archetypes with a PCA map, parallel coordinates, size-against-productivity scatters |
| **Statistics** | Experiments 1–7: descriptive statistics, three regression specifications, sampling and the CLT, probability distributions, distribution fitting, hypothesis tests and correlations |
| **Forecast** | Experiment 8: multiplicative decomposition, seasonal index, a 14-week forecast, and a backtest against a seasonal-naive benchmark |
| **Method** | How the dataset was built, the eight experiments, and six caveats that would change a conclusion if ignored |

## Three findings worth knowing

1. **The `IsHoliday` flag points at the wrong weeks.** It marks the week *ending*
   31 December — the dead week *after* Christmas, which runs about 29% *below* its
   December baseline. The actual annual peak, week 51 at $80.9M, is flagged `False`.
   Three of the five biggest weeks on record are labelled normal. A model trained on
   this flag as-is learns the wrong calendar.

2. **Small-format stores are the most productive floor space.** Type C earns about
   $1,667 per square foot against Type A's $1,111, which holds at median-store level
   too. Type A is 4.4× larger and takes 64% of revenue, so size and productivity rank
   in opposite directions.

3. **Markdown's apparent effect is mostly store-size confounding.** Across records the
   deepest markdown quintile averages 110% above the lightest. Remove each
   store-department's own mean and the slope falls to about $0.015 of sales per
   markdown dollar, explaining roughly 0.1% of variance. Markdowns are also recorded
   only from November 2011, and in that window *every* record carries one — so there
   is no zero-markdown control group anywhere in the data.

## Running it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app reads only `dashboard_sources/*.csv` (about 320 KB in total), so it starts
without the raw dataset present.

## Deploying to Streamlit Community Cloud

Optional — the GitHub Pages build above is already live. To run the Streamlit
version as a hosted service instead:

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **Create app** → **Deploy a public app from GitHub**.
3. Pick this repository, branch `main`, main file path `app.py`.
4. **Deploy.** The first build takes a couple of minutes.

Anyone with the resulting `*.streamlit.app` URL can then open it, with no sign-in.

## Regenerating the data

The raw Walmart files and the 40 MB integrated table are deliberately left out of
version control (see `.gitignore`); they are only needed to rebuild the source
tables, not to run the app. With them present:

```bash
python build_dashboard_data.py      # 8 experiments      -> dashboard_data.json
python build_dashboard_sources.py   # json -> 18 tables  -> dashboard_sources/
python build_dashboard_extras.py    # 2 more tables + 2 columns
```

| Script | Produces |
| --- | --- |
| `build_dashboard_data.py` | Runs all eight experiments and the business layer, writing one JSON of results |
| `build_dashboard_sources.py` | Flattens that JSON into 18 tidy CSVs, one per chart group |
| `build_dashboard_extras.py` | Adds the per-store weekly series, the store × department matrix, and growth/returns columns |
| `app.py` | The Streamlit dashboard |
| `build_pages.py` | Wraps the artifact page into the standalone `docs/` site served by GitHub Pages |

## Method notes

- **Forecast.** Trend is a 52-week centred moving average; because that stops ~26
  weeks short of the series end, projections carry the gap as well as the horizon.
  The backtest refits *both* the trend and the seasonal index on the first 130 weeks
  only, so the 13 scored weeks are fully held out. It reaches about 1.8% MAPE against
  2.0% for a seasonal-naive benchmark — the model wins, but not by much, because a
  series this seasonal makes last year's same week a strong guess already.
- **Clustering.** K-means on six standardised store features, k chosen at 4 from the
  elbow and silhouette. Silhouette is about 0.27, so the archetypes are real but they
  overlap; treat them as a description, not a partition.
- **Headroom.** The $1.69B figure assumes every store below the top-quartile
  benchmark for revenue per square foot could reach it. Catchment and competition cap
  what any individual store can do, so it is a ceiling worth investigating, not a
  target.
- **Significance.** At this sample size nearly every test rejects its null. The
  holiday difference has a p-value below any threshold and a Cohen's d near 0.05,
  which is negligible. Read effect sizes, not stars.

## Data

The Walmart Store Sales Forecasting dataset (`train`, `test`, `stores`, `features`),
joined on `Store` and on `Store` + `Date`. Store identities are anonymous and carry
no geography, so nothing here separates a regional effect from a store-specific one.
