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

XLSX_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SPREADSHEET_ID}/export?format=xlsx"
)

# =====================================
# REFRESH BUTTON
# =====================================
if st.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

# =====================================
# LOAD ALL SHEETS
# =====================================
@st.cache_data(ttl=60)
def load_all_sheets():

    try:

        response = requests.get(XLSX_URL)

        if response.status_code != 200:
            return None, f"HTTP Error {response.status_code}"

        excel_data = pd.ExcelFile(
            io.BytesIO(response.content),
            engine="openpyxl"
        )

        all_data = []

        for sheet_name in excel_data.sheet_names:

            # Skip LATEST tab
            if sheet_name.upper() == "LATEST":
                continue

            temp_df = pd.read_excel(
                excel_data,
                sheet_name=sheet_name,
                dtype=str
            )

            temp_df.columns = (
                temp_df.columns
                .astype(str)
                .str.strip()
                .str.upper()
            )

            temp_df["WEEK"] = sheet_name

            all_data.append(temp_df)

        final_df = pd.concat(
            all_data,
            ignore_index=True
        )

        return final_df, None

    except Exception as e:
        return None, str(e)

df, error = load_all_sheets()

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
# SORT WEEKS
# =====================================
def sort_weeks(week_name):

    try:
        return pd.to_datetime(
            week_name,
            format="%d %B %Y"
        )

    except:
        return pd.Timestamp.min

sorted_weeks = sorted(
    df_filtered["WEEK"].dropna().unique(),
    key=sort_weeks,
    reverse=True
)

# =====================================
# TABS
# =====================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Week",
    "📅 All Weeks Summary",
    "🗂️ Weekly Tables",
    "📄 Raw Data"
])

# =====================================
# TAB 1 - CURRENT WEEK
# =====================================
with tab1:

    latest_week = sorted_weeks[0]

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
        .reset_index()
    )

    if "Completed" not in summary.columns:
        summary["Completed"] = 0

    if "Not Completed" not in summary.columns:
        summary["Not Completed"] = 0

    summary["Total"] = (
        summary["Completed"] +
        summary["Not Completed"]
    )

    summary["Completion %"] = (
        summary["Completed"] /
        summary["Total"] * 100
    ).round(2)

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )

# =====================================
# TAB 2 - ALL WEEKS SUMMARY
# =====================================
with tab2:

    st.subheader("📅 All Weeks Summary")

    weekly_summary = []

    for week in sorted_weeks:

        week_df = df_filtered[
            df_filtered["WEEK"] == week
        ]

        acer_count = len(
            week_df[
                week_df["MODEL"] == "ACER VX2670G DESKTOP"
            ]
        )

        k14_count = len(
            week_df[
                week_df["MODEL"] == "LENOVO K14 GEN2"
            ]
        )

        yoga_count = len(
            week_df[
                week_df["MODEL"] == "LENOVO L13 YOGA G4"
            ]
        )

        completed = len(
            week_df[
                week_df["IPU STATUS"] == "Completed"
            ]
        )

        not_completed = len(
            week_df[
                week_df["IPU STATUS"] == "Not Completed"
            ]
        )

        total = completed + not_completed

        completion = 0

        if total > 0:
            completion = round(
                completed / total * 100,
                2
            )

        weekly_summary.append({
            "WEEK": week,
            "ACER VX2670G DESKTOP": acer_count,
            "LENOVO K14 GEN2": k14_count,
            "LENOVO L13 YOGA G4": yoga_count,
            "Completed": completed,
            "Not Completed": not_completed,
            "Total": total,
            "Completion %": completion
        })

    weekly_df = pd.DataFrame(
        weekly_summary
    )

    st.dataframe(
        weekly_df,
        use_container_width=True,
        hide_index=True
    )

    chart = alt.Chart(
        weekly_df
    ).mark_line(point=True).encode(
        x=alt.X("WEEK:N", sort=None),
        y="Completion %:Q",
        tooltip=[
            "WEEK",
            "Completion %"
        ]
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )

# =====================================
# TAB 3 - WEEKLY TABLES
# =====================================
with tab3:

    st.subheader("🗂️ Weekly Breakdown")

    for week in sorted_weeks:

        with st.expander(f"📅 {week}"):

            week_df = df_filtered[
                df_filtered["WEEK"] == week
            ]

            st.dataframe(
                week_df,
                use_container_width=True,
                hide_index=True
            )

# =====================================
# TAB 4 - RAW DATA
# =====================================
with tab4:

    st.subheader("📄 Raw Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
