import streamlit as st
import pandas as pd

st.set_page_config(page_title="FVPS Dashboard", layout="wide")

st.title("📊 FVPS Inventory Dashboard")

# =========================
# LOAD DATA
# =========================
@st.cache_data(ttl=120)
def load_inventory():
    url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/export?format=csv"
    df = pd.read_csv(url)

    df.columns = df.columns.str.strip()
    return df

df = load_inventory()

# =========================
# KPI SECTION
# =========================
st.markdown("## 📊 Key Metrics")

today = pd.Timestamp.today()

df["EndDate"] = pd.to_datetime(df["EndDate"], errors="coerce")

expired = df[df["EndDate"] < today]
expiring = df[df["EndDate"] <= today + pd.Timedelta(days=30)]

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Devices", len(df))
c2.metric("Expired", len(expired))
c3.metric("Expiring Soon", len(expiring))
c4.metric("Unique Models", df["BrandModel"].nunique())

# =========================
# CHART
# =========================
st.markdown("## 📈 Equipment Distribution")

chart_df = df["EquipmentType"].value_counts().reset_index()
chart_df.columns = ["EquipmentType", "Count"]

st.bar_chart(chart_df.set_index("EquipmentType"))

# =========================
# ALERT
# =========================
if len(expiring) > 0:
    st.warning(f"⚠️ {len(expiring)} devices expiring within 30 days")
