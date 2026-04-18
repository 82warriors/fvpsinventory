import streamlit as st
import pandas as pd
import time
import urllib.parse

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

st.title("🛠️ Patching Report")
st.caption("Auto-updating dashboard (refresh every 30s)")

# ==================================================
# AUTO REFRESH (every 30 sec)
# ==================================================
REFRESH_INTERVAL = 30

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================================================
# GET META (A1 header, A2 value)
# ==================================================
@st.cache_data(ttl=30)
def get_latest_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"

    df = pd.read_csv(url, header=None)

    if df.shape[0] < 2:
        raise Exception("META sheet missing data")

    sheet_name = str(df.iloc[1, 0]).strip()

    if not sheet_name or sheet_name.lower() == "none":
        raise Exception("LatestSheet is empty")

    return sheet_name

# ==================================================
# LOAD SHEET (FIXED VERSION)
# ==================================================
@st.cache_data(ttl=30)
def load_sheet(sheet_name):
    encoded_name = urllib.parse.quote(sheet_name)

    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}"

    try:
        df = pd.read_csv(url, dtype=str)
    except Exception as e:
        raise Exception(f"Failed to read sheet '{sheet_name}': {e}")

    if not isinstance(df, pd.DataFrame):
        raise Exception("Invalid data returned (not DataFrame)")

    if df.empty:
        raise Exception(f"Sheet '{sheet_name}' is empty or inaccessible")

    # ✅ SAFE CLEANING (no applymap)
    df.columns = df.columns.str.strip().str.upper()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df

# ==================================================
# SUMMARY CALCULATION
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
# MAIN LOAD
# ==================================================
try:
    sheet_name = get_latest_sheet()
    st.info(f"📡 Latest sheet detected: {sheet_name}")

    df = load_sheet(sheet_name)

except Exception as e:
    st.error("❌ Failed to load data")
    st.exception(e)
    st.stop()

# ==================================================
# METRICS
# ==================================================
summary = calculate_summary(df)

installed = summary["ADMIN INSTALLED"] + summary["ACAD INSTALLED"]
total = sum(summary.values())
percent = (installed / total * 100) if total else 0

col1, col2, col3 = st.columns(3)

col1.metric("Installed", int(installed))
col2.metric("Total Devices", int(total))
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
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")
