import streamlit as st
import pandas as pd
import time

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

st.title("🛠️ Patching Report")
st.caption("Auto-updating dashboard (stable version)")

# ==================================================
# AUTO REFRESH (every 60 sec)
# ==================================================
REFRESH_INTERVAL = 60

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================================================
# LOAD META (FIXED FORMAT: A1 header, A2 value)
# ==================================================
@st.cache_data(ttl=60)
def get_latest_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"

    df = pd.read_csv(url, header=None)

    # Expect:
    # Row 0 → header
    # Row 1 → value
    if df.shape[0] < 2:
        raise Exception("META sheet missing data (needs at least 2 rows)")

    sheet_name = str(df.iloc[1, 0]).strip()

    if not sheet_name or sheet_name.lower() == "none":
        raise Exception("LatestSheet is empty")

    return sheet_name

# ==================================================
# LOAD TARGET SHEET
# ==================================================
@st.cache_data(ttl=60)
def load_sheet(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    df = pd.read_csv(url, dtype=str)

    if df.empty:
        raise Exception(f"Sheet '{sheet_name}' is empty")

    # Clean data
    df.columns = df.columns.str.strip().str.upper()
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

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
st.caption("🔄 Auto refresh every 60 seconds")
