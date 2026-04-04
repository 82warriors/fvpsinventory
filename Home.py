import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")

st.title("📊 FVPS Inventory Dashboard")

# ==================================================
# LOAD DATA (ROBUST)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"

    df = pd.read_csv(url)
    df.columns = df.columns.astype(str).str.strip()

    # Fix header row if needed
    if "BrandModel" not in df.columns:
        df = pd.read_csv(url, header=3)
        df.columns = df.columns.astype(str).str.strip()

    # Final check
    if "BrandModel" not in df.columns:
        st.error("❌ Unable to detect correct header row.")
        st.write("Detected columns:", df.columns.tolist())
        st.stop()

    # Normalize column names
    df = df.rename(columns={
        "Brand Model": "BrandModel",
        "Equipment Type": "EquipmentType",
        "Start Date": "StartDate",
        "End Date": "EndDate"
    })

    # Clean data
    df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()

    if "EquipmentType" in df.columns:
        df["EquipmentType"] = df["EquipmentType"].astype(str).str.title().str.strip()

    # Dates
    if "EndDate" in df.columns:
        df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")

    return df


df = load_data()

# ==================================================
# KPI SECTION
# ==================================================
st.markdown("## 📊 Key Metrics")

today = pd.Timestamp.today()

expired = df[df["EndDate"] < today]
expiring_30 = df[df["EndDate"] <= today + pd.Timedelta(days=30)]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Devices", len(df))
col2.metric("Expired", len(expired))
col3.metric("Expiring (30 Days)", len(expiring_30))
col4.metric("Unique Models", df["BrandModel"].nunique())

# ==================================================
# ALERT
# ==================================================
if len(expiring_30) > 0:
    st.warning(f"⚠️ {len(expiring_30)} devices are expiring within 30 days")

# ==================================================
# CHARTS SECTION
# ==================================================
st.markdown("## 📈 Insights")

colA, colB = st.columns(2)

# Equipment Distribution
with colA:
    st.markdown("### Equipment Distribution")

    if "EquipmentType" in df.columns:
        eq_chart = (
            df["EquipmentType"]
            .value_counts()
            .reset_index()
        )
        eq_chart.columns = ["EquipmentType", "Count"]

        st.bar_chart(eq_chart.set_index("EquipmentType"))

# Expiry Trend
with colB:
    st.markdown("### Expiry Timeline")

    expiry_chart = (
        df.dropna(subset=["EndDate"])
        .groupby(df["EndDate"].dt.to_period("M"))
        .size()
        .reset_index(name="Count")
    )

    expiry_chart["EndDate"] = expiry_chart["EndDate"].astype(str)

    st.line_chart(expiry_chart.set_index("EndDate"))

# ==================================================
# TOP MODELS TABLE
# ==================================================
st.markdown("## 🏆 Top Equipment Models")

top_models = (
    df["BrandModel"]
    .value_counts()
    .reset_index()
    .head(10)
)

top_models.columns = ["BrandModel", "Count"]

st.dataframe(top_models, use_container_width=True)

# ==================================================
# RECENTLY UPDATED
# ==================================================
if "Last Updated" in df.columns:
    st.markdown("## 🕒 Recently Updated")

    recent = df.copy()
    recent["Last Updated"] = pd.to_datetime(recent["Last Updated"], errors="coerce")

    recent = recent.sort_values(by="Last Updated", ascending=False).head(10)

    st.dataframe(recent, use_container_width=True)
