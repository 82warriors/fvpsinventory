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
# LOAD ALL WORKSHEETS
# ==================================================
@st.cache_data(ttl=120)
def load_all_sheets():
    spreadsheet = conn.open()
    all_dfs = []

    for ws in spreadsheet.worksheets():
        df = ws.get_as_df()

        if df.empty:
            continue

        df.columns = df.columns.str.strip()

        required_cols = {"BrandModel", "Profile", "Status"}
        if not required_cols.issubset(df.columns):
            continue

        df["SOURCE_SHEET"] = ws.title
        all_dfs.append(df)

    if not all_dfs:
        return pd.DataFrame()

    return pd.concat(all_dfs, ignore_index=True)

# ==================================================
# LOAD DATA
# ==================================================
df = load_all_sheets()

# ==================================================
# REFRESH BUTTON
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
# FILTER HELPERS (Reusable 🔥)
# ==================================================
def count_devices(model_keyword=None, profile=None, status=None):
    filtered = df.copy()

    if model_keyword:
        filtered = filtered[filtered["BrandModel"].str.contains(model_keyword, na=False)]

    if profile:
        filtered = filtered[filtered["Profile"] == profile]

    if status:
        filtered = filtered[filtered["Status"] == status]

    return filtered.shape[0]

# ==================================================
# KPI CALCULATIONS
# ==================================================
st.markdown("## 📊 Overview")

total_admin = count_devices("YOGA L13", "ADMIN")
total_admin_patched = count_devices("YOGA L13", "ADMIN", "INSTALLED")

total_acad = count_devices("K14 GEN2", "ACAD")
total_acad_patched = count_devices("K14 GEN2", "ACAD", "INSTALLED")

total_shared_admin = count_devices("K14 GEN2", "ADMIN")
total_shared_admin_patched = count_devices("K14 GEN2", "ADMIN", "INSTALLED")

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
# OPTIONAL: PATCH RATE (🔥 nice insight)
# ==================================================
st.markdown("## 📈 Patch Rates")

def rate(patched, total):
    return f"{(patched / total * 100):.1f}%" if total else "0%"

col4, col5, col6 = st.columns(3)

with col4:
    st.metric("Admin Patch Rate", rate(total_admin_patched, total_admin))

with col5:
    st.metric("Acad Patch Rate", rate(total_acad_patched, total_acad))

with col6:
    st.metric("Shared Admin Patch Rate", rate(total_shared_admin_patched, total_shared_admin))

# ==================================================
# DEBUG: SOURCE SHEETS
# ==================================================
st.markdown("### 📂 Sheets Loaded")
st.write(df["SOURCE_SHEET"].unique())

# ==================================================
# TABLE VIEW
# ==================================================
st.markdown("## 📋 Combined Data")
st.dataframe(df, use_container_width=True, height=600)
