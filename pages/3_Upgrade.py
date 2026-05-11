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

            # Clean headers
            temp_df.columns = (
                temp_df.columns
                .astype(str)
                .str.strip()
                .str.upper()
            )

            # Add week column
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
    st.error("❌ Failed to load data")
    st.warning(error)
    st.stop()

st.success("✅ All weekly sheets loaded")

# =====================================
# REQUIRED HEADERS
# =====================================
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

df["CATEGORY"] = (
    df["CATEGORY"]
    .astype(str)
    .str.upper()
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
# CREATE TABS
# =====================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Week",
    "📅 All Weeks Summary",
    "🗂️ Weekly Tables",
    "📄 Raw Data"
])

# =====================================
# TAB 1 — CURRENT WEEK
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

    # KPIs
    completed = int(summary["Completed"].sum())

    not_completed = int(
        summary["Not Completed"].sum()
    )

    total = completed + not_completed

    rate = 0

    if total > 0:
        rate = completed / total * 100

    c1, c2, c3 = st.columns(3)

    c1.metric("✅ Completed", completed)
    c2.metric("❌ Not Completed", not_completed)
    c3.metric("📈 Completion Rate", f"{rate:.2f}%")

    # TABLE
    st.markdown("### 📋 Summary Table")

    st.dataframe(
        summary,
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

# =====================================
# TAB 2 — ALL WEEKS SUMMARY
# =====================================
with tab2:

    st.subheader("📅 Weekly Summary")

    weekly_rows = []

    for week in sorted_weeks:

        week_df = df_filtered[
            df_filtered["WEEK"] == week
        ]

        # MODEL COUNTS
        acer_total = len(
            week_df[
                week_df["MODEL"] == "ACER VX2670G DESKTOP"
            ]
        )

        k14_total = len(
            week_df[
                week_df["MODEL"] == "LENOVO K14 GEN2"
            ]
        )

        yoga_total = len(
            week_df[
                week_df["MODEL"] == "LENOVO L13 YOGA G4"
            ]
        )

        # STATUS COUNTS
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

        completion_rate = 0

        if total > 0:
            completion_rate = round(
                completed / total * 100,
                2
            )

        weekly_rows.append({
            "WEEK": week,
            "ACER VX2670G DESKTOP": acer_total,
            "LENOVO K14 GEN2": k14_total,
            "LENOVO L13 YOGA G4": yoga_total,
            "Completed": completed,
            "Not Completed": not_completed,
            "Total": total,
            "Completion %": completion_rate
        })

    weekly_summary = pd.DataFrame(weekly_rows)

    st.dataframe(
        weekly_summary,
        use_container_width=True,
        hide_index=True
    )

    # TREND CHART
    st.subheader("📈 Weekly Completion Trend")

    chart = alt.Chart(
        weekly_summary
    ).mark_line(point=True).encode(
        x=alt.X("WEEK:N", sort=None),
        y=alt.Y("Completion %:Q"),
        tooltip=[
            "WEEK",
            "Completed",
            "Not Completed",
            "Completion %"
        ]
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )

# =====================================
# TAB 3 — WEEKLY TABLES
# =====================================
with tab3:

    st.subheader("🗂️ Weekly Breakdown")

    for week in sorted_weeks:

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

# =====================================
# TAB 4 — RAW DATA
# =====================================
with tab4:

    st.subheader("📄 Raw Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
