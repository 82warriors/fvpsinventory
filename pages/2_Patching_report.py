import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Auto-detect latest sheet based on date name")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

# ==================================================
# GET SHEETS (RELIABLE METHOD)
# ==================================================
@st.cache_data(ttl=300)
def get_sheets():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:json"
    res = requests.get(url)
    text = res.text

    # Extract JSON part safely
    json_text = text[text.find("{"):text.rfind("}")+1]
    data = json.loads(json_text)

    sheets = []

    # This gives columns, but we need metadata fallback
    # So we ALSO use CSV gid probing

    base_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

    # Common gids (fast scan)
    possible_gids = [0]

    # Add more from heuristic
    for i in range(1, 20):
        possible_gids.append(i * 100000000)

    for gid in possible_gids:
        try:
            test_url = f"{base_url}/export?format=csv&gid={gid}"
            df = pd.read_csv(test_url, nrows=1)

            sheets.append({
                "gid": gid,
                "name": f"SHEET_{gid}"  # placeholder
            })
        except:
            continue

    return sheets

# ==================================================
# MANUAL NAME FIX (IMPORTANT)
# ==================================================
# Since Google blocks names, we read from first row instead
def get_sheet_name_from_data(df):
    # You may adjust this if your sheet has title row
    return df.columns[0]

# ==================================================
# PARSE DATE
# ==================================================
def parse_date(name):
    formats = ["%d %B %Y", "%d %b %Y"]

    for fmt in formats:
        try:
            return datetime.strptime(name.strip(), fmt)
        except:
            continue

    return None

# ==================================================
# LOAD & DETECT
# ==================================================
@st.cache_data(ttl=300)
def detect_latest_sheet():
    base_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"

    results = []

    # Try common gid range
    for gid in range(0, 2000000000, 100000000):
        try:
            url = f"{base_url}/export?format=csv&gid={gid}"
            df = pd.read_csv(url, dtype=str)

            # Try infer name from content (fallback)
            name = str(df.columns[0]).strip()

            dt = parse_date(name)

            if dt:
                results.append({
                    "gid": gid,
                    "name": name,
                    "date": dt,
                    "df": df
                })

        except:
            continue

    if not results:
        return None, []

    results.sort(key=lambda x: x["date"], reverse=True)

    return results[0], results

# ==================================================
# MAIN
# ==================================================
latest, all_sheets = detect_latest_sheet()

if latest is None:
    st.error("❌ Still cannot detect sheets — fallback needed")
    st.stop()

# Dropdown
names = [s["name"] for s in all_sheets]

selected = st.selectbox("📂 Select Sheet", names)

selected_data = next(s for s in all_sheets if s["name"] == selected)

df = selected_data["df"]

st.success(f"📅 Showing: {selected}")

# ==================================================
# CLEAN
# ==================================================
df.columns = df.columns.str.strip().str.upper()
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# ==================================================
# SUMMARY
# ==================================================
def calculate_summary(df):
    keys = [
        "ADMIN INSTALLED","ACAD INSTALLED","ADMIN NOT CONNECTED",
        "ACAD NOT CONNECTED","ADMIN REQUIRED","ACAD REQUIRED",
        "ADMIN UNKNOWN","ACAD UNKNOWN","E-EXAM","FAULTY"
    ]

    summary = {k: 0 for k in keys}

    for col in df.columns:
        for key in keys:
            if key in col:
                summary[key] += pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

    return summary

summary = calculate_summary(df)

installed = summary["ADMIN INSTALLED"] + summary["ACAD INSTALLED"]
total = sum(summary.values())
percent = (installed / total * 100) if total else 0

# ==================================================
# DISPLAY
# ==================================================
col1, col2, col3 = st.columns(3)

col1.metric("Installed", int(installed))
col2.metric("Total", int(total))
col3.metric("Patching %", f"{percent:.2f}%")

st.divider()

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
