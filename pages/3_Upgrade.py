import streamlit as st
import pandas as pd
import altair as alt
import requests
import io

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Auto-updated from LATEST sheet")

SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"
GID = "1946114847"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&gid={GID}"

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
            return None, "Google returned HTML → check sharing permissions"

        df = pd.read_csv(io.StringIO(res.text), dtype=str)

        df.columns = df.columns.astype(str).str.strip().str.upper()

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
# VALIDATION
# ==============================
REQUIRED_HEADERS = [
    "SCHOOL NAME","HOSTNAME","SERIAL NUMBER","ASSET TAG",
    "CUSTODIAN","LOCATION","BRAND","MODEL",
    "CATEGORY","IPU STATUS","EOL STATUS"
]

if not all(h in df.columns for h in REQUIRED_HEADERS):
    st.error("❌ Required headers missing")
    st.write(df.columns.tolist())
    st.stop()

# ==============================
# CLEAN DATA
# ==============================
df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()
df["CATEGORY"] = df["CATEGORY"].astype(str).str.upper().str.strip()

# ==============================
# CREATE WEEK COLUMN
# ==============================
if "TIMESTAMP" in df.columns:
    df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"], errors="coerce")
    df["WEEK"] = df["TIMESTAMP"].dt.strftime("%Y - Week %U")
else:
    df["WEEK"] = "Current Week"

# ==============================
# TARGET MODELS
# ==============================
TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

df_filtered = df[df["MODEL"].isin(TARGET_MODELS)]

# ==============================
# TABS
# ==============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Current Week",
    "📅 All Weeks Summary",
    "🗂️ Weekly Tables",
    "📄 Raw Data"
])

# =========================================================
# TAB 1 — CURRENT WEEK
# =========================================================
with tab1:

    latest_week = sorted(df_filtered["WEEK"].dropna().unique())[-1]

    current_df = df_filtered[df_filtered["WEEK"] == latest_week]

    st.markdown(f"## 📊 Current Week ({latest_week})")

    summary = current_df.groupby(
        ["MODEL","IPU STATUS"]
    ).size().unstack(fill_value=0)

    for col in ["Completed","Not Completed"]:
        if col not in summary.columns:
            summary[col] = 0

    summary = summary.reset_index()

    summary["Total"] = (
        summary["Completed"] +
        summary["Not Completed"]
    )

    summary["Completion %"] = (
        summary["Completed"] /
        summary["Total"]
    ).fillna(0) * 100

    summary["Completion %"] = summary["Completion %"].round(2)

    # KPIs
    completed = int(summary["Completed"].sum())
    not_completed = int(summary["Not Completed"].sum())
    total = completed + not_completed
    rate = (completed / total * 100) if total > 0 else 0

    c1, c2, c3 = st.columns(3)

    c1.metric("✅ Completed", completed)
    c2.metric("❌ Not Completed", not_completed)
    c3.metric("📈 Completion Rate", f"{rate:.2f}%")

    # TABLE
    st.markdown("### 📋 Summary Table")

    st.dataframe(
        summary[
            ["MODEL","Completed","Not Completed","Total","Completion %"]
        ],
        use_container_width=True,
        hide_index=True
    )

    # CHART
    st.markdown("### 📈 Upgrade Progress")

    chart_df = summary.melt(
        id_vars=["MODEL","Total"],
        value_vars=["Completed","Not Completed"],
        var_name="Status",
        value_name="Count"
    )

    chart_df["Percent"] = (
        chart_df["Count"] /
        chart_df["Total"] * 100
    ).round(1)

    chart_df["Label"] = chart_df["Percent"].astype(str) + "%"

    base = alt.Chart(chart_df).encode(
        x=alt.X("MODEL:N"),
        y=alt.Y("Count:Q"),
        xOffset="Status:N"
    )

    bars = base.mark_bar().encode(color="Status:N")
    text = base.mark_text(dy=-5).encode(text="Label")

    st.altair_chart(
        (bars + text).properties(height=400),
        use_container_width=True
    )

# =========================================================
# TAB 2 — ALL WEEKS SUMMARY
# =========================================================
with tab2:

    st.markdown("## 📅 Weekly Summary")

    weekly_summary = (
        df_filtered.groupby(["WEEK","IPU STATUS"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    if "Completed" not in weekly_summary.columns:
        weekly_summary["Completed"] = 0

    if "Not Completed" not in weekly_summary.columns:
        weekly_summary["Not Completed"] = 0

    weekly_summary["Total"] = (
        weekly_summary["Completed"] +
        weekly_summary["Not Completed"]
    )

    weekly_summary["Completion %"] = (
        weekly_summary["Completed"] /
        weekly_summary["Total"] * 100
    ).round(2)

    st.dataframe(
        weekly_summary,
        use_container_width=True,
        hide_index=True
    )

    # Weekly Trend Chart
    chart = alt.Chart(weekly_summary).mark_line(point=True).encode(
        x="WEEK:N",
        y="Completion %:Q",
        tooltip=["WEEK","Completion %"]
    )

    st.altair_chart(chart, use_container_width=True)

# =========================================================
# TAB 3 — WEEKLY TABLES
# =========================================================
with tab3:

    st.markdown("## 🗂️ Weekly Breakdown Tables")

    weeks = sorted(df_filtered["WEEK"].dropna().unique(), reverse=True)

    for week in weeks:

        with st.expander(f"📅 {week}", expanded=False):

            week_df = df_filtered[df_filtered["WEEK"] == week]

            st.metric("Total Devices", len(week_df))

            summary_week = (
                week_df.groupby(["MODEL","IPU STATUS"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )

            st.dataframe(
                summary_week,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 📋 Device List")

            st.dataframe(
                week_df,
                use_container_width=True,
                hide_index=True
            )

# =========================================================
# TAB 4 — RAW DATA
# =========================================================
with tab4:

    st.markdown("## 📄 Full Raw Data")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
