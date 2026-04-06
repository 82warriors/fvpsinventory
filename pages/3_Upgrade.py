import streamlit as st
import pandas as pd
import requests
import re

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Auto-detecting latest worksheet")

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
# 🔍 GET ALL SHEETS
# ==================================================
@st.cache_data(ttl=300)
def get_sheets():

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:json"
    res = requests.get(url)

    text = res.text[47:-2]
    data = eval(text)

    # Extract sheet info manually
    sheets = []

    # fallback approach: scrape from HTML
    html_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    html = requests.get(html_url).text

    matches = re.findall(r'"sheetId":(\d+).*?"title":"(.*?)"', html)

    for gid, name in matches:
        sheets.append({
            "gid": gid,
            "name": name
        })

    return sheets

# ==================================================
# 🧠 PARSE DATE FROM SHEET NAME
# ==================================================
def extract_date(name):
    try:
        return pd.to_datetime(name, errors="coerce")
    except:
        return None

# ==================================================
# 🔥 GET LATEST SHEET
# ==================================================
@st.cache_data(ttl=300)
def get_latest_gid():

    sheets = get_sheets()

    df = pd.DataFrame(sheets)

    df["date"] = df["name"].apply(extract_date)

    df = df.dropna(subset=["date"])

    if df.empty:
        st.error("❌ No sheet names contain valid dates")
        st.write(df)
        st.stop()

    latest = df.sort_values("date", ascending=False).iloc[0]

    return latest["gid"], latest["name"]

# ==================================================
# LOAD SHEET
# ==================================================
def load_sheet(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"

    df = pd.read_csv(url, dtype=str)

    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", na=False)]

    return df

# ==================================================
# 🚀 LOAD LATEST DATA
# ==================================================
gid, sheet_name = get_latest_gid()

st.success(f"📄 Using latest sheet: {sheet_name}")

df = load_sheet(gid)

# ==================================================
# CLEAN DATA
# ==================================================
df.columns = df.columns.str.upper()

if "MODEL" not in df.columns or "IPU STATUS" not in df.columns:
    st.error("❌ Required columns not found")
    st.write(df.columns.tolist())
    st.stop()

df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()

# ==================================================
# FILTER TARGET MODELS
# ==================================================
df = df[df["MODEL"].isin(TARGET_MODELS)]
df = df.dropna(subset=["MODEL"])

# ==================================================
# SUMMARY
# ==================================================
summary = (
    df.groupby(["MODEL", "IPU STATUS"])
    .size()
    .unstack(fill_value=0)
)

for col in ["Completed", "Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()

# ==================================================
# %
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

completed = int(summary["Completed"].sum())
not_completed = int(summary["Not Completed"].sum())

total = completed + not_completed
rate = (completed / total * 100) if total > 0 else 0

c1, c2, c3 = st.columns(3)

c1.metric("✅ Completed", completed)
c2.metric("❌ Not Completed", not_completed)
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
# PROGRESS
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
