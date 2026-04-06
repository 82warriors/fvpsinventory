import streamlit as st
import pandas as pd

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Tracking upgrade completion for selected device models")

# ==================================================
# CONFIG
# ==================================================
URL = "https://docs.google.com/spreadsheets/d/1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0/export?format=csv&gid=1946114847"

TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

# ==================================================
# LOAD DATA (BULLETPROOF)
# ==================================================
@st.cache_data(ttl=120)
def load_data():

    raw = pd.read_csv(URL, header=None, dtype=str)

    header_row = None

    # 🔍 Detect header row dynamically
    for i in range(len(raw)):
        row = raw.iloc[i].astype(str).str.upper()

        if "BRANDMODEL" in row.values or "MODEL" in row.values:
            header_row = i
            break

    if header_row is None:
        st.error("❌ Cannot detect header row")
        st.stop()

    df = pd.read_csv(URL, header=header_row)

    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    return df


df = load_data()

# ==================================================
# 🔄 REFRESH
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ==================================================
# CLEAN DATA
# ==================================================
# Normalize BrandModel
if "BrandModel" in df.columns:
    df["BrandModel"] = df["BrandModel"].astype(str).str.upper().str.strip()

# Detect Status column
status_col = None
for col in df.columns:
    if "STATUS" in col.upper():
        status_col = col
        break

if status_col is None:
    st.error("❌ No Status column found")
    st.write("Detected columns:", df.columns.tolist())
    st.stop()

# Normalize Status values
df[status_col] = df[status_col].astype(str).str.strip().str.title()

# ==================================================
# FILTER TARGET MODELS
# ==================================================
df_filtered = df[df["BrandModel"].isin(TARGET_MODELS)]

# Remove empty rows
df_filtered = df_filtered.dropna(subset=["BrandModel"])

# ==================================================
# COMPUTE SUMMARY
# ==================================================
summary = (
    df_filtered
    .groupby(["BrandModel", status_col])
    .size()
    .unstack(fill_value=0)
)

# Ensure columns exist
for col in ["Completed", "Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()

# ==================================================
# ADD PERCENTAGE
# ==================================================
summary["Total"] = summary["Completed"] + summary["Not Completed"]

summary["Completion %"] = (
    summary["Completed"] / summary["Total"]
).fillna(0) * 100

summary["Completion %"] = summary["Completion %"].round(1)

# ==================================================
# KPI
# ==================================================
st.markdown("## 📊 Overview")

total_completed = int(summary["Completed"].sum())
total_not_completed = int(summary["Not Completed"].sum())
total_devices = total_completed + total_not_completed

completion_rate = (total_completed / total_devices * 100) if total_devices > 0 else 0

c1, c2, c3 = st.columns(3)

c1.metric("✅ Completed", total_completed)
c2.metric("❌ Not Completed", total_not_completed)
c3.metric("📈 Completion Rate", f"{completion_rate:.1f}%")

# ==================================================
# TABLE
# ==================================================
st.markdown("## 📋 Upgrade Summary")

st.dataframe(
    summary[["BrandModel", "Completed", "Not Completed", "Completion %"]],
    use_container_width=True,
    hide_index=True
)

# ==================================================
# CHART
# ==================================================
st.markdown("## 📈 Upgrade Progress")

chart_df = summary.set_index("BrandModel")[["Completed", "Not Completed"]]
st.bar_chart(chart_df)

# ==================================================
# PROGRESS BARS (NICE TOUCH)
# ==================================================
st.markdown("## 🔄 Progress by Model")

for _, row in summary.iterrows():
    st.write(f"**{row['BrandModel']}**")
    st.progress(row["Completion %"] / 100)

# ==================================================
# RAW DATA
# ==================================================
with st.expander("🔍 View Raw Data"):
    st.dataframe(df_filtered, use_container_width=True)
