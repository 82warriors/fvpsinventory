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
st.caption("Automatically detects latest dated worksheet (e.g. 01 Jan 2026)")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

# ==================================================
# GET ALL SHEETS
# ==================================================
@st.cache_data(ttl=300)
def get_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    html = requests.get(url).text

    matches = re.findall(r'"sheetId":(\d+).*?"title":"(.*?)"', html)

    sheets = []
    for gid, name in matches:
        sheets.append({
            "gid": gid,
            "name": name.strip()
        })

    return sheets

# ==================================================
# GET LATEST DATED SHEET
# ==================================================
@st.cache_data(ttl=300)
def get_latest_dated_sheet():
    sheets = get_sheets()

    valid_sheets = []

    for s in sheets:
        try:
            parsed_date = datetime.strptime(s["name"], "%d %b %Y")
            valid_sheets.append({
                "gid": s["gid"],
                "name": s["name"],
                "date": parsed_date
            })
        except:
            continue  # ignore non-date sheets

    if not valid_sheets:
        return None, None, []

    valid_sheets = sorted(valid_sheets, key=lambda x: x["date"], reverse=True)

    return valid_sheets[0]["gid"], valid_sheets[0]["name"], valid_sheets

# ==================================================
# LOAD SHEET DATA
# ==================================================
def load_sheet(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={gid}"

    df = pd.read_csv(url, dtype=str)

    # Clean headers
    df.columns = df.columns.astype(str).str.strip().str.upper()

    # Clean values
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    return df

# ==================================================
# CALCULATE SUMMARY
# ==================================================
def calculate_summary(df):
    summary_keys = [
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

    summary = {key: 0 for key in summary_keys}

    for col in df.columns:
        col_upper = col.upper()

        for key in summary_keys:
            if key in col_upper:
                summary[key] += pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

    return summary

# ==================================================
# LOAD DATA
# ==================================================
latest_gid, latest_name, all_valid_sheets = get_latest_dated_sheet()

if latest_gid is None:
    st.error("❌ No valid dated worksheets found (format must be like '01 Jan 2026')")
    st.stop()

# Optional manual override
sheet_names = [s["name"] for s in all_valid_sheets]

selected_sheet = st.selectbox(
    "📂 Select Sheet (Optional Override)",
    sheet_names,
    index=0
)

selected_gid = next(s["gid"] for s in all_valid_sheets if s["name"] == selected_sheet)

df = load_sheet(selected_gid)

st.success(f"📅 Showing Sheet: {selected_sheet}")

# ==================================================
# CALCULATIONS
# ==================================================
summary = calculate_summary(df)

installed = summary["ADMIN INSTALLED"] + summary["ACAD INSTALLED"]
total = sum(summary.values())
percentage = (installed / total * 100) if total > 0 else 0

# ==================================================
# DISPLAY SUMMARY
# ==================================================
st.subheader("📊 Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Installed", int(installed))
col2.metric("Total Devices", int(total))
col3.metric("Patching %", f"{percentage:.2f}%")

st.divider()

# ==================================================
# BREAKDOWN
# ==================================================
st.subheader("📋 Breakdown")
st.dataframe(pd.DataFrame([summary]), use_container_width=True)

st.divider()

# ==================================================
# RAW DATA
# ==================================================
st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)

# ==================================================
# DEBUG VIEW
# ==================================================
with st.expander("🔍 Debug: Detected Date Sheets"):
    for s in all_valid_sheets:
        st.write(f"✅ {s['name']}")

# ==================================================
# REFRESH BUTTON
# ==================================================
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
