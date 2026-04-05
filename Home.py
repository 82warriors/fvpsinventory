import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="FVPS Dashboard", layout="wide")
st.title("📊 FVPS IT Management Dashboard")

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data(ttl=120)
def load_data():
    # 🔁 REPLACE WITH YOUR GOOGLE SHEET / CSV
    inventory_url = "https://docs.google.com/spreadsheets/d/1lmCotLUgTLJBKska2y7od2LTPT_qooIFS0_zyVnRI0A/edit?gid=1895613573#gid=1895613573&fvid=520134364"
    patching_url = "https://docs.google.com/spreadsheets/d/1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE/edit?gid=0#gid=0"

    inventory_df = pd.read_csv(inventory_url)
    patching_df = pd.read_csv(patching_url)

    return inventory_df, patching_df

inventory_df, patching_df = load_data()

# ==================================================
# DATA CLEANING (SAFE DEFAULTS)
# ==================================================
inventory_df.columns = inventory_df.columns.str.strip()
patching_df.columns = patching_df.columns.str.strip()

# ==================================================
# KPI CALCULATIONS
# ==================================================
total_devices = len(inventory_df)

active_count = len(inventory_df[inventory_df["Status"] == "🟢 Active"])
faulty_count = len(inventory_df[inventory_df["Status"].isin(["🔴 Faulty", "Faulty"])])

# ---- PATCHING FORMULA (YOUR CUSTOM LOGIC) ----
patching_df.fillna(0, inplace=True)

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
).round(2)

latest_patching = patching_df["Compliance %"].iloc[-1] if not patching_df.empty else 0

# ==================================================
# KPI DISPLAY
# ==================================================
st.subheader("📌 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Devices", total_devices)
col2.metric("🟢 Active Devices", active_count)
col3.metric("🔴 Faulty Devices", faulty_count)
col4.metric("📊 Patching Compliance", f"{latest_patching}%")

# ==================================================
# FILTERS
# ==================================================
st.divider()
st.subheader("🔍 Filters")

col1, col2 = st.columns(2)

if "Level" in inventory_df.columns:
    level_filter = col1.selectbox("Select Level", ["All"] + sorted(inventory_df["Level"].dropna().unique()))
else:
    level_filter = "All"

if "EquipmentType" in inventory_df.columns:
    type_filter = col2.selectbox("Select Equipment Type", ["All"] + sorted(inventory_df["EquipmentType"].dropna().unique()))
else:
    type_filter = "All"

filtered_df = inventory_df.copy()

if level_filter != "All":
    filtered_df = filtered_df[filtered_df["Level"] == level_filter]

if type_filter != "All":
    filtered_df = filtered_df[filtered_df["EquipmentType"] == type_filter]

# ==================================================
# CHARTS SECTION
# ==================================================
st.divider()
st.subheader("📊 Visual Insights")

# ---- PIE CHART: EQUIPMENT DISTRIBUTION ----
col1, col2 = st.columns(2)

if "EquipmentType" in filtered_df.columns:
    pie_fig = px.pie(
        filtered_df,
        names="EquipmentType",
        title="Device Distribution"
    )
    col1.plotly_chart(pie_fig, use_container_width=True)

# ---- BAR CHART: STATUS ----
status_df = filtered_df["Status"].value_counts().reset_index()
status_df.columns = ["Status", "Count"]

bar_fig = px.bar(
    status_df,
    x="Status",
    y="Count",
    title="Device Status Overview",
    text="Count"
)

col2.plotly_chart(bar_fig, use_container_width=True)

# ==================================================
# PATCHING TREND
# ==================================================
st.divider()
st.subheader("📈 Patching Compliance Trend")

if "Week" in patching_df.columns:
    line_fig = px.line(
        patching_df,
        x="Week",
        y="Compliance %",
        markers=True,
        title="Weekly Patching Compliance"
    )
    st.plotly_chart(line_fig, use_container_width=True)

# ==================================================
# FAULT ANALYSIS
# ==================================================
st.divider()
st.subheader("🧯 Fault Analysis")

col1, col2 = st.columns(2)

# Fault by Location
if "Location" in filtered_df.columns:
    fault_loc = filtered_df[filtered_df["Status"].isin(["🔴 Faulty", "Faulty"])]
    fault_loc = fault_loc["Location"].value_counts().reset_index()
    fault_loc.columns = ["Location", "Count"]

    fig_fault_loc = px.bar(
        fault_loc,
        x="Location",
        y="Count",
        title="Faults by Location"
    )

    col1.plotly_chart(fig_fault_loc, use_container_width=True)

# Fault by Equipment
if "EquipmentType" in filtered_df.columns:
    fault_type = filtered_df[filtered_df["Status"].isin(["🔴 Faulty", "Faulty"])]
    fault_type = fault_type["EquipmentType"].value_counts().reset_index()
    fault_type.columns = ["EquipmentType", "Count"]

    fig_fault_type = px.bar(
        fault_type,
        x="EquipmentType",
        y="Count",
        title="Faults by Equipment Type"
    )

    col2.plotly_chart(fig_fault_type, use_container_width=True)

# ==================================================
# SMART INSIGHTS
# ==================================================
st.divider()
st.subheader("🧠 System Insights")

if latest_patching < 80:
    st.warning("⚠️ Patching compliance is below 80%! Immediate action recommended.")

if faulty_count > (0.1 * total_devices):
    st.error("🚨 High number of faulty devices detected!")

if active_count / total_devices > 0.9:
    st.success("✅ System is in healthy condition!")

# ==================================================
# FOOTER
# ==================================================
st.caption("FVPS IT Dashboard • Auto-updated")
