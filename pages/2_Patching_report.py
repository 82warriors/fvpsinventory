import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Auto-detect latest sheet based on date name")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

# ==================================================
# GET SHEETS
# ==================================================
@st.cache_data(ttl=300)
def get_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    html = requests.get(url).text
    matches = re.findall(r'"sheetId":(\d+).*?"title":"(.*?)"', html)

    return [{"gid": gid, "name": name.strip()} for gid, name in matches]

# ==================================================
# PARSE DATE FLEXIBLY
# ==================================================
def parse_date(name):
    formats = [
        "%d %b %Y",   # 01 Jan 2026
        "%d %B %Y"    # 16 April 2026
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(name, fmt)
        except:
            continue
    
    return None

# ==================================================
# GET LATEST SHEET
# ==================================================
@st.cache_data(ttl=300)
def get_latest_dated_sheet():
    sheets = get_sheets()
    valid = []

    for s in sheets:
        parsed = parse_date(s["name"])
        if parsed:
            valid.append({
                "gid": s["gid"],
                "name": s["name"],
                "date": parsed
            })

    if not valid:
        return None, None, []

    valid.sort(key=lambda x: x["date"], reverse=True)

    return valid[0]["gid"], valid[0]["name"], valid

# ==================================================
# LOAD DATA
# ==================================================
def load_sheet(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url, dtype=str)

    # Clean headers
    df.columns = df.columns.str.strip().str.upper()

    # Clean values
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    return df

# ==================================================
# CALCULATE SUMMARY
# ==================================================
def calculate_summary(df):
    keys = [
        "ADMIN INSTALLED",
        "ACAD INSTALLED",
        "ADMIN NOT CONNECTED",
        "ACAD NOT CONNECTED",
        "ADMIN REQUIRED",
        "ACAD REQUIRED",
        "ADMIN UNKNOWN",
        "ACAD UNKNOWN",
        "E-EXAM",
        "FAULTY"
    ]

    summary = {k: 0 for k in keys}

    for col in df.columns:
        for key in keys:
            if key in col:
                summary[key] += pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

    return summary

# ==================================================
# LOAD LATEST
# ==================================================
latest_gid, latest_name, all_sheets = get_latest_dated_sheet()

if latest_gid is None:
    st.error("❌ No valid date-formatted sheets found")
    st.stop()

# Optional override
sheet_names = [s["name"] for s in all_sheets]

selected = st.selectbox(
    "📂 Select Sheet",
    sheet_names,
    index=0
)

selected_gid = next(s["gid"] for s in all_sheets if s["name"] == selected)

df = load_sheet(selected_gid)

st.success(f"📅 Showing: {selected}")

# ==================================================
# METRICS
# ==================================================
summary = calculate_summary(df)

installed = summary["ADMIN INSTALLED"] + summary["ACAD INSTALLED"]
total = sum(summary.values())
percent = (installed / total * 100) if total else 0

col1, col2, col3 = st.columns(3)

col1.metric("Installed", int(installed))
col2.metric("Total", int(total))
col3.metric("Patching %", f"{percent:.2f}%")

st.divider()

# ==================================================
# BREAKDOWN
# ==================================================
st.subheader("📊 Breakdown")
st.dataframe(pd.DataFrame([summary]), use_container_width=True)

# ==================================================
# RAW DATA
# ==================================================
st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)

# ==================================================
# DEBUG
# ==================================================
with st.expander("🔍 Detected Date Sheets"):
    for s in all_sheets:
        st.write(f"✅ {s['name']}")

# ==================================================
# REFRESH
# ==================================================
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
