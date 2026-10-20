"""
Walmart Sales Intelligence - Streamlit dashboard.

Reads the pre-computed source tables in dashboard_sources/, which are produced
by build_dashboard_data.py -> build_dashboard_sources.py -> build_dashboard_extras.py
from the integrated Walmart dataset (421,570 store-dept-week records).

Run locally:   streamlit run app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

DATA = Path(__file__).parent / "dashboard_sources"

# A deliberate palette: deep blue carries the data, ochre the comparison series,
# sage and plum the remaining categories, brick reserved for "below baseline".
BLUE, OCHRE, SAGE, PLUM = "#2F6D9E", "#C87F3D", "#5B8C6A", "#9B5B7D"
MUTED, BRICK = "#9AA3AB", "#B5483D"
SERIES = [BLUE, OCHRE, SAGE, PLUM, "#6E7FA8", "#A98455"]
GRID, AXIS, INK, FADE = "#E6E9ED", "#C3C9D0", "#1F2933", "#667080"

st.set_page_config(page_title="Walmart Sales Intelligence",
                   page_icon="chart_with_upwards_trend", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 2.2rem; max-width: 1500px; }
  [data-testid="stMetricValue"] { font-size: 1.55rem; }
  [data-testid="stMetricLabel"] { color: #667080; }
  .wsi-find { border: 1px solid #E6E9ED; border-radius: 8px; padding: 14px 16px;
    background: #FBFCFD; height: 100%; }
  .wsi-tag { display:inline-block; font-size:.72rem; color:#667080;
    border:1px solid #E6E9ED; border-radius:4px; padding:1px 6px; margin-bottom:6px; }
  .wsi-ft { font-size:.98rem; font-weight:600; line-height:1.35; margin-bottom:4px; }
  .wsi-fm { font-size:1.02rem; color:#2F6D9E; margin-bottom:8px; }
  .wsi-fd { font-size:.82rem; line-height:1.55; color:#49535C; margin-bottom:8px; }
  .wsi-fa { font-size:.82rem; line-height:1.5; border-top:1px solid #E6E9ED;
    padding-top:7px; color:#1F2933; }
  .wsi-cap { font-size:.82rem; color:#667080; line-height:1.55; }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------- loading
@st.cache_data(show_spinner=False)
def load(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / f"{name}.csv")


def num(df, *cols):
    df = df.copy()
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def kpi_map() -> dict:
    k = load("kpis")
    return {r.metric: (r.value, r.unit, r.label, r.note)
            for r in k.itertuples()}


K = kpi_map()


def fmt(unit, v):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    v = float(v)
    if unit == "usd":
        a = abs(v)
        if a >= 1e9:
            return f"${v / 1e9:,.2f}B"
        if a >= 1e6:
            return f"${v / 1e6:,.1f}M"
        if a >= 1e3:
            return f"${v:,.0f}"
        if a >= 1:
            return f"${v:,.2f}"
        return f"${v:,.3f}"
    if unit == "usd2":
        return f"${v:,.3g}"
    if unit == "pct":
        return f"{v:,.2f}%"
    if unit in ("count", "sqft"):
        return f"{v:,.0f}"
    if unit == "p":
        return "< 0.0001" if 0 < abs(v) < 1e-4 else f"{v:,.4f}"
    if unit == "ratio":
        return f"{v:,.4g}"
    return f"{v:,.2f}"


def kv(metric):
    """A KPI formatted for display, by its id."""
    if metric not in K:
        return "—"
    v, unit, _, _ = K[metric]
    return fmt(unit, v)


def kraw(metric, default=np.nan):
    return float(K[metric][0]) if metric in K else default


def dstr(ts):
    """'Dec 24, 2010' without a leading zero, portably (Windows has no %-d)."""
    ts = pd.Timestamp(ts)
    return f"{ts:%b} {ts.day}, {ts.year}"


def base_fig(h=330, margin=None, showlegend=False):
    fig = go.Figure()
    fig.update_layout(
        height=h, showlegend=showlegend,
        margin=margin or dict(l=10, r=14, t=16, b=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, Segoe UI, sans-serif",
                  size=12, color=INK),
        hoverlabel=dict(bgcolor="white", bordercolor=AXIS,
                        font=dict(size=12, color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=AXIS,
                     ticks="outside", tickcolor=AXIS, tickfont=dict(color=FADE))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                     linecolor="rgba(0,0,0,0)", tickfont=dict(color=FADE))
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch",
                    config={"displayModeBar": False})


def cap(text):
    st.markdown(f'<div class="wsi-cap">{text}</div>', unsafe_allow_html=True)


def ramp(t):
    """Opacity ramp, so one hue carries intensity."""
    return float(min(1.0, 0.08 + max(0.0, t) ** 0.62 * 0.9))


# ------------------------------------------------------------------ header
st.title("Walmart Sales Intelligence")
st.markdown(
    f"Across **{kv('weeks')}** weeks, **{kv('stores')}** stores and "
    f"**{kv('depts')}** departments this chain turned over "
    f"**{kv('total_revenue')}**. Almost none of that movement is the economy; "
    f"it is the calendar and the store itself. The largest prize here is "
    f"**{kv('b_opportunity')}** of floor-space productivity the weaker stores "
    f"never reach."
)

# ----------------------------------------------------------------- sidebar
stores_df = num(load("stores"), "store", "size", "total_rev", "avg_weekly",
                "rev_per_sqft", "cv", "hol_lift", "growth_pct", "unemployment",
                "gap_to_benchmark", "pca_x", "pca_y", "rev_share_pct", "rank")

with st.sidebar:
    st.subheader("Filters")
    fmt_pick = st.radio("Store format", ["All", "A", "B", "C"], horizontal=True)
    store_opts = ["None"] + [str(int(s)) for s in sorted(stores_df["store"])]
    store_pick = st.selectbox("Highlight a store", store_opts)
    st.divider()
    st.caption(
        "Every figure comes from a pre-computed table in `dashboard_sources/`. "
        "The underlying dataset is 421,570 store-dept-week records covering "
        f"{K['date_span'][3] if 'date_span' in K else '2010–2012'}."
    )

FMT = None if fmt_pick == "All" else fmt_pick
SEL = None if store_pick == "None" else int(store_pick)

tabs = st.tabs(["Overview", "Business impact", "Stores", "Statistics",
                "Forecast", "Method"])

# ==================================================================== OVERVIEW
with tabs[0]:
    c = st.columns(6)
    c[0].metric("Total revenue", kv("total_revenue"), help="143 weeks, all stores")
    c[1].metric("Average week", kv("avg_weekly_chain"), help="chain-wide")
    c[2].metric("Revenue per sq ft", kv("rev_per_sqft"))
    c[3].metric("Biggest week", kv("e8_peak_value"),
                help=f"week ending {K['e8_peak_value'][3]}")
    c[4].metric("Quietest week", kv("e8_trough_value"),
                help=f"week ending {K['e8_trough_value'][3]}")
    c[5].metric("Forecast error", kv("e8_mape"), help="MAPE, 13 held-out weeks")

    st.subheader("Every week of the chain")
    cap("Total weekly sales across all 45 stores. The two spikes each year are the "
        "pre-Christmas week and Thanksgiving week.")
    wk = num(load("weekly"), "sales", "ma4", "ma12", "trend", "seasonal", "resid")
    wk["date"] = pd.to_datetime(wk["date"])
    overlays = st.multiselect("Overlays", ["4-week average", "12-week average",
                                           "52-week trend", "Flagged holidays"],
                              default=["52-week trend", "Flagged holidays"],
                              key="ov_overlay")
    fig = base_fig(360, showlegend=True)
    fig.add_trace(go.Scatter(x=wk["date"], y=wk["sales"], name="Chain revenue",
                             mode="lines", line=dict(color=BLUE, width=2),
                             fill="tozeroy", fillcolor="rgba(47,109,158,0.12)",
                             hovertemplate="%{x|%b %-d, %Y}<br>$%{y:,.0f}<extra></extra>"))
    if "4-week average" in overlays:
        fig.add_trace(go.Scatter(x=wk["date"], y=wk["ma4"], name="4-week average",
                                 mode="lines", line=dict(color=OCHRE, width=1.5)))
    if "12-week average" in overlays:
        fig.add_trace(go.Scatter(x=wk["date"], y=wk["ma12"], name="12-week average",
                                 mode="lines", line=dict(color=SAGE, width=1.5)))
    if "52-week trend" in overlays:
        fig.add_trace(go.Scatter(x=wk["date"], y=wk["trend"], name="52-week trend",
                                 mode="lines", line=dict(color=PLUM, width=1.5,
                                                         dash="dash")))
    if "Flagged holidays" in overlays:
        h = wk[wk["holiday"] == "yes"]
        fig.add_trace(go.Scatter(x=h["date"], y=h["sales"], name="Flagged holiday",
                                 mode="markers",
                                 marker=dict(color=BRICK, size=7, symbol="circle"),
                                 hovertemplate="%{x|%b %-d, %Y}<br>flagged holiday"
                                               "<br>$%{y:,.0f}<extra></extra>"))
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    show(fig)

    st.subheader("Two and a half years at a glance")
    cap("Every week as one cell, years stacked. Darker is a bigger week. Cells "
        "ringed in brick are the weeks the dataset flags as holidays — they do not "
        "line up with the dark ones.")
    cal = wk.copy()
    cal["year"] = cal["date"].dt.year
    cal["wk"] = cal["date"].dt.isocalendar().week.astype(int)
    years = sorted(cal["year"].unique())
    z = np.full((len(years), 53), np.nan)
    txt = [["" for _ in range(53)] for _ in years]
    for r in cal.itertuples():
        z[years.index(r.year), r.wk - 1] = r.sales
        txt[years.index(r.year)][r.wk - 1] = (
            f"{dstr(r.date)}<br>${r.sales:,.0f}<br>week {r.wk}"
            + ("<br>flagged holiday" if r.holiday == "yes" else ""))
    fig = base_fig(190, margin=dict(l=10, r=14, t=10, b=28))
    fig.add_trace(go.Heatmap(
        z=z, x=[f"{i + 1}" for i in range(53)], y=[str(y) for y in years],
        text=txt, hovertemplate="%{text}<extra></extra>",
        colorscale=[[0, "#EEF3F8"], [1, BLUE]], showscale=False, xgap=1.5, ygap=2))
    hol = cal[cal["holiday"] == "yes"]
    fig.add_trace(go.Scatter(
        x=[str(w) for w in hol["wk"]], y=[str(y) for y in hol["year"]],
        mode="markers", showlegend=False,
        marker=dict(symbol="square-open", size=13, color=BRICK, line=dict(width=2)),
        hoverinfo="skip"))
    fig.update_xaxes(title_text="calendar week", showgrid=False, linecolor=AXIS,
                     tickmode="array", tickvals=[str(w) for w in range(1, 53, 5)])
    fig.update_yaxes(showgrid=False, autorange="reversed")
    show(fig)

    st.subheader("What the data says")
    cap("Nine findings from the eight experiments, each with the number behind it "
        "and the decision it should change.")
    find = load("findings").sort_values("n")
    rows = [find.iloc[i:i + 3] for i in range(0, len(find), 3)]
    for chunk in rows:
        cols = st.columns(len(chunk))
        for col, r in zip(cols, chunk.itertuples()):
            col.markdown(
                f'<div class="wsi-find"><span class="wsi-tag">{r.tag}</span>'
                f'<div class="wsi-ft">{r.title}</div>'
                f'<div class="wsi-fm">{r.metric}</div>'
                f'<div class="wsi-fd">{r.detail}</div>'
                f'<div class="wsi-fa">{r.action}</div></div>',
                unsafe_allow_html=True)

# ============================================================ BUSINESS IMPACT
with tabs[1]:
    st.subheader("The holiday flag points at the wrong weeks")
    cap("The dataset marks four holidays as equal. Measured against a same-month "
        "baseline, only Thanksgiving earns its flag — and the week the chain "
        "actually peaks carries no flag at all.")
    hol = num(load("holidays"), "weeks_observed", "avg_chain_week",
              "baseline_week", "lift_abs", "lift_pct", "total_revenue")
    hol = hol.sort_values("lift_pct", ascending=False)
    a, b = st.columns([1, 1])
    with a:
        fig = base_fig(290, margin=dict(l=10, r=14, t=24, b=10))
        fig.add_trace(go.Bar(
            x=hol["holiday"], y=hol["lift_pct"],
            marker_color=[BLUE if v >= 0 else BRICK for v in hol["lift_pct"]],
            text=[f"{v:+.1f}%" for v in hol["lift_pct"]], textposition="outside",
            customdata=np.stack([hol["avg_chain_week"], hol["baseline_week"],
                                 hol["weeks_observed"]], axis=-1),
            hovertemplate="<b>%{x}</b><br>Lift %{y:+.1f}%<br>"
                          "Flagged week $%{customdata[0]:,.0f}<br>"
                          "Baseline $%{customdata[1]:,.0f}<br>"
                          "%{customdata[2]} weeks<extra></extra>"))
        fig.update_yaxes(ticksuffix="%")
        fig.add_hline(y=0, line=dict(color=AXIS, width=1))
        show(fig)
    with b:
        tw = num(load("top_weeks"), "week", "revenue", "vs_median_pct")
        disp = pd.DataFrame({
            "Week ending": [dstr(d) for d in pd.to_datetime(tw["date"])],
            "Wk": tw["week"],
            "Chain revenue": [f"${v:,.0f}" for v in tw["revenue"]],
            "vs median": [f"{v:+.0f}%" for v in tw["vs_median_pct"]],
            "Flagged": tw["flagged"],
        })
        st.dataframe(disp, hide_index=True, width="stretch", height=290)

    c = st.columns(4)
    c[0].metric("Average flagged week", kv("b_hol_week_rev"))
    c[1].metric("Average normal week", kv("b_normal_week_rev"))
    c[2].metric("Average December week", kv("b_december_week"),
                delta=kv("b_december_vs_year") + " vs average week")
    c[3].metric("Top-5 weeks flagged normal", kv("b_unflagged_top5"), help="of five")

    st.divider()
    st.subheader("Which departments actually ride the holiday")
    cap("Holiday lift for the strongest and weakest of the larger departments. Some "
        "more than double; others fall, because shoppers switch spend toward gifting.")
    dep = num(load("depts"), "dept", "revenue", "share_pct", "cum_pct", "avg",
              "cv", "stores", "hol_lift", "records", "growth_pct", "returns_value")
    big = dep[dep["revenue"] >= dep["revenue"].median()]

    def dept_bars(frame, field, label, n=9):
        d = frame.dropna(subset=[field]).sort_values(field, ascending=False)
        d = pd.concat([d.head(n), d.tail(n)]).drop_duplicates("dept")
        d = d.sort_values(field)
        fig = base_fig(max(300, 20 * len(d)), margin=dict(l=10, r=20, t=12, b=30))
        fig.add_trace(go.Bar(
            x=d[field], y=["D" + str(int(x)) for x in d["dept"]], orientation="h",
            marker_color=[BLUE if v >= 0 else BRICK for v in d[field]],
            customdata=d["revenue"],
            hovertemplate="<b>Dept %{y}</b><br>" + label +
                          " %{x:+.1f}%<br>Revenue $%{customdata:,.0f}<extra></extra>"))
        fig.add_vline(x=0, line=dict(color=AXIS, width=1))
        fig.update_xaxes(ticksuffix="%", showgrid=True, gridcolor=GRID)
        fig.update_yaxes(showgrid=False, type="category")
        return fig

    show(dept_bars(big, "hol_lift", "Holiday lift"))

    st.divider()
    st.subheader("A few departments carry the chain")
    cap("Departments ranked by revenue with the cumulative share running across. "
        f"**{kv('b_depts_for_80')}** of 81 departments produce 80% of revenue.")
    top = dep.sort_values("revenue", ascending=False).head(25)
    fig = base_fig(330, margin=dict(l=10, r=48, t=16, b=30), showlegend=True)
    fig.add_trace(go.Bar(x=["D" + str(int(d)) for d in top["dept"]],
                         y=top["revenue"], name="Revenue", marker_color=BLUE,
                         hovertemplate="<b>Dept %{x}</b><br>$%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=["D" + str(int(d)) for d in top["dept"]],
                             y=top["cum_pct"], name="Cumulative share", yaxis="y2",
                             mode="lines+markers", line=dict(color=PLUM, width=2),
                             marker=dict(size=5),
                             hovertemplate="%{y:.1f}% cumulative<extra></extra>"))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                                  range=[0, 100], showgrid=False,
                                  tickfont=dict(color=FADE)))
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    show(fig)

    a, b = st.columns([3, 2])
    with a:
        st.markdown("**Every department sized by revenue**")
        cap("Area and shade are both revenue. The 34 largest are drawn individually.")
        t34 = dep.sort_values("revenue", ascending=False).head(34)
        rest = dep.sort_values("revenue", ascending=False).iloc[34:]
        labels = ["D" + str(int(d)) for d in t34["dept"]]
        vals = list(t34["revenue"])
        shares = list(t34["share_pct"])
        if len(rest):
            labels.append(f"{len(rest)} smaller")
            vals.append(float(rest["revenue"].sum()))
            shares.append(float(rest["share_pct"].sum()))
        mx = max(vals)
        fig = base_fig(360, margin=dict(l=0, r=0, t=4, b=0))
        fig.add_trace(go.Treemap(
            labels=labels, parents=[""] * len(labels), values=vals,
            text=[f"{s:.1f}%" for s in shares], textinfo="label+text",
            marker=dict(colors=[f"rgba(47,109,158,{ramp(v / mx):.3f})" for v in vals],
                        line=dict(color="white", width=2)),
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>"
                          "%{text} of chain<extra></extra>",
            tiling=dict(pad=2)))
        show(fig)
    with b:
        st.markdown("**How concentrated is the revenue**")
        cap("Share of revenue held by the biggest stores and departments. The dashed "
            "diagonal is perfectly even spread; the further a curve bows above it, "
            "the more concentrated.")

        def curve(vals):
            v = np.sort(np.asarray(vals, dtype=float))[::-1]
            return (np.arange(1, len(v) + 1) / len(v) * 100,
                    np.cumsum(v) / v.sum() * 100)

        fig = base_fig(360, showlegend=True, margin=dict(l=10, r=14, t=24, b=34))
        for nm, vals, col in [("Stores", stores_df["total_rev"], BLUE),
                              ("Departments", dep["revenue"], PLUM)]:
            xs, ys = curve(vals)
            fig.add_trace(go.Scatter(x=xs, y=ys, name=nm, mode="lines",
                                     line=dict(color=col, width=2),
                                     hovertemplate="Top %{x:.0f}% hold "
                                                   "%{y:.1f}% of revenue<extra></extra>"))
        fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], name="Even spread",
                                 mode="lines",
                                 line=dict(color=AXIS, width=1, dash="dash"),
                                 hoverinfo="skip"))
        fig.update_xaxes(ticksuffix="%", title_text="share, largest first")
        fig.update_yaxes(ticksuffix="%")
        show(fig)

    st.markdown("**Growing and shrinking departments**")
    cap("2011 against 2010, larger departments only.")
    show(dept_bars(big, "growth_pct", "Growth"))

    with st.expander("All 81 departments"):
        q = st.text_input("Filter by department number", key="dq")
        d = dep if not q.strip() else dep[dep["dept"].astype(str).str.contains(q.strip())]
        st.dataframe(pd.DataFrame({
            "Dept": d["dept"].astype(int),
            "Revenue": [f"${v:,.0f}" for v in d["revenue"]],
            "Share": [f"{v:.2f}%" for v in d["share_pct"]],
            "Cumulative": [f"{v:.1f}%" for v in d["cum_pct"]],
            "Avg week": [f"${v:,.0f}" for v in d["avg"]],
            "Volatility": [f"{v:.2f}" for v in d["cv"]],
            "Stores": d["stores"].astype(int),
            "Holiday lift": [f"{v:+.0f}%" if pd.notna(v) else "—" for v in d["hol_lift"]],
            "Growth": [f"{v:+.0f}%" if pd.notna(v) else "—" for v in d["growth_pct"]],
        }).sort_values("Dept"), hide_index=True, width="stretch", height=380)

    st.divider()
    st.subheader("Month by month, start to finish")
    seas = num(load("seasonality"), "sort", "index", "value")
    ms = seas[seas["kind"] == "month_series"].sort_values("sort")
    mx = ms["value"].max()
    fig = base_fig(300, margin=dict(l=10, r=14, t=12, b=70))
    fig.add_trace(go.Bar(x=ms["label"], y=ms["value"],
                         marker_color=[BLUE if v > mx * 0.9 else MUTED
                                       for v in ms["value"]],
                         hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>"))
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    fig.update_xaxes(tickangle=-45)
    show(fig)

    st.subheader("Where each store makes its money")
    cap("Every store against the twenty largest departments, about two thirds of all "
        "revenue. Shade is that department's share of that store's **own** revenue, "
        "so a small store and a large one compare directly.")
    sd = num(load("store_dept"), "store", "dept", "revenue", "pct_of_store",
             "dept_rank")
    piv = sd.pivot_table(index="store", columns="dept", values="pct_of_store")
    order = (sd.sort_values("dept_rank")["dept"].drop_duplicates().tolist())
    piv = piv[order]
    fig = base_fig(max(360, 11 * len(piv)), margin=dict(l=10, r=14, t=10, b=34))
    fig.add_trace(go.Heatmap(
        z=piv.values, x=[str(int(c)) for c in piv.columns],
        y=[str(int(i)) for i in piv.index],
        colorscale=[[0, "#F2F6FA"], [1, BLUE]], xgap=1, ygap=1,
        colorbar=dict(title="% of store", thickness=10, len=0.5, outlinewidth=0),
        hovertemplate="Store %{y} · dept %{x}<br>%{z:.1f}% of that store"
                      "<extra></extra>"))
    fig.update_xaxes(title_text="department, largest first", showgrid=False,
                     type="category")
    fig.update_yaxes(title_text="store", showgrid=False, type="category",
                     autorange="reversed")
    show(fig)

    st.divider()
    st.subheader("Markdown depth, with the confound removed")
    cap("Markdowns are recorded only from November 2011, and in that window every "
        "record carries one, so **there is no zero-markdown control group**. The "
        "chart compares records; the figures beside it compare each store-dept with "
        "itself.")
    md = num(load("markdown"), "avg_sales", "records_or_total",
             "markdown_or_share", "vs_lightest_or_active", "corr_within_store")
    a, b = st.columns([3, 2])
    with a:
        view = st.radio("View", ["By depth", "By channel"], horizontal=True,
                        key="mdview")
        sub = md[md["kind"] == ("band" if view == "By depth" else "channel")]
        fig = base_fig(300, margin=dict(l=10, r=14, t=12, b=40))
        fig.add_trace(go.Bar(x=sub["label"], y=sub["avg_sales"], marker_color=BLUE,
                             customdata=np.stack([sub["markdown_or_share"],
                                                  sub["vs_lightest_or_active"]], -1),
                             hovertemplate="<b>%{x}</b><br>Avg sales $%{y:,.0f}"
                                           "<br>%{customdata[0]:,.0f}"
                                           "<br>%{customdata[1]:,.1f}<extra></extra>"))
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        show(fig)
    with b:
        st.markdown("**What a markdown dollar actually moves**")
        for lab, m in [("Recorded markdown spend", "b_md_spend"),
                       ("Sales per markdown dollar", "b_md_slope"),
                       ("Holding holiday constant", "b_md_slope_hol"),
                       ("Variance it explains", "b_md_r2"),
                       ("Attributable movement", "b_md_attributable")]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;"
                        f"font-size:.85rem;padding:3px 0;border-bottom:1px solid "
                        f"{GRID}'><span style='color:{FADE}'>{lab}</span>"
                        f"<b>{kv(m)}</b></div>", unsafe_allow_html=True)
        st.caption("The chart's spread is almost entirely store size. Read it as "
                   "where markdown money goes, never as its return.")

    st.divider()
    st.subheader("The economy barely registers")
    eb = num(load("econ_bands"), "sort", "avg", "n", "vs_first_pct")
    driver = st.radio("Driver", list(eb["driver"].unique()), horizontal=True,
                      key="econ")
    sub = eb[eb["driver"] == driver].sort_values("sort")
    fig = base_fig(300, margin=dict(l=10, r=14, t=26, b=30))
    fig.add_trace(go.Bar(x=sub["band"], y=sub["avg"], marker_color=BLUE,
                         text=[f"{v:+.1f}%" for v in sub["vs_first_pct"]],
                         textposition="outside", customdata=sub["n"],
                         hovertemplate="<b>%{x}</b><br>Avg store-week $%{y:,.0f}"
                                       "<br>%{customdata:,.0f} store-weeks<extra></extra>"))
    fig.update_yaxes(tickprefix="$", tickformat="~s",
                     range=[sub["avg"].min() * 0.9, sub["avg"].max() * 1.06])
    show(fig)

    st.divider()
    st.subheader("Where the headroom is")
    cap("Every store below the top-quartile benchmark for revenue per square foot, "
        "and what closing that gap would be worth. This is a **ceiling, not a plan**: "
        "catchment and location cap what any single store can reach.")
    c = st.columns(6)
    c[0].metric("Benchmark $/sq ft", kv("b_topq_rps"))
    c[1].metric("Stores below it", kv("b_underperformers"), help="of 45")
    c[2].metric("Headroom", kv("b_opportunity"),
                delta=kv("b_opportunity_pct") + " of revenue", delta_color="off")
    c[3].metric("Top 10 stores", kv("b_top10_store_share"), help="of all revenue")
    c[4].metric("Largest / smallest", kv("b_spread_ratio"), help="by total revenue")
    c[5].metric("Net returns", kv("b_returns_pct"), help="of revenue")
    gap = stores_df[stores_df["gap_to_benchmark"] > 0].nlargest(12, "gap_to_benchmark")
    gap = gap.sort_values("gap_to_benchmark")
    fig = base_fig(330, margin=dict(l=10, r=20, t=12, b=30))
    fig.add_trace(go.Bar(
        x=gap["gap_to_benchmark"], y=["Store " + str(int(s)) for s in gap["store"]],
        orientation="h", marker_color=BLUE,
        customdata=np.stack([gap["rev_per_sqft"], gap["size"], gap["type"]], -1),
        hovertemplate="<b>%{y}</b> (Type %{customdata[2]})<br>"
                      "At benchmark $%{x:,.0f}<br>"
                      "Current $%{customdata[0]:,.0f}/sq ft<br>"
                      "%{customdata[1]:,.0f} sq ft<extra></extra>"))
    fig.update_xaxes(tickprefix="$", tickformat="~s", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(showgrid=False, type="category")
    show(fig)

# ====================================================================== STORES
with tabs[2]:
    sw = num(load("store_week"), "store", "revenue")
    sw["date"] = pd.to_datetime(sw["date"])
    st.subheader("All 45 stores, same scale")
    cap("One panel per store, every panel on the same vertical scale so the sizes "
        "are honest. The label is the store number and its format.")
    ids = sorted(sw["store"].unique())
    ncol, ymax = 9, sw["revenue"].max()
    nrow = int(np.ceil(len(ids) / ncol))
    types = stores_df.set_index("store")["type"].to_dict()
    fig = make_subplots(rows=nrow, cols=ncol, shared_yaxes=True,
                        vertical_spacing=0.06, horizontal_spacing=0.004,
                        subplot_titles=[f"{int(s)}{types.get(s, '')}" for s in ids])
    for i, s in enumerate(ids):
        d = sw[sw["store"] == s].sort_values("date")
        on = FMT is None or types.get(s) == FMT
        col = BLUE if on else MUTED
        fig.add_trace(go.Scatter(
            x=d["date"], y=d["revenue"], mode="lines", showlegend=False,
            line=dict(color=col, width=1.8 if s == SEL else 0.9),
            fill="tozeroy",
            fillcolor=f"rgba(47,109,158,{0.16 if on else 0.05})",
            name=f"Store {int(s)}",
            hovertemplate=f"<b>Store {int(s)}{types.get(s, '')}</b><br>"
                          "%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>"),
            row=i // ncol + 1, col=i % ncol + 1)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, range=[0, ymax])
    fig.update_layout(height=115 * nrow, margin=dict(l=4, r=4, t=18, b=4),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(size=11, color=INK),
                      hoverlabel=dict(bgcolor="white", bordercolor=AXIS))
    for ann, sid in zip(fig.layout.annotations, ids):
        ann.font.size = 10
        ann.font.color = INK if (FMT is None or types.get(sid) == FMT) else FADE
    show(fig)

    st.subheader("Store scorecard")
    cap("All 45 stores. Sort any column by clicking its header.")
    sc = stores_df if FMT is None else stores_df[stores_df["type"] == FMT]
    st.dataframe(pd.DataFrame({
        "Store": sc["store"].astype(int), "Format": sc["type"],
        "Cluster": sc["cluster"], "Size": sc["size"].astype(int),
        "Revenue": sc["total_rev"], "Avg week": sc["avg_weekly"],
        "$/sq ft": sc["rev_per_sqft"], "Volatility": sc["cv"],
        "Holiday lift %": sc["hol_lift"], "Growth %": sc["growth_pct"],
        "Unemp %": sc["unemployment"], "Gap to benchmark": sc["gap_to_benchmark"],
    }).sort_values("Revenue", ascending=False), hide_index=True,
        width="stretch", height=420,
        column_config={
            "Revenue": st.column_config.ProgressColumn(
                "Revenue", format="$%.0f", min_value=0,
                max_value=float(stores_df["total_rev"].max())),
            "Avg week": st.column_config.NumberColumn(format="$%.0f"),
            "$/sq ft": st.column_config.NumberColumn(format="$%.0f"),
            "Size": st.column_config.NumberColumn(format="%d"),
            "Volatility": st.column_config.NumberColumn(format="%.3f"),
            "Holiday lift %": st.column_config.NumberColumn(format="%.1f"),
            "Growth %": st.column_config.NumberColumn(format="%.1f"),
            "Unemp %": st.column_config.NumberColumn(format="%.2f"),
            "Gap to benchmark": st.column_config.NumberColumn(format="$%.0f"),
        })

    st.divider()
    st.subheader("Four store archetypes")
    cap("K-means on six behavioural features, projected onto its two principal "
        f"components. Silhouette is **{kv('e4_silhouette')}** — the archetypes are "
        "real but they overlap.")
    seg = num(load("segments"), "stores", "revenue", "rev_share_pct", "avg_size",
              "rev_per_sqft", "avg_weekly_per_store", "cv", "hol_lift", "cpi",
              "unemployment", "box_lo", "box_q1", "box_median", "box_q3", "box_hi")
    clusters = seg[seg["kind"] == "cluster"]
    cmap = {n: SERIES[i] for i, n in enumerate(clusters["group"])}
    a, b = st.columns(2)
    with a:
        fig = base_fig(360, showlegend=True, margin=dict(l=10, r=14, t=30, b=30))
        for nm, grp in stores_df.groupby("cluster"):
            on = FMT is None
            fig.add_trace(go.Scatter(
                x=grp["pca_x"], y=grp["pca_y"], mode="markers", name=nm,
                marker=dict(size=np.sqrt(grp["size"] / 1000) * 3.2,
                            color=cmap.get(nm, BLUE), opacity=0.72,
                            line=dict(width=2 if SEL in set(grp["store"]) else 0,
                                      color=INK)),
                customdata=np.stack([grp["store"].astype(int), grp["type"],
                                     grp["avg_weekly"], grp["size"]], -1),
                hovertemplate="<b>Store %{customdata[0]}</b> (Type %{customdata[1]})"
                              "<br>Avg week $%{customdata[2]:,.0f}"
                              "<br>%{customdata[3]:,.0f} sq ft<extra></extra>"))
        fig.update_xaxes(title_text="principal component 1", showgrid=True,
                         gridcolor=GRID)
        fig.update_yaxes(title_text="principal component 2")
        show(fig)
    with b:
        el = num(load("curves"), "x", "y", "y2")
        el = el[el["series"] == "elbow"].sort_values("x")
        fig = base_fig(360, showlegend=True, margin=dict(l=10, r=48, t=30, b=30))
        fig.add_trace(go.Scatter(x=el["x"], y=el["y"], name="Inertia",
                                 mode="lines+markers", line=dict(color=BLUE, width=2),
                                 hovertemplate="k=%{x}<br>inertia %{y:,.0f}<extra></extra>"))
        sil = el.dropna(subset=["y2"])
        fig.add_trace(go.Scatter(x=sil["x"], y=sil["y2"], name="Silhouette",
                                 yaxis="y2", mode="lines+markers",
                                 line=dict(color=PLUM, width=2),
                                 hovertemplate="k=%{x}<br>silhouette %{y:.3f}<extra></extra>"))
        fig.add_vline(x=4, line=dict(color=AXIS, dash="dash", width=1),
                      annotation_text="k = 4", annotation_font_color=FADE)
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                      tickfont=dict(color=FADE)))
        fig.update_xaxes(title_text="clusters (k)", dtick=1)
        show(fig)

    st.markdown("**The four archetypes across every feature**")
    cap("Each line is one archetype traced across the six clustering features. "
        "Where lines cross, the ranking reverses.")
    AX = [("avg_weekly_per_store", "Weekly revenue"), ("avg_size", "Floor space"),
          ("rev_per_sqft", "$ / sq ft"), ("cv", "Volatility"),
          ("hol_lift", "Holiday lift"), ("unemployment", "Unemployment")]
    fig = base_fig(330, showlegend=True, margin=dict(l=40, r=40, t=46, b=20))
    for i, r in enumerate(clusters.itertuples()):
        fig.add_trace(go.Scatter(
            x=[lab for _, lab in AX],
            y=[(getattr(r, k) - clusters[k].min()) /
               max(1e-9, clusters[k].max() - clusters[k].min()) for k, _ in AX],
            name=r.group, mode="lines+markers",
            line=dict(color=SERIES[i], width=2.4), marker=dict(size=7),
            customdata=[getattr(r, k) for k, _ in AX],
            hovertemplate="<b>" + r.group + "</b><br>%{x}: %{customdata:,.2f}"
                          "<extra></extra>"))
    fig.update_yaxes(title_text="relative position", showticklabels=False,
                     range=[-0.1, 1.1])
    show(fig)
    st.dataframe(pd.DataFrame({
        "Archetype": clusters["group"], "Stores": clusters["stores"].astype(int),
        "Avg week": [f"${v:,.0f}" for v in clusters["avg_weekly_per_store"]],
        "Avg size": [f"{v:,.0f}" for v in clusters["avg_size"]],
        "$/sq ft": [f"${v:,.0f}" for v in clusters["rev_per_sqft"]],
        "Volatility": [f"{v:.3f}" for v in clusters["cv"]],
        "Holiday lift": [f"{v:+.1f}%" for v in clusters["hol_lift"]],
        "Revenue share": [f"{v:.1f}%" for v in clusters["rev_share_pct"]],
    }), hide_index=True, width="stretch")

    st.divider()
    st.subheader("Size against productivity")
    cap("Bubble area is total revenue, colour is format. If bigger stores were more "
        "productive the cloud would slope **up**; it slopes down.")
    TC = {"A": BLUE, "B": OCHRE, "C": SAGE}
    a, b = st.columns(2)

    def bubbles(xcol, ycol, xlab, ylab, hline=None, xfmt="~s", yfmt=",.0f",
                xpre="", ypre="$"):
        fig = base_fig(340, showlegend=True, margin=dict(l=10, r=14, t=30, b=40))
        for t, grp in stores_df.groupby("type"):
            on = FMT is None or t == FMT
            fig.add_trace(go.Scatter(
                x=grp[xcol], y=grp[ycol], mode="markers", name=f"Type {t}",
                marker=dict(size=np.sqrt(grp["total_rev"] / 1e6) * 1.5,
                            color=TC[t] if on else MUTED, opacity=0.62 if on else 0.2,
                            line=dict(width=2 if SEL in set(grp["store"]) else 0,
                                      color=INK)),
                customdata=np.stack([grp["store"].astype(int), grp["total_rev"]], -1),
                hovertemplate=f"<b>Store %{{customdata[0]}}</b> (Type {t})<br>"
                              f"{xlab} %{{x:,.0f}}<br>{ylab} %{{y:,.0f}}<br>"
                              "Total revenue $%{customdata[1]:,.0f}<extra></extra>"))
        if hline is not None and np.isfinite(hline):
            fig.add_hline(y=hline, line=dict(color=AXIS, dash="dash", width=1),
                          annotation_text="top-quartile benchmark",
                          annotation_font_color=FADE, annotation_font_size=10)
        fig.update_xaxes(title_text=xlab, tickformat=xfmt, tickprefix=xpre)
        fig.update_yaxes(title_text=ylab, tickformat=yfmt, tickprefix=ypre)
        return fig

    with a:
        show(bubbles("size", "rev_per_sqft", "Floor space (sq ft)",
                     "Revenue per sq ft", hline=kraw("b_topq_rps")))
    with b:
        show(bubbles("avg_weekly", "cv", "Average weekly revenue", "Volatility",
                     xfmt="~s", yfmt=".2f", xpre="$", ypre=""))

    st.subheader("Spread of store-week revenue by format")
    fmts = seg[seg["kind"] == "format"]
    fig = base_fig(300, margin=dict(l=10, r=14, t=16, b=30))
    for i, r in enumerate(fmts.itertuples()):
        fig.add_trace(go.Box(
            name=r.group, q1=[r.box_q1], median=[r.box_median], q3=[r.box_q3],
            lowerfence=[r.box_lo], upperfence=[r.box_hi], showlegend=False,
            marker_color=SERIES[i], fillcolor=f"rgba(47,109,158,0.0)",
            line=dict(color=SERIES[i], width=2)))
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    show(fig)

# ================================================================== STATISTICS
with tabs[3]:
    cur = num(load("curves"), "x", "y", "y2")

    def series(name):
        return cur[cur["series"] == name].sort_values("x")

    st.subheader("Experiment 1 — Descriptive statistics")
    cap("Quartiles and Tukey fences on every store-dept-week record. The outliers "
        "are not errors: they are the weeks the business lives on.")
    c = st.columns(6)
    c[0].metric("Q1", kv("e1_q1"))
    c[1].metric("Median", kv("e1_q2"))
    c[2].metric("Q3", kv("e1_q3"))
    c[3].metric("IQR", kv("e1_iqr"))
    c[4].metric("Upper fence", kv("e1_fence_hi"))
    c[5].metric("Outliers", kv("e1_outlier_pct"),
                delta=kv("e1_outlier_revenue_pct") + " of revenue", delta_color="off")
    h = series("sales_hist")
    fig = base_fig(300, margin=dict(l=10, r=14, t=16, b=34))
    fig.add_trace(go.Bar(x=h["x"], y=h["y"], marker_color=BLUE, marker_line_width=0,
                         hovertemplate="around $%{x:,.0f}<br>%{y:,.0f} records"
                                       "<extra></extra>"))
    fig.add_vline(x=kraw("e1_fence_hi"), line=dict(color=BRICK, dash="dash", width=1),
                  annotation_text="upper fence", annotation_font_color=FADE,
                  annotation_font_size=10)
    fig.update_xaxes(title_text="weekly sales per store-dept", tickprefix="$",
                     tickformat="~s")
    fig.update_yaxes(title_text="records", tickformat="~s")
    show(fig)

    st.divider()
    st.subheader("Experiment 2 — Linear regression")
    cap("Three specifications on the same target. Economic indicators alone explain "
        "essentially nothing; floor space explains most of what can be explained.")
    c = st.columns(4)
    c[0].metric("Economic drivers only", kv("e2_economic_r2"), help="R², store-dept-week")
    c[1].metric("Adding size and holiday", kv("e2_full_r2"), help="R², store-dept-week")
    c[2].metric("Aggregated to store-week", kv("e2_store_week_r2"), help="R²")
    c[3].metric("Store-week RMSE", kv("e2_store_week_rmse"))
    mdl = num(load("model"), "coef", "se", "t", "p", "r2")
    a, b = st.columns(2)
    with a:
        st.markdown("**Predicted against actual**")
        cap("Store-week model, 1,200 sampled weeks. The dashed diagonal is a "
            "perfect prediction.")
        sc = series("fit_scatter")
        lo = float(min(sc["x"].min(), sc["y"].min()))
        hi = float(max(sc["x"].max(), sc["y"].max()))
        fig = base_fig(330, margin=dict(l=10, r=14, t=16, b=40))
        fig.add_trace(go.Scatter(x=sc["x"], y=sc["y"], mode="markers",
                                 marker=dict(color=BLUE, size=4, opacity=0.4),
                                 hovertemplate="predicted $%{x:,.0f}<br>"
                                               "actual $%{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                                 line=dict(color=AXIS, dash="dash", width=1),
                                 hoverinfo="skip"))
        fig.update_xaxes(title_text="predicted", tickprefix="$", tickformat="~s")
        fig.update_yaxes(title_text="actual", tickprefix="$", tickformat="~s")
        show(fig)
    with b:
        st.markdown("**Coefficients, store-week model**")
        cap("Dollars of weekly revenue per one unit of the driver. Size dominates.")
        NAME = {"Size": "Floor space (per sq ft)", "Temperature": "Temperature (°F)",
                "Fuel_Price": "Fuel price (per $)", "CPI": "CPI (per point)",
                "Unemployment": "Unemployment (per point)",
                "IsHolidayNum": "Flagged holiday week",
                "TotalMarkDown": "Markdown (per $)"}
        sub = mdl[mdl["model"] == "store_week"].copy()
        sub["abs"] = sub["coef"].abs()
        sub = sub.sort_values("abs", ascending=False)
        st.dataframe(pd.DataFrame({
            "Driver": [NAME.get(f, f) for f in sub["feature"]],
            "Per unit": [f"${v:,.2f}" for v in sub["coef"]],
        }), hide_index=True, width="stretch", height=290)

    a, b = st.columns(2)
    with a:
        st.markdown("**Where the model is wrong**")
        cap("Residuals of the store-week model: centred and roughly symmetric, "
            "which is what a well-specified linear model gives — but wide.")
        rh = series("resid_hist")
        fig = base_fig(290, margin=dict(l=10, r=14, t=16, b=34))
        fig.add_trace(go.Bar(x=rh["x"], y=rh["y"], marker_color=BLUE,
                             marker_line_width=0,
                             hovertemplate="residual near $%{x:,.0f}<br>"
                                           "%{y:,.0f} store-weeks<extra></extra>"))
        fig.add_vline(x=0, line=dict(color=AXIS, dash="dash", width=1))
        fig.update_xaxes(tickprefix="$", tickformat="~s", title_text="residual")
        fig.update_yaxes(tickformat="~s")
        show(fig)
    with b:
        st.markdown("**Impact of a one-standard-deviation move**")
        cap("What a typical swing in each economic driver is worth to a store's "
            "weekly revenue.")
        el = mdl[mdl["model"] == "elasticity"].copy()
        el["abs"] = el["coef"].abs()
        el = el.sort_values("abs")
        fig = base_fig(290, margin=dict(l=10, r=20, t=16, b=34))
        fig.add_trace(go.Bar(
            x=el["coef"], y=[f.replace("_", " ") for f in el["feature"]],
            orientation="h",
            marker_color=[BLUE if v >= 0 else BRICK for v in el["coef"]],
            customdata=el["r2"],
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f} per 1 sd<br>"
                          "%{customdata:+.2f}% of a week<extra></extra>"))
        fig.add_vline(x=0, line=dict(color=AXIS, width=1))
        fig.update_xaxes(tickprefix="$", tickformat="~s", showgrid=True,
                         gridcolor=GRID)
        fig.update_yaxes(showgrid=False, type="category")
        show(fig)

    st.divider()
    st.subheader("Experiment 3 — Sampling")
    samp = num(load("sampling"), "n", "mean", "std", "median", "se", "ci_lo",
               "ci_hi", "err_pct")
    a, b = st.columns(2)
    with a:
        st.markdown("**How fast a sample converges**")
        cap(f"Error against the true population mean of **{kv('e3_pop_mean')}** as "
            "the sample grows, on a log scale.")
        sr = samp[samp["method"] == "simple random"].sort_values("n")
        fig = base_fig(300, margin=dict(l=10, r=14, t=16, b=40))
        fig.add_trace(go.Scatter(x=sr["n"], y=sr["err_pct"], mode="lines+markers",
                                 line=dict(color=BLUE, width=2), marker=dict(size=8),
                                 customdata=sr["mean"],
                                 hovertemplate="%{x:,.0f} records<br>"
                                               "error %{y:.3f}%<br>"
                                               "mean $%{customdata:,.0f}<extra></extra>"))
        fig.update_xaxes(type="log", title_text="sample size (log scale)")
        fig.update_yaxes(ticksuffix="%", title_text="error vs population")
        show(fig)
        st.dataframe(pd.DataFrame({
            "Sample": samp["label"], "Method": samp["method"],
            "Mean": [f"${v:,.0f}" for v in samp["mean"]],
            "Std error": [f"${v:,.0f}" if pd.notna(v) else "—" for v in samp["se"]],
            "Error": [f"{v:.3f}%" for v in samp["err_pct"]],
        }), hide_index=True, width="stretch", height=260)
    with b:
        st.markdown("**The central limit theorem, demonstrated**")
        cap("1,000 repeated samples of 500 records each. Their means are close to "
            "normal even though the underlying sales are strongly skewed.")
        clt = series("clt_hist")
        fig = base_fig(300, margin=dict(l=10, r=14, t=16, b=40))
        fig.add_trace(go.Bar(x=clt["x"], y=clt["y"], marker_color=BLUE,
                             marker_line_width=0,
                             hovertemplate="mean near $%{x:,.0f}<br>%{y:,.0f} samples"
                                           "<extra></extra>"))
        fig.update_xaxes(title_text="sample mean", tickprefix="$", tickformat="~s")
        fig.update_yaxes(title_text="samples")
        show(fig)
        c = st.columns(2)
        c[0].metric("Observed spread", kv("e3_clt_std"))
        c[1].metric("Theory predicts", kv("e3_clt_se"))

    st.divider()
    st.subheader("Experiment 5 — Weekly sales as a random variable")
    a, b = st.columns(2)
    with a:
        pv = st.radio("View", ["Density", "Cumulative"], horizontal=True, key="pdv")
        d = series("pdf" if pv == "Density" else "cdf")
        fig = base_fig(300, margin=dict(l=10, r=14, t=16, b=40))
        fig.add_trace(go.Scatter(x=d["x"], y=d["y"], mode="lines",
                                 line=dict(color=BLUE, width=2), fill="tozeroy",
                                 fillcolor="rgba(47,109,158,0.12)",
                                 hovertemplate="$%{x:,.0f}<br>%{y:.4g}<extra></extra>"))
        fig.update_xaxes(title_text="weekly sales", tickprefix="$", tickformat="~s")
        if pv == "Cumulative":
            fig.update_yaxes(tickformat=".0%", title_text="share at or below")
        else:
            fig.update_yaxes(tickformat=".1e", title_text="density")
        show(fig)
        c = st.columns(3)
        c[0].metric("Expected value", kv("e5_mean"))
        c[1].metric("Std deviation", kv("e5_std"))
        c[2].metric("Coef. of variation", kv("e5_cv"))
    with b:
        st.markdown("**The percentile ladder**")
        cap("The jump from the 95th to the 99th percentile is larger than the whole "
            "distance from the 1st to the 75th — the heavy tail stated plainly.")
        pct = [(int(m[4:]), float(v[0])) for m, v in K.items()
               if m.startswith("e5_p") and m[4:].isdigit()]
        pct.sort()
        mxp = max(v for _, v in pct)
        fig = base_fig(300, margin=dict(l=10, r=30, t=16, b=34))
        fig.add_trace(go.Bar(
            x=[v for _, v in pct], y=[f"{p}th" for p, _ in pct], orientation="h",
            marker=dict(color=[f"rgba(47,109,158,{ramp(v / mxp):.3f})"
                               for _, v in pct]),
            text=[f"${v:,.0f}" for _, v in pct], textposition="outside",
            hovertemplate="<b>%{y} percentile</b><br>$%{x:,.0f}<extra></extra>"))
        fig.update_xaxes(tickprefix="$", tickformat="~s", showgrid=True,
                         gridcolor=GRID)
        fig.update_yaxes(showgrid=False, type="category")
        show(fig)

    exc = series("exceedance")
    st.markdown("**Probability of clearing a threshold**")
    st.dataframe(pd.DataFrame({
        "Threshold": [f"${v:,.0f}" for v in exc["x"]],
        "P(sales above)": [f"{v:.3f}" for v in exc["y"]],
        "Share of revenue above": [f"{v:.2f}%" for v in exc["y2"]],
    }), hide_index=True, width="stretch")

    st.divider()
    st.subheader("Experiment 6 — Which distribution fits")
    cap("Weekly sales are strongly right-skewed with heavy tails, so the normal "
        "distribution is rejected outright. Log-normal is much closer.")
    c = st.columns(4)
    c[0].metric("Skewness", kv("e6_skew"))
    c[1].metric("Excess kurtosis", kv("e6_kurtosis"))
    c[2].metric("Skew after log", kv("e6_log_skew"),
                help="overshoots into mild left skew")
    c[3].metric("Chain weekly total", kv("e6_shapiro_p"),
                help="Shapiro-Wilk p — aggregation restores normality")
    a, b = st.columns(2)
    with a:
        st.markdown("**Empirical density against two fits**")
        cap("The normal fit puts mass below zero and misses the peak; log-normal "
            "tracks the real shape.")
        fig = base_fig(320, showlegend=True, margin=dict(l=10, r=14, t=30, b=40))
        for nm, s, col, w in [("Observed", "empirical_density", BLUE, 2.2),
                              ("Log-normal fit", "lognormal_density", PLUM, 1.8),
                              ("Normal fit", "normal_density", MUTED, 1.8)]:
            d = series(s)
            fig.add_trace(go.Scatter(x=d["x"], y=d["y"], name=nm, mode="lines",
                                     line=dict(color=col, width=w),
                                     hovertemplate="$%{x:,.0f}<br>%{y:.3e}<extra></extra>"))
        fig.update_xaxes(tickprefix="$", tickformat="~s", title_text="weekly sales")
        fig.update_yaxes(tickformat=".1e", title_text="density")
        show(fig)
    with b:
        st.markdown("**Normal Q-Q plot**")
        cap("Points leave the diagonal at both ends, which is the heavy tail.")
        qq = series("qq")
        lo = float(min(qq["x"].min(), qq["y"].min()))
        hi = float(max(qq["x"].max(), qq["y"].max()))
        fig = base_fig(320, margin=dict(l=10, r=14, t=30, b=40))
        fig.add_trace(go.Scatter(x=qq["x"], y=qq["y"], mode="markers",
                                 marker=dict(color=BLUE, size=5, opacity=0.65),
                                 hovertemplate="normal $%{x:,.0f}<br>"
                                               "observed $%{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                                 line=dict(color=AXIS, dash="dash", width=1),
                                 hoverinfo="skip"))
        fig.update_xaxes(title_text="normal quantile", tickprefix="$", tickformat="~s")
        fig.update_yaxes(title_text="observed quantile", tickprefix="$",
                         tickformat="~s")
        show(fig)
    fits = num(load("dist_fits"), "ks_stat", "ks_p").sort_values("ks_stat")
    st.dataframe(pd.DataFrame({
        "Distribution": fits["name"], "Fitted parameters": fits["params"],
        "KS statistic": [f"{v:.4f}" for v in fits["ks_stat"]],
        "p-value": ["< 0.0001" if v < 1e-4 else f"{v:.4f}" for v in fits["ks_p"]],
        "Note": fits["note"].fillna(""),
    }), hide_index=True, width="stretch")

    st.divider()
    st.subheader("Experiment 7 — Statistical inference")
    cap("With 421,570 records almost any difference reaches significance, so effect "
        "size matters more than the p-value. The holiday difference is real and "
        "small; the format difference is real and large.")
    a, b = st.columns(2)
    with a:
        st.markdown("**Holiday against normal weeks**")
        for lab, m in [("Mean, flagged holiday weeks", "e7_hol_mean"),
                       ("Mean, normal weeks", "e7_non_mean"),
                       ("Difference", "e7_hol_diff"), ("Lift", "e7_hol_lift"),
                       ("t statistic", "e7_hol_t"), ("p-value", "e7_hol_p"),
                       ("Cohen's d", "e7_hol_d"),
                       ("Mann-Whitney p", "e7_hol_mw_p")]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;"
                        f"font-size:.85rem;padding:3px 0;border-bottom:1px solid "
                        f"{GRID}'><span style='color:{FADE}'>{lab}</span>"
                        f"<b>{kv(m)}</b></div>", unsafe_allow_html=True)
        st.caption("Significant, but Cohen's d near 0.05 is a very small effect. The "
                   "chain-level holiday story lives in two specific weeks, not in "
                   "the flag.")
    with b:
        st.markdown("**Across the formats, and the mean itself**")
        for lab, m in [("ANOVA F", "e7_anova_f"), ("ANOVA p", "e7_anova_p"),
                       ("Kruskal-Wallis p", "e7_kruskal_p"),
                       ("Chi-square, markdown × holiday", "e7_chi2"),
                       ("Estimated mean", "e7_mean"),
                       ("Standard error", "e7_se"),
                       ("95% interval, lower", "e7_ci95_lo"),
                       ("95% interval, upper", "e7_ci95_hi")]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;"
                        f"font-size:.85rem;padding:3px 0;border-bottom:1px solid "
                        f"{GRID}'><span style='color:{FADE}'>{lab}</span>"
                        f"<b>{kv(m)}</b></div>", unsafe_allow_html=True)

    st.markdown("**Correlation matrix**")
    cap("Blue is positive, brick negative. Switch between individual records and "
        "store-week totals — aggregating reveals the size effect that record-level "
        "noise hides.")
    corr = num(load("correlation"), "r")
    lvl = st.radio("Level", ["Store-week totals", "Store-dept-week records"],
                   horizontal=True, key="corrlvl")
    sub = corr[corr["level"] == ("store_week" if lvl.startswith("Store-week")
                                 else "record")]
    piv = sub.pivot(index="var1", columns="var2", values="r")
    order = [v for v in ["Weekly_Sales", "Size", "Temperature", "Fuel_Price",
                         "CPI", "Unemployment", "TotalMarkDown"] if v in piv.index]
    piv = piv.loc[order, order]
    SHORT = {"Weekly_Sales": "Sales", "Temperature": "Temp", "Fuel_Price": "Fuel",
             "Unemployment": "Unemp", "TotalMarkDown": "Markdown"}
    lbl = [SHORT.get(v, v) for v in order]
    fig = base_fig(420, margin=dict(l=10, r=14, t=16, b=10))
    fig.add_trace(go.Heatmap(
        z=piv.values, x=lbl, y=lbl, zmid=0,
        colorscale=[[0, BRICK], [0.5, "#F5F7F9"], [1, BLUE]], zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in piv.values],
        texttemplate="%{text}", textfont=dict(size=11),
        xgap=2, ygap=2,
        colorbar=dict(thickness=10, len=0.6, outlinewidth=0),
        hovertemplate="%{y} / %{x}<br>r = %{z:+.3f}<extra></extra>"))
    fig.update_xaxes(showgrid=False, side="top")
    fig.update_yaxes(showgrid=False, autorange="reversed")
    show(fig)

# ==================================================================== FORECAST
with tabs[4]:
    wkf = num(load("weekly"), "sales", "ma4", "ma12", "trend", "seasonal", "resid")
    wkf["date"] = pd.to_datetime(wkf["date"])
    st.subheader("Experiment 8 — Taking the series apart")
    cap("Classical multiplicative decomposition with a 52-week period. The trend is "
        f"nearly flat (**{kv('e8_trend_slope')}** per week on a "
        f"**{kv('avg_weekly_chain')}** base), which means almost everything in the "
        "raw series is the calendar.")
    comp = st.radio("Component", ["Observed", "Trend", "Seasonal", "Residual"],
                    horizontal=True, key="decomp")
    col = {"Observed": "sales", "Trend": "trend", "Seasonal": "seasonal",
           "Residual": "resid"}[comp]
    d = wkf.dropna(subset=[col])
    idx = comp in ("Seasonal", "Residual")
    fig = base_fig(320, margin=dict(l=10, r=14, t=16, b=30))
    fig.add_trace(go.Scatter(x=d["date"], y=d[col], mode="lines",
                             line=dict(color=BLUE, width=2),
                             hovertemplate="%{x|%b %-d, %Y}<br>" +
                                           ("%{y:.3f}" if idx else "$%{y:,.0f}") +
                                           "<extra></extra>"))
    if idx:
        fig.add_hline(y=1, line=dict(color=AXIS, dash="dash", width=1))
    else:
        fig.update_yaxes(tickprefix="$", tickformat="~s")
    show(fig)

    st.subheader("The shape of the year")
    cap("Seasonal index by calendar week: 1.00 is an average week. Two weeks carry "
        "the year.")
    seas2 = num(load("seasonality"), "sort", "index", "value")
    sv = st.radio("Grain", ["By week", "By month"], horizontal=True, key="seas")
    if sv == "By week":
        s = seas2[seas2["kind"] == "week"].sort_values("sort")
        yv, lab = s["index"], [f"wk {int(v)}" for v in s["sort"]]
    else:
        s = seas2[seas2["kind"] == "month"].sort_values("sort")
        yv, lab = s["index"] / 100, list(s["label"])
    fig = base_fig(310, margin=dict(l=10, r=14, t=16, b=40))
    fig.add_trace(go.Bar(x=lab, y=yv,
                         marker_color=[BLUE if v >= 1.15 else BRICK if v <= 0.9
                                       else MUTED for v in yv],
                         hovertemplate="<b>%{x}</b><br>index %{y:.3f}<extra></extra>"))
    fig.add_hline(y=1, line=dict(color=AXIS, dash="dash", width=1))
    fig.update_yaxes(title_text="seasonal index")
    show(fig)

    st.subheader("Fourteen weeks ahead")
    cap("Trend projected forward and multiplied by each target week's seasonal "
        "index, with a 95% band from the decomposition residuals. Total forecast "
        f"over the next fourteen weeks is **{kv('e8_forecast_total')}**.")
    fc = num(load("forecast"), "week", "value", "lo", "hi", "predicted")
    fc["date"] = pd.to_datetime(fc["date"])
    fut = fc[fc["kind"] == "forecast"].sort_values("date")
    hist = wkf.tail(60)
    band = st.checkbox("Show 95% band", value=True, key="fcband")
    fig = base_fig(340, showlegend=True, margin=dict(l=10, r=14, t=30, b=30))
    join = pd.DataFrame({"date": [hist["date"].iloc[-1]],
                         "value": [hist["sales"].iloc[-1]],
                         "lo": [hist["sales"].iloc[-1]],
                         "hi": [hist["sales"].iloc[-1]]})
    fl = pd.concat([join, fut[["date", "value", "lo", "hi"]]], ignore_index=True)
    if band:
        fig.add_trace(go.Scatter(
            x=list(fl["date"]) + list(fl["date"])[::-1],
            y=list(fl["hi"]) + list(fl["lo"])[::-1], fill="toself",
            fillcolor="rgba(47,109,158,0.14)", line=dict(width=0),
            name="95% band", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=hist["date"], y=hist["sales"], name="Actual",
                             mode="lines", line=dict(color=BLUE, width=2),
                             hovertemplate="%{x|%b %-d, %Y}<br>$%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=fl["date"], y=fl["value"], name="Forecast",
                             mode="lines",
                             line=dict(color=BLUE, width=2, dash="dash"),
                             hovertemplate="%{x|%b %-d, %Y}<br>forecast $%{y:,.0f}"
                                           "<extra></extra>"))
    fig.add_vline(x=hist["date"].iloc[-1], line=dict(color=AXIS, dash="dot", width=1),
                  annotation_text="forecast →", annotation_font_color=FADE,
                  annotation_font_size=10)
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    show(fig)

    st.subheader("Does the model actually work")
    cap("The last 13 weeks were held out completely: both the trend and the seasonal "
        "index were refitted on the earlier weeks only, so nothing the model scored "
        "had influenced it.")
    a, b = st.columns([3, 2])
    with a:
        bt = fc[fc["kind"] == "backtest"].sort_values("date")
        fig = base_fig(320, showlegend=True, margin=dict(l=10, r=14, t=30, b=30))
        fig.add_trace(go.Scatter(x=bt["date"], y=bt["value"], name="Actual",
                                 mode="lines+markers", line=dict(color=BLUE, width=2),
                                 hovertemplate="%{x|%b %-d}<br>actual $%{y:,.0f}"
                                               "<extra></extra>"))
        fig.add_trace(go.Scatter(x=bt["date"], y=bt["predicted"], name="Predicted",
                                 mode="lines+markers",
                                 line=dict(color=PLUM, width=2, dash="dash"),
                                 hovertemplate="%{x|%b %-d}<br>predicted $%{y:,.0f}"
                                               "<extra></extra>"))
        fig.update_yaxes(tickprefix="$", tickformat="~s")
        show(fig)
    with b:
        c = st.columns(2)
        c[0].metric("Model MAPE", kv("e8_mape"))
        c[1].metric("Seasonal-naive", kv("e8_naive_mape"))
        c = st.columns(2)
        c[0].metric("RMSE", kv("e8_rmse"))
        c[1].metric("MAE", kv("e8_mae"))
        c = st.columns(2)
        c[0].metric("Weeks to fit", kv("e8_train_weeks"))
        c[1].metric("Weeks held out", kv("e8_holdout_weeks"))
        st.caption("The model beats the naive benchmark, but not by much, which is "
                   "the honest read: this series is so seasonal that last year's "
                   "same week is already a strong guess. The held-out window is "
                   "also a quiet stretch of late summer, so it does not test the "
                   "peaks.")

    yoy = seas2[seas2["kind"] == "year"].sort_values("sort")
    st.markdown("**Year on year**")
    cap("2010 starts in February and 2012 ends in October, so growth is computed on "
        "comparable calendar weeks only.")
    st.dataframe(pd.DataFrame({
        "Year": yoy["label"],
        "Revenue": [f"${v:,.0f}" for v in yoy["value"]],
        "Growth on comparable weeks": [f"{v:+.2f}%" if pd.notna(v) else "—"
                                       for v in yoy["index"]],
    }), hide_index=True, width="stretch")

# ====================================================================== METHOD
with tabs[5]:
    st.subheader("How the dataset was built")
    st.markdown(f"""
1. **Integration.** The sales file was joined to the store file on `Store`, then to
   the features file on `Store` and `Date`. The result is **{kv('records')}**
   store-dept-week rows carrying sales, store attributes and local economic
   indicators side by side.
2. **Preprocessing.** Dates parsed to real timestamps, the holiday flag coerced to a
   boolean, markdown columns read as numbers with blanks treated as zero, and rows
   without a sales figure dropped.
3. **Analysis.** The eight experiments below, each written against the integrated
   table rather than the raw files.
4. **Publication.** Each experiment's results were exported to a table in
   `dashboard_sources/`, and every figure in this app is read from one of those
   tables — nothing is recomputed in the page.
""")

    st.subheader("The eight experiments")
    exp = load("experiments").sort_values("n")
    st.dataframe(pd.DataFrame({
        "#": exp["n"], "Experiment": exp["title"], "Method": exp["method"],
        "Headline result": exp["headline"],
    }), hide_index=True, width="stretch", height=330)

    st.subheader("What to be careful about")
    CAVEATS = [
        ("The markdown window",
         "Markdown columns are blank for the first two years and populated from "
         "November 2011 onward. In that later window every single record carries a "
         "non-zero markdown, so there is no zero-markdown control group anywhere in "
         "the data. Any 'with promotion versus without' comparison here is comparing "
         "a recorded period with an unrecorded one, not a treated group with an "
         "untreated one."),
        ("The holiday flag",
         "The flag marks the week ending after Christmas Day, which is a trough, and "
         "leaves the pre-Christmas peak unflagged. It also treats Super Bowl and "
         "Labor Day as equal to Thanksgiving. Used raw as a model feature it teaches "
         "the wrong calendar."),
        ("The headroom figure is a ceiling",
         "It assumes every store below the top-quartile benchmark could reach that "
         "benchmark. Catchment, local income and competition cap what any individual "
         "store can do, so treat it as the size of a prize worth investigating, not "
         "a target to commit to."),
        ("Significance is not importance",
         "At this sample size almost every test rejects its null hypothesis. The "
         "holiday difference has a p-value below any threshold and an effect size "
         "near 0.05, which is negligible. Read effect sizes and confidence "
         "intervals, not stars."),
        ("Correlation is not a promotion plan",
         "The markdown depth curve rises steeply across records and is almost flat "
         "within a store-dept. The cross-sectional version is mostly store size. "
         "Nothing here identifies a causal promotion effect; that needs a holdout "
         "group the data does not contain."),
        ("Two and a half years, one chain",
         "The window opens in February 2010 and closes in October 2012, giving only "
         "two complete Christmas peaks to learn seasonality from. Store identities "
         "are anonymous and there is no geography, so nothing here separates a "
         "regional effect from a store-specific one."),
    ]
    for chunk in [CAVEATS[i:i + 2] for i in range(0, len(CAVEATS), 2)]:
        cols = st.columns(len(chunk))
        for col, (title, body) in zip(cols, chunk):
            col.markdown(f"**{title}**")
            col.markdown(f'<div class="wsi-cap">{body}</div>',
                         unsafe_allow_html=True)
            col.write("")

    st.divider()
    st.subheader("Sources")
    cap("Every table this app reads, with its size. Regenerate them by running "
        "`build_dashboard_data.py`, then `build_dashboard_sources.py`, then "
        "`build_dashboard_extras.py`.")
    files = sorted(DATA.glob("*.csv"))
    st.dataframe(pd.DataFrame({
        "Table": [f.stem for f in files],
        "Rows": [sum(1 for _ in open(f, encoding="utf-8")) - 1 for f in files],
        "Size": [f"{f.stat().st_size / 1024:,.1f} KB" for f in files],
    }), hide_index=True, width="stretch", height=300)
