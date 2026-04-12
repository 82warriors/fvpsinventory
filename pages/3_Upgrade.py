import streamlit as st
import pandas as pd
import requests
import re

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Always pulls the latest worksheet for raw data, summary calculated separately")

# ==================================================
# CONFIG
# ==================================================
SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"

REQUIRED_HEADERS = [
    "SCHOOL NAME", "HOSTNAME", "SERIAL NUMBER", "ASSET TAG",
    "CUSTODIAN", "LOCATION", "BRAND", "MODEL",
    "CATEGORY", "IPU STATUS", "EOL STATUS"
]

TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

# ==================================================
# 🔍 GET SHEETS
# ==================================================
@st.cache_data(ttl=300)
def get_sheets():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
        html = requests.get(url).text
        matches = re.findall(r'"sheetId":(\d+).*?"title":"(.*?)"', html)
        sheets = [{"gid": gid, "name": name} for gid, name in matches]
        if not sheets:
            raise ValueError("No sheets found")
        return sheets
    except:
        return []

# ==================================================
# 🔥 GET LATEST TAB
# ==================================================
@st.cache_data(ttl=300)
def get_latest_sheet():
    sheets = get_sheets()
    if sheets:
        latest = sheets[-1]  # last tab = latest
        return latest["gid"], latest["name"]
    return "1946114847", "Default Sheet"

# ==================================================
# LOAD LATEST SHEET
# ==================================================
def load_latest_sheet():
    gid, sheet_name = get_latest_sheet()
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"

    raw = pd.read_csv(url, header=None, dtype=str)

    # detect header row
    header_row = None
    for i in range(len(raw)):
        row = raw.iloc[i].astype(str).str.upper()
        if "MODEL" in row.values and "IPU STATUS" in row.values:
            header_row = i
            break

    if header_row is None:
        st.error(f"❌ Cannot detect header row in {sheet_name}")
        st.write(raw.head(10))
        st.stop()

    df = pd.read_csv(url, header=header_row, dtype=str)
    df.columns = df.columns.astype(str).str.strip().str.upper()
    df = df.loc[:, ~df.columns.str.contains("^UNNAMED", na=False)]

    # validate required headers
    if not all(h in df.columns for h in REQUIRED_HEADERS):
        st.error(f"❌ Required headers missing in {sheet_name}")
        st.write(df.columns.tolist())
        st.stop()

    return df, sheet_name

# ==================================================
# 🚀 LOAD DATA
# ==================================================
df, sheet_name = load_latest_sheet()
st.info(f"📄 Using latest sheet: {sheet_name}")

# ==================================================
# RAW DATA (always latest)
# ==================================================
st.markdown("## 🗂️ Full Updated Data (Latest Worksheet)")
st.dataframe(df, use_container_width=True)

# ==================================================
# SUMMARY (calculated separately)
# ==================================================
df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()
df = df[df["MODEL"].isin(TARGET_MODELS)]
df = df.dropna(subset=["MODEL"])

summary = (
    df.groupby(["MODEL", "IPU STATUS"])
    .size()
    .unstack(fill_value=0)
)

for col in ["Completed", "Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()
summary["Total"] = summary["Completed"] + summary["Not Completed"]
summary["Completion %"] = (summary["Completed"] / summary["Total"]).fillna(0) * 100
summary["Completion %"] = summary["Completion %"].round(1)

# ==================================================
# KPI
# ==================================================
st.markdown("## 📊 Overview (Summary)")
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
# REFRESH
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
