import streamlit as st
import pandas as pd
import time
import urllib.parse

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Patching Report", layout="wide")

SPREADSHEET_ID = "1zvwKzIEbvQEEgbcqcyp9WP0IfguSaHm2G67ZAeuiSOE"

st.title("🛠️ Patching Report Dashboard")
st.caption("Device status monitoring (stacked view)")

# ==================================================
# AUTO REFRESH (30 sec)
# ==================================================
REFRESH_INTERVAL = 30

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================================================
# GET META
# ==================================================
@st.cache_data(ttl=30)
def get_latest_sheet():
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=META"
    df = pd.read_csv(url, header=None)

    if df.shape[0] < 2:
        raise Exception("META missing data")

    return str(df.iloc[1, 0]).strip()

# ==================================================
# LOAD SHEET
# ==================================================
@st.cache_data(ttl=30)
def load_sheet(sheet_name):
    encoded = urllib.parse.quote(sheet_name)
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded}"

    df = pd.read_csv(url, dtype=str)

    if df.empty:
        raise Exception("Sheet empty")

    df.columns = df.columns.str.strip().str.upper()

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    return df

# ==================================================
# DEVICE STATUS COUNT + TOTAL
# ==================================================
def device_status_count(df):
    devices = [
        "LENOVO K14 GEN2",
        "LENOVO L13 YOGA G4",
        "ACER VX2670G DESKTOP"
    ]

    statuses = [
        "INSTALLED",
        "SCCM EPP > 4 WKS",
        "NOT CONNECTED",
        "REQUIRED"
    ]

    result = []

    for device in devices:
        row = {"Device": device.title()}
        total = 0

        for status in statuses:
            count = df[
                (df.iloc[:, 6].str.upper() == device) &
                (df.iloc[:, 11].str.upper() == status)
            ].shape[0]

            row[status] = count
            total += count

        row["TOTAL"] = total
        result.append(row)

    return pd.DataFrame(result)

# ==================================================
# MAIN LOAD
# ==================================================
try:
    sheet_name = get_latest_sheet()
    df = load_sheet(sheet_name)

    st.success(f"📅 Latest: {sheet_name}")

except Exception as e:
    st.error("❌ Load error")
    st.exception(e)
    st.stop()

# ==================================================
# DEVICE TABLE
# ==================================================
device_df = device_status_count(df)

# Clean column order
device_df = device_df[
    ["Device", "INSTALLED", "SCCM EPP > 4 WKS", "NOT CONNECTED", "REQUIRED", "TOTAL"]
]

st.subheader("💻 Device Status Breakdown")
st.dataframe(device_df, use_container_width=True)

# ==================================================
# 📊 STACKED BAR CHART
# ==================================================
st.subheader("📊 Stacked Status Distribution")

chart_df = device_df.set_index("Device")[[
    "INSTALLED",
    "SCCM EPP > 4 WKS",
    "NOT CONNECTED",
    "REQUIRED"
]]

st.bar_chart(chart_df)  # 🔥 auto-stacked in Streamlit

# ==================================================
# OPTIONAL: % INSTALLED
# ==================================================
device_df["% INSTALLED"] = (
    device_df["INSTALLED"] / device_df["TOTAL"] * 100
).round(1)

st.subheader("📈 Installation Rate (%)")
st.dataframe(device_df[["Device", "% INSTALLED"]], use_container_width=True)

# ==================================================
# RAW DATA
# ==================================================
st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)

# ==================================================
# FOOTER
# ==================================================
st.caption("🔄 Auto refresh every 30 seconds")
