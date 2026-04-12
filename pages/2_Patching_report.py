import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")
st.title("🛠 Patching Report")

# ==================================================
# CONNECT TO GOOGLE SHEETS
# ==================================================
conn = st.connection("gsheets", type=GSheetsConnection)

# ==================================================
# LOAD ALL WORKSHEETS 🔥
# ==================================================
@st.cache_data(ttl=120)
def load_all_sheets():
    spreadsheet = conn.open()  # open full workbook

    all_dfs = []

    for ws in spreadsheet.worksheets():  # 🔥 key part
        df = ws.get_as_df()

        if df.empty:
            continue

        df.columns = df.columns.str.strip()

        # Skip sheets without required structure
        required_cols = {"BrandModel", "Profile", "Status"}
        if not required_cols.issubset(df.columns):
            continue

        df["SOURCE_SHEET"] = ws.title  # track source
        all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame()

    combined = pd.concat(all_dfs, ignore_index=True)
    return combined


# ==================================================
# LOAD DATA
# ==================================================
df = load_all_sheets()

# ==================================================
# REFRESH
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# VALIDATION
# ==================================================
if df.empty:
    st.error("❌ No valid data found in any worksheet")
    st.stop()

# ==================================================
# CLEAN DATA
# ==================================================
df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()
df["Profile"] = df["Profile"].astype(str).str.upper().str.strip()
df["Status"] = df["Status"].astype(str).str.upper().str.strip()

# ==================================================
# KPI CALCULATIONS
# ==================================================
st.markdown("## 📊 Overview")

is_yoga = df["BrandModel"].str.contains("YOGA L13", na=False)
is_k14 = df["BrandModel"].str.contains("K14 GEN2", na=False)

is_admin = df["Profile"] == "ADMIN"
is_acad = df["Profile"] == "ACAD"
is_installed = df["Status"] == "INSTALLED"

total_admin = df[is_yoga].shape[0]
total_admin_patched = df[is_yoga & is_admin & is_installed].shape[0]

total_acad = df[is_k14 & is_acad].shape[0]
total_acad_patched = df[is_k14 & is_acad & is_installed].shape[0]

total_shared_admin = df[is_k14 & is_admin].shape[0]
total_shared_admin_patched = df[is_k14 & is_admin & is_installed].shape[0]

# ==================================================
# DISPLAY KPIs
# ==================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Admin (Yoga L13)", total_admin)
    st.metric("Admin Patched", total_admin_patched)

with col2:
    st.metric("Total Acad (K14 Gen2)", total_acad)
    st.metric("Acad Patched", total_acad_patched)

with col3:
    st.metric("Total Shared Admin", total_shared_admin)
    st.metric("Shared Admin Patched", total_shared_admin_patched)

# ==================================================
# SHOW SOURCE SHEETS (DEBUG 🔥)
# ==================================================
st.markdown("### 📂 Sheets Loaded")
st.write(df["SOURCE_SHEET"].unique())

# ==================================================
# TABLE
# ==================================================
st.markdown("## 📋 Combined Data")
st.dataframe(df, use_container_width=True, height=600)
