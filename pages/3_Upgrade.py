import streamlit as st
import pandas as pd
import altair as alt
import requests
import io

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(
    page_title="Upgrade Tracking Dashboard",
    layout="wide"
)

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Auto-updated from Google Sheets")

# =====================================
# GOOGLE SHEET CONFIG
# =====================================
SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"
GID = "1946114847"

CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"
)

# =====================================
# REFRESH BUTTON
# =====================================
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# =====================================
# LOAD DATA
# =====================================
@st.cache_data(ttl=60)
def load_data(url):

    try:

        response = requests.get(url)

        if response.status_code != 200:
            return None, f"HTTP Error {response.status_code}"

        df = pd.read_csv(
            io.StringIO(response.text),
            dtype=str
        )

        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
        )

        return df, None

    except Exception as e:
        return None, str(e)

df, error = load_data(CSV_URL)

if error:
    st.error(error)
    st.stop()

# =====================================
# CLEAN DATA
# =====================================
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

# =====================================
# FIND DATE COLUMN
# =====================================
DATE_COLUMNS = [
    "TIMESTAMP",
    "DATE",
    "UPDATED DATE",
    "LAST UPDATED",
    "CREATED DATE"
]

date_col = None

for col in DATE_COLUMNS:
    if col in df.columns:
        date_col = col
        break

# =====================================
# CREATE WEEK COLUMN
# =====================================
if date_col:

    df[date_col] = pd.to_datetime(
        df[date_col],
        errors="coerce"
    )

    df = df[df[date_col].notna()]

    iso = df[date_col].dt.isocalendar()

    df["WEEK"] = (
        iso.year.astype(str)
        + " - Week "
        + iso.week.astype(str)
    )

else:

    df["WEEK"] = "Current Week"

# =====================================
# TARGET MODELS
# =====================================
TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

df_filtered = df[
    df["MODEL"].isin(TARGET_MODELS)
]

# =====================================
# CREATE TABS
# =====================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Week",
    "📅 All Weeks Summary",
    "🗂️ Weekly Tables",
    "📄 Raw Data"
])

# =====================================
# CURRENT WEEK TAB
# =====================================
with tab1:

    latest_week = sorted(
        df_filtered["WEEK"].unique()
    )[-1]

    current_df = df_filtered[
        df_filtered["WEEK"] == latest_week
    ]

    st.subheader(f"📊 {latest_week}")

    summary = (
        current_df.groupby(
            ["MODEL", "IPU STATUS"]
        )
        .size()
        .unstack(fill_value=0)
    )

    if "Completed" not in summary.columns:
        summary["Completed"] = 0

    if "Not Completed" not in summary.columns:
        summary["Not Completed"] = 0

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

    completed = int(summary["Completed"].sum())
    not_completed = int(summary["Not Completed"].sum())
    total = completed + not_completed

    rate = 0

    if total > 0:
        rate = completed / total * 100

    c1, c2, c3 = st.columns(3)

    c1.metric("✅ Completed", completed)
    c2.metric("❌ Not Completed", not_completed)
    c3.metric("📈 Completion Rate", f"{rate:.2f}%")

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )

# =====================================
# ALL WEEKS SUMMARY
# =====================================
with tab2:

    st.subheader("📅 Weekly Summary")

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

    chart = alt.Chart(
        weekly_summary
    ).mark_line(point=True).encode(
        x="WEEK:N",
        y="Completion %:Q",
        tooltip=["WEEK", "Completion %"]
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )

# =====================================
# WEEKLY TABLES
# =====================================
with tab3:

    st.subheader("🗂️ Weekly Breakdown")

    weeks = sorted(
        df_filtered["WEEK"].unique(),
        reverse=True
    )

    for week in weeks:

        with st.expander(week):

            week_df = df_filtered[
                df_filtered["WEEK"] == week
            ]

            st.dataframe(
                week_df,
                use_container_width=True,
                hide_index=True
            )

# =====================================
# RAW DATA TAB
# =====================================
with tab4:

    st.subheader("📄 Raw Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
