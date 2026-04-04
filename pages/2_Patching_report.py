import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠 Patching Report")

URL = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/export?format=csv"

# ==================================================
# LOAD RAW DATA (NO LOSS)
# ==================================================
@st.cache_data(ttl=120)
def load_data():

    # 🔥 LOAD EVERYTHING AS TEXT (NO DATA LOSS)
    raw_df = pd.read_csv(URL, header=None, dtype=str)

    # 🔍 FIND HEADER ROW (contains DATE)
    header_row = None
    for i in range(len(raw_df)):
        row = raw_df.iloc[i].astype(str).str.upper()

        if "DATE" in row.values:
            header_row = i
            break

    if header_row is None:
        st.error("❌ Header row not found")
        st.stop()

    # ✅ RELOAD WITH CORRECT HEADER
    df = pd.read_csv(URL, header=header_row, dtype=str)

    df.columns = df.columns.str.strip()

    # ✅ REMOVE ONLY USELESS COLUMNS (NOT ROWS)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    return df


df = load_data()

# ==================================================
# REFRESH
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# KPI (SAFE)
# ==================================================
st.markdown("## 📊 Overview")

admin = 0
acad = 0

if "DATE" in df.columns:
    df["DATE_PARSED"] = pd.to_datetime(df["DATE"], errors="coerce")

    latest = df[df["DATE_PARSED"].notna()].sort_values("DATE_PARSED", ascending=False)

    if len(latest) > 0:
        latest_row = latest.iloc[0]
        admin = int(float(latest_row.get("ADMIN INSTALLED", 0) or 0))
        acad = int(float(latest_row.get("ACAD INSTALLED", 0) or 0))

col1, col2 = st.columns(2)

col1.metric("Total Admin Devices", admin)
col2.metric("Total Acad Devices", acad)

# ==================================================
# DISPLAY FULL TABLE (NO LOSS)
# ==================================================
st.markdown("## 📋 Raw Data (Full Google Sheet)")

display_df = df.copy()

# Optional: format date nicely WITHOUT removing rows
if "DATE" in display_df.columns:
    parsed = pd.to_datetime(display_df["DATE"], errors="coerce")

    display_df["DATE"] = parsed.where(
        parsed.notna(),
        display_df["DATE"]
    )

    display_df["DATE"] = display_df["DATE"].apply(
        lambda x: x.strftime("%d %B %Y") if isinstance(x, pd.Timestamp) else x
    )

st.dataframe(
    display_df,
    use_container_width=True,
    height=650,
    hide_index=True
)

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
