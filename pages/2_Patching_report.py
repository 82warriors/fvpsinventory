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
# LOAD DATA (ROBUST)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    df = pd.read_csv(URL, header=1)

    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    # -------------------------
    # FIX DATE
    # -------------------------
    if "DATE" in df.columns:
        df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
        df = df[df["DATE"].notna()]

    # -------------------------
    # NUMERIC CLEAN
    # -------------------------
    num_cols = df.columns.drop("DATE", errors="ignore")

    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Sort latest first
    df = df.sort_values("DATE", ascending=False)

    return df


df = load_data()

# ==================================================
# REFRESH BUTTON
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# KPI (LATEST WEEK)
# ==================================================
st.markdown("## 📊 Overview")

if len(df) > 0:
    latest = df.iloc[0]

    admin = latest.get("ADMIN INSTALLED", 0)
    acad = latest.get("ACAD INSTALLED", 0)

    # Patching % formula
    total_base = (
        latest.get("ADMIN SCCM EPP > 4 wks", 0) +
        latest.get("ACAD SCCM EPP > 4 wks", 0) +
        latest.get("ADMIN NOT CONNECTED", 0) +
        latest.get("ACAD NOT CONNECTED", 0) +
        latest.get("ADMIN REQUIRED", 0) +
        latest.get("ACAD REQUIRED", 0) +
        latest.get("ADMIN UNKNOWN", 0) +
        latest.get("ACAD UNKNOWN", 0) +
        latest.get("E-EXAM", 0) +
        latest.get("FAULTY", 0)
    )

    installed = admin + acad

    patching_pct = (installed / total_base * 100) if total_base > 0 else 0

else:
    admin = acad = patching_pct = 0

col1, col2, col3 = st.columns(3)

col1.metric("Admin Devices", int(admin))
col2.metric("Acad Devices", int(acad))
col3.metric("Patching %", f"{patching_pct:.1f}%")

# ==================================================
# WEEKLY TREND
# ==================================================
st.markdown("## 📈 Weekly Trend")

trend_df = df.copy()

trend_df["Week"] = trend_df["DATE"].dt.strftime("%d %b")

trend_df["Total Installed"] = (
    trend_df.get("ADMIN INSTALLED", 0) +
    trend_df.get("ACAD INSTALLED", 0)
)

st.line_chart(
    trend_df.set_index("Week")["Total Installed"]
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

# ==================================================
# TABLE DISPLAY
# ==================================================
st.markdown("## 📋 Raw Data")

display_df = df.copy()

# Format DATE nicely
display_df["DATE"] = display_df["DATE"].dt.strftime("%d %B %Y")

st.dataframe(
    display_df,
    use_container_width=True,
    height=600
)
