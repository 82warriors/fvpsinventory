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
# LOAD DATA (FIXED)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(URL, header=1)

    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # ==================================================
    # 🔥 FIX DATE COLUMN
    # ==================================================
    if "DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

        # Remove invalid rows
        df = df[df["DATE"].notna()]

        # Format display
        df["DATE_DISPLAY"] = df["DATE"].dt.strftime("%d %B %Y")

    return df

df = load_data()

# ==================================================
# SORT LATEST FIRST
# ==================================================
if "DATE" in df.columns:
    df = df.sort_values("DATE", ascending=False)

# ==================================================
# REFRESH BUTTON
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# KPI (LATEST WEEK ONLY)
# ==================================================
st.subheader("📊 Overview")

if "DATE" in df.columns:
    latest_row = df.iloc[0]

    admin_total = latest_row.get("ADMIN INSTALLED", 0)
    acad_total = latest_row.get("ACAD INSTALLED", 0)

else:
    admin_total = 0
    acad_total = 0

col1, col2 = st.columns(2)

col1.metric("Total Admin Devices", int(admin_total))
col2.metric("Total Acad Devices", int(acad_total))

# ==================================================
# DOWNLOAD BUTTON
# ==================================================
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Report",
    csv,
    "patching_report.csv",
    "text/csv"
)

# ==================================================
# DISPLAY TABLE (CLEAN DATE)
# ==================================================
st.subheader("📋 Raw Data")

display_df = df.copy()

# Replace DATE with formatted version
if "DATE_DISPLAY" in display_df.columns:
    display_df["DATE"] = display_df["DATE_DISPLAY"]
    display_df = display_df.drop(columns=["DATE_DISPLAY"])

st.dataframe(
    display_df,
    use_container_width=True,
    height=600
)
