import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path


DATA_PATH = Path("data/labor_data.csv")


st.set_page_config(
    page_title="U.S. Labor Statistics Dashboard",
    page_icon="📊",
    layout="wide",
)


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        return None

    df = pd.read_csv(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_data()


st.title("U.S. Labor Statistics Dashboard")

st.write(
    "This dashboard presents selected monthly labor market indicators from the "
    "U.S. Bureau of Labor Statistics."
)


if df is None:
    st.error(
        "No data file found. Please run `python scripts/update_data.py` first "
        "to create `data/labor_data.csv`."
    )
    st.stop()


# Basic data information
min_date = df["date"].min()
max_date = df["date"].max()
indicators = sorted(df["indicator"].unique())

info_col1, info_col2, info_col3 = st.columns(3)

info_col1.metric("Data Source", "BLS Public API")
info_col2.metric("Frequency", "Monthly, on the 10th")
info_col3.metric(
    "Date Range",
    f"{min_date.strftime('%Y-%m')} to {max_date.strftime('%Y-%m')}",
)


# Latest summary section
st.subheader("Latest Labor Market Summary")

latest_date = df["date"].max()
latest_df = df[df["date"] == latest_date]

st.caption(f"Latest available month: {latest_date.strftime('%B %Y')}")

summary_cols = st.columns(4)

summary_items = [
    "Total Nonfarm Employment",
    "Unemployment Rate",
    "Average Hourly Earnings",
    "Average Weekly Hours",
]

for col, indicator in zip(summary_cols, summary_items):
    row = latest_df[latest_df["indicator"] == indicator]

    if not row.empty:
        value = row["value"].iloc[0]
        unit = row["unit"].iloc[0]
        monthly_change = row["monthly_change"].iloc[0]

        if pd.isna(monthly_change):
            delta = None
        else:
            delta = f"{monthly_change:,.2f}"

        col.metric(
            label=indicator,
            value=f"{value:,.2f}",
            delta=delta,
            help=unit,
        )


# First row: overall trend and single indicator actual values
st.subheader("Labor Market Trends and Indicator Details")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("#### Overall Trend Comparison")

    selected_indicators = st.multiselect(
        "Select indicators",
        indicators,
        default=[
            "Total Nonfarm Employment",
            "Unemployment Rate",
            "Average Hourly Earnings",
        ],
        key="overall_trend_indicators",
    )

    overall_date_range = st.slider(
        "Select date range",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
        key="overall_trend_date_range",
    )

    filtered = df[
        (df["indicator"].isin(selected_indicators))
        & (df["date"] >= pd.to_datetime(overall_date_range[0]))
        & (df["date"] <= pd.to_datetime(overall_date_range[1]))
    ].copy()

    if filtered.empty:
        st.warning("Please select at least one indicator.")
    else:
        normalized = filtered.sort_values(["indicator", "date"]).copy()

        normalized["Baseline Value"] = normalized.groupby("indicator")["value"].transform("first")
        normalized["Normalized Value"] = (
            normalized["value"] / normalized["Baseline Value"] * 100
        )

        fig_trend = px.line(
            normalized,
            x="date",
            y="Normalized Value",
            color="indicator",
            labels={
                "date": "Date",
                "Normalized Value": "Index: First Selected Month = 100",
                "indicator": "Indicator",
            },
        )

        fig_trend.update_layout(
            height=430,
            title_text="",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="center",
                x=0.5,
            ),
            margin=dict(l=20, r=20, t=20, b=80),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.caption(
            "Each selected indicator is normalized to 100 at the first selected month. "
        )


with chart_col2:
    st.markdown("#### Single Indicator Actual Values")

    single_indicator = st.selectbox(
        "Select indicator",
        indicators,
        index=indicators.index("Unemployment Rate") if "Unemployment Rate" in indicators else 0,
        key="single_indicator_selector",
    )

    single_date_range = st.slider(
        "Select date range",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
        key="single_indicator_date_range",
    )

    single_df = df[
        (df["indicator"] == single_indicator)
        & (df["date"] >= pd.to_datetime(single_date_range[0]))
        & (df["date"] <= pd.to_datetime(single_date_range[1]))
    ].copy()

    if single_df.empty:
        st.warning("No data available for the selected indicator.")
    else:
        fig_single = px.area(
            single_df,
            x="date",
            y="value",
            labels={
                "date": "Date",
                "value": single_df["unit"].iloc[0],
            },
        )

        fig_single.update_layout(
            height=430,
            title_text="",
            margin=dict(l=20, r=20, t=20, b=20),
        )

        st.plotly_chart(fig_single, use_container_width=True)


# Change analysis: one bar chart with tabs
st.subheader("Change Analysis")

change_indicator = st.selectbox(
    "Select indicator for change analysis",
    indicators,
    index=indicators.index("Unemployment Rate") if "Unemployment Rate" in indicators else 0,
    key="change_indicator_selector",
)

change_date_range = st.slider(
    "Select date range for change analysis",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    key="change_date_range",
)

change_df = df[
    (df["indicator"] == change_indicator)
    & (df["date"] >= pd.to_datetime(change_date_range[0]))
    & (df["date"] <= pd.to_datetime(change_date_range[1]))
].copy()

monthly_tab, yearly_tab = st.tabs(["Monthly Change", "Year-over-Year Change"])

with monthly_tab:
    monthly_change_df = change_df.dropna(subset=["monthly_change"])

    if monthly_change_df.empty:
        st.warning("Monthly change data are not available for this indicator.")
    else:
        fig_monthly = px.bar(
            monthly_change_df,
            x="date",
            y="monthly_change",
            labels={
                "date": "Date",
                "monthly_change": "Monthly Change",
            },
        )

        fig_monthly.update_layout(
            height=430,
            title_text="",
            margin=dict(l=20, r=20, t=20, b=20),
        )

        st.plotly_chart(fig_monthly, use_container_width=True)


with yearly_tab:
    yearly_change_df = change_df.dropna(subset=["year_over_year_percent_change"])

    if yearly_change_df.empty:
        st.warning("Year-over-year change data are not available for this indicator.")
    else:
        fig_yearly = px.bar(
            yearly_change_df,
            x="date",
            y="year_over_year_percent_change",
            labels={
                "date": "Date",
                "year_over_year_percent_change": "Year-over-Year Change (%)",
            },
        )

        fig_yearly.update_layout(
            height=430,
            title_text="",
            margin=dict(l=20, r=20, t=20, b=20),
        )

        st.plotly_chart(fig_yearly, use_container_width=True)


# Recent changes table
st.subheader("Recent Labor Market Changes")

recent_table = (
    df.sort_values("date")
    .groupby("indicator")
    .tail(1)
    .copy()
)

recent_table = recent_table[
    [
        "indicator",
        "date",
        "value",
        "unit",
        "monthly_change",
        "year_over_year_change",
        "monthly_percent_change",
        "year_over_year_percent_change",
    ]
]

recent_table["date"] = recent_table["date"].dt.strftime("%Y-%m")

recent_table = recent_table.rename(
    columns={
        "indicator": "Indicator",
        "date": "Latest Month",
        "value": "Latest Value",
        "unit": "Unit",
        "monthly_change": "Monthly Change",
        "year_over_year_change": "Year-over-Year Change",
        "monthly_percent_change": "Monthly Change (%)",
        "year_over_year_percent_change": "Year-over-Year Change (%)",
    }
)

st.dataframe(
    recent_table,
    use_container_width=True,
    hide_index=True,
)


# Raw data section
st.subheader("Source Data")

with st.expander("View source data"):
    raw_data = df.rename(
        columns={
            "date": "Date",
            "series_id": "Series ID",
            "indicator": "Indicator",
            "category": "Category",
            "unit": "Unit",
            "value": "Value",
            "monthly_change": "Monthly Change",
            "year_over_year_change": "Year-over-Year Change",
            "monthly_percent_change": "Monthly Change (%)",
            "year_over_year_percent_change": "Year-over-Year Change (%)",
        }
    )

    st.dataframe(raw_data, use_container_width=True, hide_index=True)


st.markdown("---")

st.caption(
    "Data source: U.S. Bureau of Labor Statistics Public Data API. "
    "The data are collected and cleaned using a separate Python script, saved as a CSV file, "
    "and designed to be updated monthly through GitHub Actions."
)