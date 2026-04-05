import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")

st.title("📊 FVPS IT Management Dashboard")
st.caption("Real-time monitoring of FVPS IT infrastructure • Auto-updated from central data source")

# ==================================================
# 🏫 OVERVIEW (NEW UX SECTION)
# ==================================================
st.markdown("""
## 🏫 System Overview

This dashboard provides a real-time view of the school's IT environment.

It helps to monitor:

- 📦 **Inventory Status** – Total devices, active usage, faulty equipment  
- 🧯 **Fault Monitoring** – Devices and locations with issues  
- 🔄 **Patching Compliance** – Weekly update and security status  
- 📊 **Operational Insights** – Trends to support planning and decisions  

Use the filters and charts below to explore system performance.
""")

st.divider()

# ==================================================
# 📌 KPI SECTION
# ==================================================
st.markdown("## 📌 System Health Summary")

total_devices = len(inventory_df)

status_col = inventory_df.get("Status", pd.Series(dtype=str)).astype(str)

active_count = status_col.str.contains("Active", case=False, na=False).sum()
faulty_count = status_col.str.contains("Fault", case=False, na=False).sum()

# PATCHING
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

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Devices", total_devices)
col2.metric("🟢 Active Devices", int(active_count))
col3.metric("🔴 Faulty Devices", int(faulty_count))
col4.metric(
    "📊 Patching Compliance",
    f"{latest_patching}%",
    help="Percentage of devices updated to latest patch level"
)

st.divider()

# ==================================================
# 🔍 FILTERS
# ==================================================
st.markdown("## 🔍 Filters")

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

st.divider()

# ==================================================
# 📊 CHARTS
# ==================================================
st.markdown("## 📊 Operational Insights")

col1, col2 = st.columns(2)

if "EquipmentType" in filtered_df.columns:
    fig1 = px.pie(filtered_df, names="EquipmentType", title="Device Distribution")
    col1.plotly_chart(fig1, use_container_width=True)

if "Status" in filtered_df.columns:
    status_df = filtered_df["Status"].value_counts().reset_index()
    status_df.columns = ["Status", "Count"]

    fig2 = px.bar(status_df, x="Status", y="Count", text="Count", title="Device Status Overview")
    col2.plotly_chart(fig2, use_container_width=True)

st.divider()

# ==================================================
# 📈 PATCHING
# ==================================================
if not patching_df.empty and "Week" in patching_df.columns:
    st.markdown("## 🔄 Patching Performance")

    fig3 = px.line(
        patching_df,
        x="Week",
        y="Compliance %",
        markers=True
    )

    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ==================================================
# 🧠 INSIGHTS
# ==================================================
st.markdown("## 🧠 Key Observations")

if latest_patching < 80:
    st.warning("⚠️ Patching compliance is below 80%. Devices may be vulnerable and require updates.")

if total_devices > 0 and faulty_count > total_devices * 0.1:
    st.error("🚨 A high number of faulty devices detected. Immediate attention may be required.")

if total_devices > 0 and active_count / total_devices > 0.9:
    st.success("✅ Most systems are functioning normally. Overall system health is good.")

# ==================================================
# DEBUG
# ==================================================
with st.expander("🔧 Debug Data"):
    st.write("Inventory Columns:", list(inventory_df.columns))
    st.write("Patching Columns:", list(patching_df.columns))
