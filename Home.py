import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")

st.title("📊 FVPS Dashboard")

# ==================================================
# LOAD DATA (CLEAN + STABLE)
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"

    df = None

    # 🔍 Auto-detect header (silent)
    for i in range(6):
        temp = pd.read_csv(url, header=i)
        temp.columns = temp.columns.astype(str).str.strip()

        if "BrandModel" in temp.columns or "Brand Model" in temp.columns:
            df = temp
            break

    if df is None:
        st.error("❌ Could not detect correct header row")
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
    if "BrandModel" in df.columns:
        df["BrandModel"] = (
            df["BrandModel"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

    if "EquipmentType" in df.columns:
        df["EquipmentType"] = (
            df["EquipmentType"]
            .astype(str)
            .str.title()
            .str.strip()
        )

    # Convert dates safely
    for col in ["EndDate", "StartDate", "Last Updated"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Remove completely empty rows (important)
    df = df.dropna(how="all")

    return df


df = load_data()

# ==================================================
# REFRESH BUTTON
# ==================================================
if st.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# KPI CALCULATIONS
# ==================================================
today = pd.Timestamp.today()

if "EndDate" in df.columns:
    expired = df[df["EndDate"] < today]
    expiring = df[
        (df["EndDate"] >= today) &
        (df["EndDate"] <= today + pd.Timedelta(days=30))
    ]
else:
    expired = expiring = pd.DataFrame()

total_devices = len(df)
expired_count = len(expired)
expiring_count = len(expiring)
unique_models = df["BrandModel"].nunique() if "BrandModel" in df.columns else 0

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
        eq_chart = (
            df["EquipmentType"]
            .value_counts()
            .sort_values(ascending=False)
        )
        st.bar_chart(eq_chart)
    else:
        st.info("No EquipmentType data")

# Expiry Trend (sorted correctly)
with colB:
    st.markdown("### Expiry Timeline")

    if "EndDate" in df.columns:
        expiry_chart = (
            df.dropna(subset=["EndDate"])
            .groupby(df["EndDate"].dt.to_period("M"))
            .size()
            .sort_index()
        )

        expiry_chart.index = expiry_chart.index.astype(str)
        st.line_chart(expiry_chart)
    else:
        st.info("No EndDate data")

# ==================================================
# TOP MODELS
# ==================================================
st.markdown("## 🏆 Top Equipment Models")

if "BrandModel" in df.columns:
    top_models = (
        df["BrandModel"]
        .value_counts()
        .reset_index()
        .head(10)
    )
    top_models.columns = ["BrandModel", "Count"]

    st.dataframe(top_models, use_container_width=True, hide_index=True)
else:
    st.info("No BrandModel data")

# ==================================================
# RECENTLY UPDATED
# ==================================================
if "Last Updated" in df.columns:
    st.markdown("## 🕒 Recently Updated")

    recent = (
        df.sort_values("Last Updated", ascending=False)
        .dropna(subset=["Last Updated"])
        .head(10)
    )

    st.dataframe(recent, use_container_width=True, hide_index=True)
