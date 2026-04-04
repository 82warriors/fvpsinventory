import streamlit as st
import pandas as pd

st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠 Patching Report")

URL = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"

# =========================
# REFRESH BUTTON
# =========================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(URL, header=1)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    return df

df = load_data()

# =========================
# KPI
# =========================
# Ensure DATE is datetime
df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

# Get latest row
latest_row = df.sort_values("DATE", ascending=False).iloc[0]

admin_total = latest_row.get("ADMIN INSTALLED", 0)
acad_total = latest_row.get("ACAD INSTALLED", 0)

# Display
col1, col2 = st.columns(2)

col1.metric("Total Admin Devices", int(admin_total))
col2.metric("Total Acad Devices", int(acad_total))

# =========================
# FILTER
# =========================
if "Week" in df.columns:
    week = st.selectbox("Select Week", ["All"] + list(df["Week"].dropna().unique()))

    if week != "All":
        df = df[df["Week"] == week]

# =========================
# EXPORT
# =========================
csv = df.to_csv(index=False).encode("utf-8")

st.download_button("📥 Download Report", csv, "patching.csv", "text/csv")

# =========================
# TABLE
# =========================
st.dataframe(df, use_container_width=True)

# ==================================================
# FIX DATE COLUMN
# ==================================================
if "DATE" in df.columns:
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")

    # Remove invalid dates
    df = df[df["DATE"].notna()]

    # Format display (01 March 2026)
    df["DATE_DISPLAY"] = df["DATE"].dt.strftime("%d %B %Y")
