import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Auto-detect latest date-based worksheet")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

# ==================================================
# GET SHEETS (OFFICIAL FEED - RELIABLE)
# ==================================================
@st.cache_data(ttl=300)
def get_sheets():
    url = f"https://spreadsheets.google.com/feeds/worksheets/{SPREADSHEET_ID}/public/full?alt=json"
    res = requests.get(url)
    data = res.json()

    sheets = []

    for entry in data["feed"]["entry"]:
        name = entry["title"]["$t"]
        gid = entry["id"]["$t"].split("/")[-1]

        sheets.append({
            "name": name.strip(),
            "gid": gid
        })

    return sheets

# ==================================================
# PARSE DATE
# ==================================================
def parse_date(name):
    formats = [
        "%d %B %Y",  # 16 April 2026
        "%d %b %Y"   # 01 Jan 2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(name.strip(), fmt)
        except:
            continue

    return None

# ==================================================
# GET LATEST SHEET
# ==================================================
@st.cache_data(ttl=300)
def get_valid_sheets():
    sheets = get_sheets()

    valid = []

    for s in sheets:
        dt = parse_date(s["name"])
        if dt:
            valid.append({
                "name": s["name"],
                "gid": s["gid"],
                "date": dt
            })

    valid.sort(key=lambda x: x["date"], reverse=True)

    return valid

# ==================================================
# LOAD DATA
# ==================================================
def load_sheet(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url, dtype=str)

    df.columns = df.columns.str.strip().str.upper()
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    return df

# ==================================================
# SUMMARY
# ==================================================
def calculate_summary(df):
    keys = [
        "ADMIN INSTALLED","ACAD INSTALLED",
        "ADMIN NOT CONNECTED","ACAD NOT CONNECTED",
        "ADMIN REQUIRED","ACAD REQUIRED",
        "ADMIN UNKNOWN","ACAD UNKNOWN",
        "E-EXAM","FAULTY"
    ]

    summary = {k: 0 for k in keys}

    for col in df.columns:
        for key in keys:
            if key in col:
                summary[key] += pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

    return summary

# ==================================================
# MAIN
# ==================================================
valid_sheets = get_valid_sheets()

if not valid_sheets:
    st.error("❌ No valid date-named sheets found")
    st.stop()

# Dropdown
sheet_names = [s["name"] for s in valid_sheets]

selected_name = st.selectbox("📂 Select Sheet", sheet_names, index=0)

selected_sheet = next(s for s in valid_sheets if s["name"] == selected_name)

df = load_sheet(selected_sheet["gid"])

st.success(f"📅 Showing: {selected_name}")

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
# TABLES
# ==================================================
st.subheader("📊 Breakdown")
st.dataframe(pd.DataFrame([summary]), use_container_width=True)

st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)

# ==================================================
# REFRESH
# ==================================================
if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
