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
st.markdown("### 📊 Overview")

# Safe column handling
admin_total = df.get("ADMIN INSTALLED", pd.Series(dtype=float)).sum()
acad_total = df.get("ACAD INSTALLED", pd.Series(dtype=float)).sum()

col1, col2 = st.columns(2)

total_devices = admin_total + acad_total

installed = (
    df.get("ADMIN INSTALLED", 0).sum() +
    df.get("ACAD INSTALLED", 0).sum()
)

percentage = (installed / total_devices * 100) if total_devices > 0 else 0

st.metric("Installed %", f"{percentage:.1f}%")

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
