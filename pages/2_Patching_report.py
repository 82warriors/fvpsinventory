import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠 Patching Report")

# ==================================================
# DATA SOURCE
# ==================================================
URL = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"

# ==================================================
# LOAD DATA (CLEAN + STABLE)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(URL, header=1)

    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # -------------------------
    # FIX DATE
    # -------------------------
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df[df["DATE"].notna()]  # remove bad rows

    # -------------------------
    # NUMERIC CLEAN
    # -------------------------
    for col in df.columns:
        if col != "DATE":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # -------------------------
    # SORT (LATEST FIRST)
    # -------------------------
    df = df.sort_values("DATE", ascending=False)

    return df


df = load_data()

# ==================================================
# REFRESH BUTTON
# ==================================================
col_btn, _ = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# ==================================================
# KPI SECTION (LATEST WEEK ONLY)
# ==================================================
st.markdown("## 📊 Overview")

latest = df.iloc[0]

admin = int(latest.get("ADMIN INSTALLED", 0))
acad = int(latest.get("ACAD INSTALLED", 0))

col1, col2 = st.columns(2)

col1.metric("Total Admin Devices", admin)
col2.metric("Total Acad Devices", acad)

# ==================================================
# TREND CHART
# ==================================================
st.markdown("## 📈 Weekly Trend")

trend_df = df.copy()
trend_df["Week"] = trend_df["DATE"].dt.strftime("%d %b")

trend_df["Total"] = (
    trend_df["ADMIN INSTALLED"] +
    trend_df["ACAD INSTALLED"]
)

st.line_chart(trend_df.set_index("Week")["Total"])

# ==================================================
# DOWNLOAD
# ==================================================
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Report",
    csv,
    "patching_report.csv",
    "text/csv"
)

# ==================================================
# DISPLAY TABLE (CLEAN)
# ==================================================
st.markdown("## 📋 Raw Data")

display_df = df.copy()

# Format DATE nicely
display_df["DATE"] = display_df["DATE"].dt.strftime("%d %B %Y")

st.dataframe(
    display_df,
    use_container_width=True,
    height=600,
    hide_index=True  # ✅ THIS FIXES YOUR ISSUE
)
