import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

st.title("🛠️ Patching Report")
st.caption("Auto-detect latest sheet (date-based)")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

# ==================================================
# TRY LOAD SHEET BY NAME
# ==================================================
def try_load_sheet(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url, dtype=str)
        return df
    except:
        return None

# ==================================================
# FIND VALID SHEETS (LAST 60 DAYS)
# ==================================================
@st.cache_data(ttl=300)
def find_valid_sheets():
    today = datetime.today()
    valid = []

    for i in range(0, 90):  # check last 90 days
        d = today - timedelta(days=i)

        # Try full month format
        name = d.strftime("%-d %B %Y")  # Linux
        alt_name = d.strftime("%d %B %Y")  # fallback

        for sheet_name in [name, alt_name]:
            df = try_load_sheet(sheet_name)

            if df is not None:
                valid.append({
                    "name": sheet_name,
                    "date": d
                })
                break

    # remove duplicates
    unique = {v["name"]: v for v in valid}.values()

    sorted_list = sorted(unique, key=lambda x: x["date"], reverse=True)

    return sorted_list

# ==================================================
# LOAD SHEET
# ==================================================
def load_sheet(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
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
valid_sheets = find_valid_sheets()

if not valid_sheets:
    st.error("❌ No sheets found (check sharing permissions)")
    st.stop()

sheet_names = [s["name"] for s in valid_sheets]

selected = st.selectbox("📂 Select Sheet", sheet_names, index=0)

df = load_sheet(selected)

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
