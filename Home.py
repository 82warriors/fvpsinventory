import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")

st.title("📊 FVPS Dashboard")

# ==================================================
# LOAD DATA (BULLETPROOF)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"

    # Try default
    df = pd.read_csv(url)
    df.columns = df.columns.astype(str).str.strip()

    # Try alternative header if needed
    if "BrandModel" not in df.columns:
        df = pd.read_csv(url, header=3)
        df.columns = df.columns.astype(str).str.strip()

    # Try header=4 if still not found
    if "BrandModel" not in df.columns:
        df = pd.read_csv(url, header=4)
        df.columns = df.columns.astype(str).str.strip()

    # If still missing → show debug and stop
    if "BrandModel" not in df.columns:
        st.error("❌ Unable to detect 'BrandModel' column")
        st.write("Detected columns:", df.columns.tolist())
        st.stop()

    # ==================================================
    # NORMALIZE COLUMN NAMES
    # ==================================================
    df = df.rename(columns={
        "Brand Model": "BrandModel",
        "Equipment Type": "EquipmentType",
        "End Date": "EndDate",
        "Start Date": "StartDate",
        "Last Updated": "Last Updated"
    })

    # ==================================================
    # CLEAN DATA
    # ==================================================
    df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()

    if "EquipmentType" in df.columns:
        df["EquipmentType"] = df["EquipmentType"].astype(str).str.title().str.strip()

    # Convert dates safely
    if "EndDate" in df.columns:
        df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")

    if "StartDate" in df.columns:
        df["StartDate"] = pd.to_datetime(df["StartDate"], errors="coerce")

    if "Last Updated" in df.columns:
        df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")

    return df


df = load_data()

# ==================================================
# KPI CALCULATIONS
# ==================================================
today = pd.Timestamp.today()

expired = df[df["EndDate"] < today] if "EndDate" in df.columns else pd.DataFrame()
expiring = df[df["EndDate"] <= today + pd.Timedelta(days=30)] if "EndDate" in df.columns else pd.DataFrame()

total_devices = len(df)
expired_count = len(expired)
expiring_count = len(expiring)
unique_models = df["BrandModel"].nunique()

# ==================================================
# KPI SECTION
# ==================================================
st.markdown("## 📊 Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Devices", total_devices)
col2.metric("Expired", expired_count)
col3.metric("Expiring (30 Days)", expiring_count)
col4.metric("Unique Models", unique_models)

# ==================================================
# ALERT
# ==================================================
if expiring_count > 0:
    st.warning(f"⚠️ {expiring_count} devices expiring within 30 days")

# ==================================================
# CHARTS
# ==================================================
st.markdown("## 📈 Insights")

colA, colB = st.columns(2)

# Equipment Distribution
with colA:
    st.markdown("### Equipment Distribution")

    if "EquipmentType" in df.columns:
        eq_chart = df["EquipmentType"].value_counts()
        st.bar_chart(eq_chart)
    else:
        st.info("No EquipmentType data")

# Expiry Trend
with colB:
    st.markdown("### Expiry Timeline")

    if "EndDate" in df.columns:
        expiry_chart = (
            df.dropna(subset=["EndDate"])
            .groupby(df["EndDate"].dt.to_period("M"))
            .size()
        )

        expiry_chart.index = expiry_chart.index.astype(str)
        st.line_chart(expiry_chart)
    else:
        st.info("No EndDate data")

# ==================================================
# TOP MODELS
# ==================================================
st.markdown("## 🏆 Top Equipment Models")

top_models = df["BrandModel"].value_counts().head(10)
st.dataframe(top_models, use_container_width=True)

# ==================================================
# RECENTLY UPDATED
# ==================================================
if "Last Updated" in df.columns:
    st.markdown("## 🕒 Recently Updated")

    recent = df.sort_values("Last Updated", ascending=False).head(10)
    st.dataframe(recent, use_container_width=True)
