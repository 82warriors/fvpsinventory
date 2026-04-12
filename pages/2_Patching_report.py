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
# LOAD DATA FUNCTION
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    raw_df = pd.read_csv(URL, header=None, dtype=str)

    # Detect header row dynamically
    header_row = None
    for i in range(len(raw_df)):
        row = raw_df.iloc[i].astype(str).str.upper()
        if "DATE" in row.values:
            header_row = i
            break

    if header_row is None:
        return pd.DataFrame()

    df = pd.read_csv(URL, header=header_row, dtype=str)

    # Clean columns
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    return df


# ==================================================
# LOAD DATA
# ==================================================
df = load_data()

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
    st.error("❌ No data loaded. Check your Google Sheet.")
    st.stop()

required_cols = ["BrandModel", "Profile", "Status"]
missing = [col for col in required_cols if col not in df.columns]

if missing:
    st.error(f"❌ Missing columns: {missing}")
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

# Model filters (robust)
is_yoga = df["BrandModel"].str.contains("YOGA L13", na=False)
is_k14 = df["BrandModel"].str.contains("K14 GEN2", na=False)

# Profile filters
is_admin = df["Profile"] == "ADMIN"
is_acad = df["Profile"] == "ACAD"

# Status filter
is_installed = df["Status"] == "INSTALLED"

# --- Metrics ---
total_admin = df[is_yoga].shape[0]

total_admin_patched = df[
    is_yoga & is_admin & is_installed
].shape[0]

total_acad = df[
    is_k14 & is_acad
].shape[0]

total_acad_patched = df[
    is_k14 & is_acad & is_installed
].shape[0]

total_shared_admin = df[
    is_k14 & is_admin
].shape[0]

total_shared_admin_patched = df[
    is_k14 & is_admin & is_installed
].shape[0]

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
# PATCHING %
# ==================================================
st.markdown("### 📈 Patching Rates")

def calc_pct(patched, total):
    return round((patched / total * 100), 1) if total > 0 else 0

st.write(f"Admin: {calc_pct(total_admin_patched, total_admin)}%")
st.write(f"Acad: {calc_pct(total_acad_patched, total_acad)}%")
st.write(f"Shared Admin: {calc_pct(total_shared_admin_patched, total_shared_admin)}%")

# ==================================================
# OPTIONAL DEBUG (toggle)
# ==================================================
with st.expander("🔍 Debug Filters"):
    st.write("Yoga L13 count:", df[is_yoga].shape[0])
    st.write("K14 Gen2 count:", df[is_k14].shape[0])

# ==================================================
# DISPLAY TABLE
# ==================================================
st.markdown("## 📋 Raw Data")

display_df = df.copy()

if "DATE" in display_df.columns:
    parsed = pd.to_datetime(display_df["DATE"], errors="coerce")
    display_df["DATE"] = parsed.where(parsed.notna(), display_df["DATE"])
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
# DOWNLOAD BUTTON
# ==================================================
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "📥 Download Report",
    csv,
    "patching_report.csv",
    "text/csv"
)
