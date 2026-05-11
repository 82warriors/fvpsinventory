```python
import streamlit as st
import pandas as pd
import altair as alt
import requests
import io

# ==============================
# CONFIG
# ==============================
st.set_page_config(
    page_title="Upgrade Tracking Dashboard",
    layout="wide"
)

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Auto-updated from Google Sheets")

SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"
GID = "1946114847"

CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"
)

# ==============================
# REFRESH BUTTON
# ==============================
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# ==============================
# LOAD DATA
# ==============================
@st.cache_data(ttl=60)
def load_data(url):

    try:
        res = requests.get(url)

        if res.status_code != 200:
            return None, f"HTTP Error {res.status_code}"

        if "text/html" in res.headers.get("Content-Type", ""):
            return None, "Google returned HTML"

        df = pd.read_csv(
            io.StringIO(res.text),
            dtype=str
        )

        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.upper()
        )

        return df, None

    except Exception as e:
        return None, str(e)

df, error = load_data(CSV_URL)

if error:
    st.error("❌ Failed to load data")
    st.warning(error)
    st.stop()

st.success("✅ Data loaded successfully")

# ==============================
# REQUIRED HEADERS
# ==============================
REQUIRED_HEADERS = [
    "SCHOOL NAME",
    "HOSTNAME",
    "SERIAL NUMBER",
    "ASSET TAG",
    "CUSTODIAN",
    "LOCATION",
    "BRAND",
    "MODEL",
    "CATEGORY",
    "IPU STATUS",
    "EOL STATUS"
]

missing = [
    h for h in REQUIRED_HEADERS
    if h not in df.columns
]

if missing:
    st.error("❌ Missing required headers")
    st.write(missing)
    st.stop()

# ==============================
# CLEAN DATA
# ==============================
df["MODEL"] = (
    df["MODEL"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df["IPU STATUS"] = (
    df["IPU STATUS"]
    .astype(str)
    .str.title()
    .str.strip()
)

df["CATEGORY"] = (
    df["CATEGORY"]
    .astype(str)
    .str.upper()
    .str.strip()
)

# ==============================
# DETECT DATE COLUMN
# ==============================
DATE_COLUMNS = [
    "TIMESTAMP",
    "DATE",
    "UPDATED DATE",
    "LAST UPDATED",
    "CREATED DATE"
]

date_col_found = None

for col in DATE_COLUMNS:
    if col in df.columns:
        date_col_found = col
        break

# ==============================
# CREATE WEEK COLUMN
# ==============================
if date_col_found:

    df[date_col_found] = pd.to_datetime(
        df[date_col_found],
        errors="coerce"
    )

    df = df[df[date_col_found].notna()]

    iso_calendar = df[date_col_found].dt.isocalendar()

    df["WEEK"] = (
        iso_calendar.year.astype(str)
        + " - Week "
        + iso_calendar.week.astype(str)
    )

else:

    st.warning(
        "⚠️ No date column found. "
        "Using Current Week only."
    )

    df["WEEK"] = "Current Week"

# ==============================
# TARGET MODELS
# ==============================
TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

df_filtered = df[
    df["MODEL"].isin(TARGET_MODELS)
]

# ==============================
# TABS
# ==============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Week",
    "📅 All Weeks Summary",
    "🗂️ Weekly Tables",
    "📄 Raw Data"
])

# =====================================================
# TAB 1 — CURRENT WEEK
# =====================================================
with tab1:

    latest_week = sorted(
        df_filtered["WEEK"].dropna().unique()
    )[-1]

    current_df = df_filtered[
        df_filtered["WEEK"] == latest_week
    ]

    st.markdown(f"## 📊 Current Week ({latest_week})")

    summary = (
        current_df.groupby(
            ["MODEL", "IPU STATUS"]
        )
        .size()
        .unstack(fill_value=0)
    )

    for col in ["Completed", "Not Completed"]:
        if col not in summary.columns:
            summary[col] = 0

    summary = summary.reset_index()

    summary["Total"] = (
        summary["Completed"]
        + summary["Not Completed"]
    )

    summary["Completion %"] = (
        summary["Completed"]
        / summary["Total"]
        * 100
    ).round(2)

    # KPIs
    completed = int(summary["Completed"].sum())
    not_completed = int(summary["Not Completed"].sum())
    total = completed + not_completed

    rate = (
        completed / total * 100
        if total > 0 else 0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("✅ Completed", completed)
    c2.metric("❌ Not Completed", not_completed)
    c3.metric("📈 Completion Rate", f"{rate:.2f}%")

    # TABLE
    st.markdown("### 📋 Summary Table")

    st.dataframe(
        summary[
            [
                "MODEL",
                "Completed",
                "Not Completed",
                "Total",
                "Completion %"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    # CHART
    st.markdown("### 📈 Upgrade Progress")

    chart_df = summary.melt(
        id_vars=["MODEL", "Total"],
        value_vars=[
            "Completed",
            "Not Completed"
        ],
        var_name="Status",
        value_name="Count"
    )

    chart_df["Percent"] = (
        chart_df["Count"]
        / chart_df["Total"]
        * 100
    ).round(1)

    chart_df["Label"] = (
        chart_df["Percent"]
        .astype(str)
        + "%"
    )

    base = alt.Chart(chart_df).encode(
        x=alt.X("MODEL:N"),
        y=alt.Y("Count:Q"),
        xOffset="Status:N"
    )

    bars = (
        base.mark_bar()
        .encode(color="Status:N")
    )

    text = (
        base.mark_text(dy=-5)
        .encode(text="Label")
    )

    st.altair_chart(
        (bars + text).properties(height=400),
        use_container_width=True
    )

# =====================================================
# TAB 2 — ALL WEEKS SUMMARY
# =====================================================
with tab2:

    st.markdown("## 📅 Weekly Summary")

    weekly_summary = (
        df_filtered.groupby(
            ["WEEK", "IPU STATUS"]
        )
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    if "Completed" not in weekly_summary.columns:
        weekly_summary["Completed"] = 0

    if "Not Completed" not in weekly_summary.columns:
        weekly_summary["Not Completed"] = 0

    weekly_summary["Total"] = (
        weekly_summary["Completed"]
        + weekly_summary["Not Completed"]
    )

    weekly_summary["Completion %"] = (
        weekly_summary["Completed"]
        / weekly_summary["Total"]
        * 100
    ).round(2)

    st.dataframe(
        weekly_summary,
        use_container_width=True,
        hide_index=True
    )

    # TREND CHART
    st.markdown("### 📈 Weekly Completion Trend")

    trend_chart = alt.Chart(
        weekly_summary
    ).mark_line(point=True).encode(
        x="WEEK:N",
        y="Completion %:Q",
        tooltip=[
            "WEEK",
            "Completion %"
        ]
    )

    st.altair_chart(
        trend_chart,
        use_container_width=True
    )

# =====================================================
# TAB 3 — WEEKLY TABLES
# =====================================================
with tab3:

    st.markdown("## 🗂️ Weekly Breakdown")

    all_weeks = sorted(
        df_filtered["WEEK"]
        .dropna()
        .unique(),
        reverse=True
    )

    for week in all_weeks:

        with st.expander(f"📅 {week}"):

            week_df = df_filtered[
                df_filtered["WEEK"] == week
            ]

            st.metric(
                "Total Devices",
                len(week_df)
            )

            summary_week = (
                week_df.groupby(
                    ["MODEL", "IPU STATUS"]
                )
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )

            st.markdown("### 📋 Weekly Summary")

            st.dataframe(
                summary_week,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 💻 Device Details")

            st.dataframe(
                week_df,
                use_container_width=True,
                hide_index=True
            )

# =====================================================
# TAB 4 — RAW DATA
# =====================================================
with tab4:

    st.markdown("## 📄 Raw Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
```
