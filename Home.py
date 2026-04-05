import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")
st.title("📊 FVPS IT Management Dashboard")

# ==================================================
# GOOGLE SHEET CONFIG
# ==================================================
FILE_ID = "1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A"
EXCEL_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"

# ==================================================
# LOAD DATA (ROBUST + SAFE)
# ==================================================
@st.cache_data(ttl=300)
def load_data():
    try:
        xls = pd.ExcelFile(EXCEL_URL)

        inventory_df = pd.DataFrame()
        patching_df = pd.DataFrame()

        for sheet in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            df.columns = df.columns.astype(str).str.strip()

            # Auto-detect inventory
            if "Status" in df.columns:
                inventory_df = df.copy()

            # Auto-detect patching
            if "ADMIN INSTALLED" in df.columns:
                patching_df = df.copy()

        return inventory_df, patching_df

    except Exception as e:
        st.error("❌ Failed to load data from Google Sheets")
        st.exception(e)
        return pd.DataFrame(), pd.DataFrame()

inventory_df, patching_df = load_data()

# ==================================================
# CLEANING FUNCTIONS
# ==================================================
def clean_inventory(df):
    if df.empty:
        return df

    df = df.dropna(how="all")
    df.columns = df.columns.str.strip()

    rename_map = {
        "Equipment Type": "EquipmentType",
        "equipmenttype": "EquipmentType",
        "STATUS": "Status",
        "status": "Status",
        "LOCATION": "Location",
        "location": "Location",
        "LEVEL": "Level",
        "level": "Level"
    }

    df.rename(columns=rename_map, inplace=True)
    return df


def clean_patching(df):
    if df.empty:
        return df

    df = df.dropna(how="all")
    df.fillna(0, inplace=True)
    return df


inventory_df = clean_inventory(inventory_df)
patching_df = clean_patching(patching_df)

# ==================================================
# KPI CALCULATIONS
# ==================================================
total_devices = len(inventory_df)

status_col = inventory_df.get("Status", pd.Series(dtype=str)).astype(str)

active_count = status_col.str.contains("Active", case=False, na=False).sum()
faulty_count = status_col.str.contains("Fault", case=False, na=False).sum()

# ---- PATCHING ----
if not patching_df.empty:

    patching_df["Installed"] = (
        patching_df.get("ADMIN INSTALLED", 0) +
        patching_df.get("ACAD INSTALLED", 0)
    )

    patching_df["Total"] = (
        patching_df.get("ADMIN SCCM EPP > 4 wks", 0) +
        patching_df.get("ACAD SCCM EPP > 4 wks", 0) +
        patching_df.get("ADMIN NOT CONNECTED", 0) +
        patching_df.get("ACAD NOT CONNECTED", 0) +
        patching_df.get("ADMIN REQUIRED", 0) +
        patching_df.get("ACAD REQUIRED", 0) +
        patching_df.get("ADMIN UNKNOWN", 0) +
        patching_df.get("ACAD UNKNOWN", 0) +
        patching_df.get("E-EXAM", 0) +
        patching_df.get("FAULTY", 0)
    )

    patching_df["Compliance %"] = (
        (patching_df["Installed"] / patching_df["Total"]) * 100
    ).fillna(0).round(2)

    latest_patching = patching_df["Compliance %"].iloc[-1]

else:
    latest_patching = 0

# ==================================================
# KPI DISPLAY
# ==================================================
st.subheader("📌 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Devices", total_devices)
col2.metric("🟢 Active Devices", int(active_count))
col3.metric("🔴 Faulty Devices", int(faulty_count))
col4.metric("📊 Patching Compliance", f"{latest_patching}%")

# ==================================================
# FILTERS
# ==================================================
st.divider()
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

level_filter = "All"
type_filter = "All"

if "Level" in inventory_df.columns:
    level_filter = col1.selectbox(
        "Select Level",
        ["All"] + sorted(inventory_df["Level"].dropna().astype(str).unique())
    )

if "EquipmentType" in inventory_df.columns:
    type_filter = col2.selectbox(
        "Select Equipment Type",
        ["All"] + sorted(inventory_df["EquipmentType"].dropna().astype(str).unique())
    )

filtered_df = inventory_df.copy()

if level_filter != "All":
    filtered_df = filtered_df[filtered_df["Level"].astype(str) == level_filter]

if type_filter != "All":
    filtered_df = filtered_df[filtered_df["EquipmentType"].astype(str) == type_filter]

# ==================================================
# CHARTS
# ==================================================
st.divider()
st.subheader("📊 Visual Insights")

col1, col2 = st.columns(2)

# Pie Chart
if "EquipmentType" in filtered_df.columns:
    fig1 = px.pie(filtered_df, names="EquipmentType", title="Device Distribution")
    col1.plotly_chart(fig1, use_container_width=True)

# Bar Chart
if "Status" in filtered_df.columns:
    status_df = filtered_df["Status"].value_counts().reset_index()
    status_df.columns = ["Status", "Count"]

    fig2 = px.bar(status_df, x="Status", y="Count", text="Count", title="Device Status Overview")
    col2.plotly_chart(fig2, use_container_width=True)

# ==================================================
# PATCHING TREND
# ==================================================
if not patching_df.empty and "Week" in patching_df.columns:
    st.divider()
    st.subheader("📈 Patching Compliance Trend")

    fig3 = px.line(
        patching_df,
        x="Week",
        y="Compliance %",
        markers=True
    )

    st.plotly_chart(fig3, use_container_width=True)

# ==================================================
# SMART INSIGHTS
# ==================================================
st.divider()
st.subheader("🧠 System Insights")

if latest_patching < 80:
    st.warning("⚠️ Patching compliance is below 80%")

if total_devices > 0 and faulty_count > total_devices * 0.1:
    st.error("🚨 High number of faulty devices")

if total_devices > 0 and active_count / total_devices > 0.9:
    st.success("✅ System is healthy")

# ==================================================
# DEBUG PANEL
# ==================================================
with st.expander("🔧 Debug Data"):
    st.write("Inventory Columns:", list(inventory_df.columns))
    st.write("Patching Columns:", list(patching_df.columns))
    st.write("Inventory Preview:", inventory_df.head())
    st.write("Patching Preview:", patching_df.head())
