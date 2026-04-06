import streamlit as st
import pandas as pd
import requests

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Latest upgrade status based on most recent worksheet")

# ==================================================
# CONFIG
# ==================================================
SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"

TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

# ==================================================
# 🔍 GET ALL SHEETS (GIDs)
# ==================================================
@st.cache_data(ttl=300)
def get_sheet_gids():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:json"
    res = requests.get(url)

    text = res.text[47:-2]  # remove wrapper
    data = eval(text)

    sheets = data["table"]["cols"]  # fallback

    # Better way: scrape sheet names + gids
    # Simpler: manually define known gids if needed

    return data

# ==================================================
# LOAD SINGLE SHEET
# ==================================================
def load_sheet(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"

    df = pd.read_csv(url, dtype=str)

    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    return df

# ==================================================
# 🔥 MANUAL LATEST GID (RECOMMENDED)
# ==================================================
# ⚠️ BEST PRACTICE: update this when new sheet added
LATEST_GID = "1946114847"

df = load_sheet(LATEST_GID)

# ==================================================
# CLEAN DATA
# ==================================================
df.columns = df.columns.str.upper()

if "MODEL" not in df.columns or "IPU STATUS" not in df.columns:
    st.error("❌ Required columns not found")
    st.write(df.columns.tolist())
    st.stop()

# Normalize
df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()

# ==================================================
# FILTER TARGET MODELS
# ==================================================
df = df[df["MODEL"].isin(TARGET_MODELS)]

# Remove blanks
df = df.dropna(subset=["MODEL"])

# ==================================================
# COMPUTE SUMMARY
# ==================================================
summary = (
    df.groupby(["MODEL", "IPU STATUS"])
    .size()
    .unstack(fill_value=0)
)

# Ensure columns
for col in ["Completed", "Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()

# ==================================================
# ADD %
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

total = total_completed + total_not_completed
rate = (total_completed / total * 100) if total > 0 else 0

c1, c2, c3 = st.columns(3)

c1.metric("✅ Completed", total_completed)
c2.metric("❌ Not Completed", total_not_completed)
c3.metric("📈 Completion Rate", f"{rate:.1f}%")

# ==================================================
# TABLE
# ==================================================
st.markdown("## 📋 Upgrade Summary")

st.dataframe(
    summary[["MODEL", "Completed", "Not Completed", "Completion %"]],
    use_container_width=True,
    hide_index=True
)

# ==================================================
# CHART
# ==================================================
st.markdown("## 📈 Upgrade Progress")

chart_df = summary.set_index("MODEL")[["Completed", "Not Completed"]]
st.bar_chart(chart_df)

# ==================================================
# PROGRESS BAR
# ==================================================
st.markdown("## 🔄 Progress by Model")

for _, row in summary.iterrows():
    st.write(f"**{row['MODEL']}**")
    st.progress(row["Completion %"] / 100)

# ==================================================
# RAW DATA
# ==================================================
with st.expander("🔍 Raw Data"):
    st.dataframe(df, use_container_width=True)
