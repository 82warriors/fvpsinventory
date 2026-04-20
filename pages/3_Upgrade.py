import streamlit as st
import pandas as pd
import altair as alt
import requests
import re
from datetime import datetime

st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Always pulls the latest worksheet automatically")

# ==============================
# CONFIG
# ==============================
SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"
API_KEY = "YOUR_GOOGLE_API_KEY"  # 🔴 replace this

# ==============================
# DATE PARSER (robust)
# ==============================
def parse_sheet_date(title):
    title = title.strip()

    match = re.match(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{3,4})", title)
    if not match:
        return None

    day, month, year = match.groups()

    # Fix 3-digit year (e.g. 206 → 2026)
    if len(year) == 3:
        year = "2" + year

    try:
        return datetime.strptime(f"{day} {month} {year}", "%d %b %Y")
    except:
        return None

# ==============================
# GET LATEST SHEET
# ==============================
def get_latest_sheet(spreadsheet_id, api_key):
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={api_key}"
    res = requests.get(meta_url).json()

    sheets = res.get("sheets", [])
    valid_sheets = []

    for s in sheets:
        title = s["properties"]["title"]
        gid = s["properties"]["sheetId"]

        parsed_date = parse_sheet_date(title)

        if parsed_date:
            valid_sheets.append((parsed_date, title, gid))

    if not valid_sheets:
        st.error("❌ No valid dated sheets found")
        st.stop()

    latest = sorted(valid_sheets, key=lambda x: x[0], reverse=True)[0]

    return latest[1], latest[2]

# ==============================
# LOAD DATA
# ==============================
sheet_name, GID = get_latest_sheet(SPREADSHEET_ID, API_KEY)

url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

st.info(f"📄 Data Source: {sheet_name}")

df = pd.read_csv(url, dtype=str)
df.columns = df.columns.astype(str).str.strip().str.upper()

# ==============================
# VALIDATION
# ==============================
REQUIRED_HEADERS = [
    "SCHOOL NAME","HOSTNAME","SERIAL NUMBER","ASSET TAG",
    "CUSTODIAN","LOCATION","BRAND","MODEL",
    "CATEGORY","IPU STATUS","EOL STATUS"
]

if not all(h in df.columns for h in REQUIRED_HEADERS):
    st.error("❌ Required headers missing")
    st.write(df.columns.tolist())
    st.stop()

# ==============================
# RAW DATA
# ==============================
st.markdown("## 🗂️ Full Updated Data")
st.dataframe(df, use_container_width=True)

# ==============================
# CLEAN DATA
# ==============================
df["MODEL"] = df["MODEL"].astype(str).str.upper().str.strip()
df["IPU STATUS"] = df["IPU STATUS"].astype(str).str.title().str.strip()

TARGET_MODELS = [
    "ACER VX2670G DESKTOP",
    "LENOVO K14 GEN2",
    "LENOVO L13 YOGA G4"
]

df = df[df["MODEL"].isin(TARGET_MODELS)]

# ==============================
# SUMMARY
# ==============================
summary = df.groupby(["MODEL","IPU STATUS"]).size().unstack(fill_value=0)

for col in ["Completed","Not Completed"]:
    if col not in summary.columns:
        summary[col] = 0

summary = summary.reset_index()
summary["Total"] = summary["Completed"] + summary["Not Completed"]
summary["Completion %"] = (summary["Completed"]/summary["Total"]).fillna(0)*100
summary["Completion %"] = summary["Completion %"].round(2)

# ==============================
# KPIs
# ==============================
st.markdown("## 📊 Overview")

completed = int(summary["Completed"].sum())
not_completed = int(summary["Not Completed"].sum())
total = completed + not_completed
rate = (completed/total*100) if total>0 else 0

c1,c2,c3 = st.columns(3)
c1.metric("✅ Completed",completed)
c2.metric("❌ Not Completed",not_completed)
c3.metric("📈 Completion Rate",f"{rate:.2f}%")

# ==============================
# TABLE
# ==============================
st.markdown("## 📋 Upgrade Summary")
st.dataframe(
    summary[["MODEL","Completed","Not Completed","Total","Completion %"]],
    use_container_width=True,
    hide_index=True
)

# ==============================
# CHART
# ==============================
st.markdown("## 📈 Upgrade Progress")

chart_df = summary.melt(
    id_vars=["MODEL","Total"],
    value_vars=["Completed","Not Completed"],
    var_name="Status",
    value_name="Count"
)

chart_df["Percent"] = (chart_df["Count"] / chart_df["Total"] * 100).round(1)
chart_df["Label"] = chart_df["Percent"].astype(str) + "%"

base = alt.Chart(chart_df).encode(
    x=alt.X("MODEL:N", title="Model"),
    y=alt.Y("Count:Q", title="Number of Devices"),
    xOffset="Status:N"
)

bars = base.mark_bar().encode(
    color=alt.Color("Status:N", title="")
)

text = base.mark_text(
    dy=-5,
    fontSize=12
).encode(
    text="Label"
)

chart = (bars + text).properties(height=400)

st.altair_chart(chart, use_container_width=True)

# ==============================
# PROGRESS BARS
# ==============================
st.markdown("## 🔄 Progress by Model")

for _,row in summary.iterrows():
    st.write(f"**{row['MODEL']}** ({row['Completion %']}%)")
    st.progress(row["Completion %"]/100)
