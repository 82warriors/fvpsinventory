import streamlit as st
import pandas as pd
import requests
import re

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")
st.title("🛠 Patching Report")

# ==================================================
# GOOGLE SHEET CONFIG
# ==================================================
SHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

# ==================================================
# LOAD ALL WORKSHEETS (always includes new ones)
# ==================================================
@st.cache_data(ttl=120)
def load_all_sheets():
    # Get spreadsheet metadata (list of sheets)
    meta_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?"
    meta_text = requests.get(meta_url).text

    # Extract sheet names with regex
    sheet_names = re.findall(r'"(.*?)"', meta_text)
    all_dfs = []

    for sheet_name in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
            df = pd.read_csv(url)
            if df.empty:
                continue
            df.columns = df.columns.str.strip()
            required_cols = {"BrandModel", "Profile", "Status"}
            if not required_cols.issubset(df.columns):
                continue
            df["SOURCE_SHEET"] = sheet_name
            all_dfs.append(df)
        except Exception:
            continue

    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs, ignore_index=True)

# ==================================================
# LOAD DATA
# ==================================================
df = load_all_sheets()

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
# FILTER HELPER
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
    st.metric("Total Shared Admin (K14 Gen2)", total_shared_admin)
    st.metric("Shared Admin Patched", total_shared_admin_patched)

# ==================================================
# PATCH RATES
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
# TABLE VIEW
# ==================================================
st.markdown("## 📋 Combined Data")
st.dataframe(df, use_container_width=True, height=600)
