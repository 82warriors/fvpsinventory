import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")

# ==================================================
# 🎨 UI STYLING
# ==================================================
st.markdown("""
<style>
.main {background-color: #f5f7fa;}

.kpi-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
    text-align: center;
}

.kpi-title {
    font-size: 14px;
    color: gray;
}

.kpi-value {
    font-size: 30px;
    font-weight: bold;
    color: #2e7d32;
}

.section {
    margin-top: 25px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# TITLE
# ==================================================
st.title("📊 FVPS Dashboard")

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"

    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()

    # Fix header issue
    if "BrandModel" not in df.columns:
        df = pd.read_csv(url, header=3)
        df.columns = df.columns.str.strip()

    # Normalize
    df = df.rename(columns={
        "Brand Model": "BrandModel",
        "Equipment Type": "EquipmentType",
        "End Date": "EndDate"
    })

    # Clean
    df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()

    if "EquipmentType" in df.columns:
        df["EquipmentType"] = df["EquipmentType"].astype(str).str.title()

    df["EndDate"] = pd.to_datetime(df.get("EndDate"), errors="coerce")

    return df


df = load_data()

# ==================================================
# KPI CALCULATIONS
# ==================================================
today = pd.Timestamp.today()

expired = df[df["EndDate"] < today]
expiring = df[df["EndDate"] <= today + pd.Timedelta(days=30)]

total_devices = len(df)
expired_count = len(expired)
expiring_count = len(expiring)
unique_models = df["BrandModel"].nunique()

# ==================================================
# KPI SECTION
# ==================================================
st.markdown("## 📊 Overview")

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">Total Devices</div>
    <div class="kpi-value">{total_devices}</div>
</div>
""", unsafe_allow_html=True)

c2.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">Expired</div>
    <div class="kpi-value">{expired_count}</div>
</div>
""", unsafe_allow_html=True)

c3.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">Expiring (30 Days)</div>
    <div class="kpi-value">{expiring_count}</div>
</div>
""", unsafe_allow_html=True)

c4.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">Unique Models</div>
    <div class="kpi-value">{unique_models}</div>
</div>
""", unsafe_allow_html=True)

# ==================================================
# ALERT
# ==================================================
if expiring_count > 0:
    st.warning(f"⚠️ {expiring_count} devices expiring within 30 days")

# ==================================================
# CHARTS
# ==================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown("## 📈 Insights")

col1, col2 = st.columns(2)

# Equipment Distribution
with col1:
    st.markdown("### Equipment Distribution")

    if "EquipmentType" in df.columns:
        eq_chart = df["EquipmentType"].value_counts()
        st.bar_chart(eq_chart)

# Expiry Trend
with col2:
    st.markdown("### Expiry Timeline")

    expiry_chart = (
        df.dropna(subset=["EndDate"])
        .groupby(df["EndDate"].dt.to_period("M"))
        .size()
    )

    expiry_chart.index = expiry_chart.index.astype(str)

    st.line_chart(expiry_chart)

st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# TOP MODELS
# ==================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown("## 🏆 Top Equipment Models")

top_models = df["BrandModel"].value_counts().head(10)
st.dataframe(top_models, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# RECENT UPDATES
# ==================================================
if "Last Updated" in df.columns:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown("## 🕒 Recently Updated")

    df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")

    recent = df.sort_values("Last Updated", ascending=False).head(10)

    st.dataframe(recent, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
