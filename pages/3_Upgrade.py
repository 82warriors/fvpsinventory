import streamlit as st
import pandas as pd
import altair as alt
import requests
import re
from datetime import datetime

st.set_page_config(page_title="Upgrade Tracking", layout="wide")

st.title("⬆️ Upgrade Status Dashboard")
st.caption("Auto-detect latest worksheet (NO API key)")

# ==============================
# CONFIG
# ==============================
SPREADSHEET_ID = "1x4EP6dO3FpkFRMBXqHDku0pl4vtHrWnE1S3J-e86vt0"

# ==============================
# DATE PARSER
# ==============================
def parse_sheet_date(title):
    title = title.strip()

    formats = [
        "%d %b %Y",
        "%d %B %Y",
        "%d-%b-%Y",
        "%d-%B-%Y"
    ]

    match = re.search(r"\d{1,2}[\s\-][A-Za-z]+[\s\-]\d{3,4}", title)
    if not match:
        return None

    text = match.group(0)

    parts = re.split(r"[\s\-]", text)
    if parts[-1].isdigit() and len(parts[-1]) == 3:
        parts[-1] = "2" + parts[-1]

    text = " ".join(parts)

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except:
            continue

    return None

# ==============================
# SCRAPE SHEET LIST (NO API)
# ==============================
@st.cache_data(ttl=300)
def get_sheets_no_api(spreadsheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"

    res = requests.get(url)

    if res.status_code != 200:
        return None, "Failed to access sheet (check sharing settings)"

    html = res.text

    # 🔥 Extract sheet titles + gid
    matches = re.findall(r'"sheetId":(\d+),"title":"(.*?)"', html)

    if not matches:
        return None, "No sheets found in HTML"

    sheets = [(title, gid) for gid, title in matches]

    return sheets, None

# ==============================
# FIND LATEST SHEET
# ==============================
def get_latest_sheet(sheets):
    valid = []

    for title, gid in sheets:
        dt = parse_sheet_date(title)
        if dt:
            valid.append((dt, title, gid))

    if valid:
        latest = sorted(valid, key=lambda x: x[0], reverse=True)[0]
        return latest[1], latest[2], None

    # fallback → last sheet
    last = sheets[-1]
    return last[0], last[1], "No dated sheet found, using last sheet"

# ==============================
# LOAD SHEET LIST
# ==============================
sheets, error = get_sheets_no_api(SPREADSHEET_ID)

if error:
    st.error(error)
    st.stop()

sheet_name, GID, warn = get_latest_sheet(sheets)

if warn:
    st.warning(warn)

st.info(f"📄 Data Source: {sheet_name}")

# ==============================
# LOAD DATA
# ==============================
csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

try:
    df = pd.read_csv(csv_url, dtype=str)
except Exception as e:
    st.error("❌ Failed to load data")
    st.write(str(e))
    st.stop()

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
    x=alt.X("MODEL:N"),
    y=alt.Y("Count:Q"),
    xOffset="Status:N"
)

bars = base.mark_bar().encode(color="Status:N")

text = base.mark_text(dy=-5).encode(text="Label")

st.altair_chart((bars + text).properties(height=400), use_container_width=True)

# ==============================
# PROGRESS
# ==============================
st.markdown("## 🔄 Progress by Model")

for _,row in summary.iterrows():
    st.write(f"**{row['MODEL']}** ({row['Completion %']}%)")
    st.progress(row["Completion %"]/100)
